import sys
import os
import io
import time
from base64 import b64decode
from pymongo import MongoClient

from bson import ObjectId
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.responses import StreamingResponse
from cachetools import TTLCache
from fastapi import FastAPI, Depends, Request
import hashlib


response_cache = TTLCache(maxsize=256, ttl=300)
activity_cache = TTLCache(maxsize=256, ttl=600)
uid_cache = TTLCache(maxsize=256, ttl=300)
from dotenv import load_dotenv

# Add project_root to the sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Load variables from .env into the environment
from utils.utils import (
    get_all_activities,
    summarize_activity,
    plot_calendar,
    request_token,
    refresh_access_token_if_expired,
    get_user_name,
)


load_dotenv()
env = os.environ


mongopass = env.get("MONGODB_PASSWORD")

# Connect to MongoDB
uri = f"mongodb+srv://samliao:{mongopass}@cluster0.7zimm5o.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(uri, username="samliao", password=mongopass)
db = client["strava-calendar"]
users_collection = db["users"]

app = FastAPI()
# Define CORS settings
origins = [
    "http://localhost:4200",
    "https://strava-calender.vercel.app",
]

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all HTTP headers
)


def _get_response_cache():
    return response_cache


def _get_activity_cache():
    return activity_cache


def _get_uid_cache():
    return uid_cache


def _get_hashed_url(request: Request):
    # Use a hash function to generate the hash from the URL
    url = request.url._url
    hashed_url = hashlib.sha256(url.encode()).hexdigest()
    return hashed_url


@app.get("/")
async def root():
    result = {"Welcome to Strava-calendar-api": "Thank you for the contribution!"}
    return result


@app.get("/uid")
def generate_user_id(code: str):
    if not code:
        error_message = {"error": "No code is found in redirect url"}
        return JSONResponse(content=error_message), 400

    credentials, status_code = request_token(code)
    if status_code == 200:
        result = users_collection.insert_one(credentials)
        return {"uid": str(result.inserted_id)}

    error_message = {"error": credentials}
    return JSONResponse(content=error_message), 400


@app.get("/calendar")
async def get_activity_calendar(
    uid,
    sport_type,
    unit="metric",
    theme="All",
    as_image=False,
    hashed_url_cache_key: str = Depends(_get_hashed_url),
    response_cache: TTLCache = Depends(_get_response_cache),
    activity_cache: TTLCache = Depends(_get_activity_cache),
):
    start = time.time()

    if hashed_url_cache_key in response_cache:
        print("Cache hit!")
        cached_result = response_cache.get(hashed_url_cache_key)
        new_image_src = cached_result["image"]

    else:
        print("Cache miss")
        if not uid:
            error_message = {"error": f"uid is required in query parameter"}
            return JSONResponse(error_message), 404

        if not ObjectId.is_valid(uid):
            error_message = {"error": "Invalid user id"}
            return JSONResponse(error_message), 400

        user = users_collection.find_one({"_id": ObjectId(uid)})
        if not user:
            error_message = {"error": "User was not found in database"}
            return JSONResponse(error_message), 404

        access_token = user["access_token"]
        refresh_token_response, status_code = refresh_access_token_if_expired(user)
        if status_code != 200:
            return refresh_token_response, status_code
        if refresh_token_response:
            users_collection.update_one(
                {"_id": ObjectId(uid)},
                {
                    "$set": {
                        "access_token": refresh_token_response["access_token"],
                        "refresh_token": refresh_token_response["refresh_token"],
                        "expires_at": refresh_token_response["expires_at"],
                    }
                },
            )
            access_token = refresh_token_response["access_token"]

        activities, status_code = await get_all_activities(activity_cache, access_token)

        if status_code == 200 and len(activities) > 0:
            daily_summary, stat_summary = summarize_activity(
                activities, sport_type=sport_type
            )
            if daily_summary.empty:
                raise HTTPException(
                    status_code=404,
                    detail=f"No  {sport_type} activity found in your Strava",
                )

            username = user.get("username", None)

            if username is None:
                username = get_user_name(access_token)
                users_collection.update_one(
                    {"_id": ObjectId(uid)},
                    {"$set": {"username": username}},
                )

            # bug: currently, if set is_parallel to True, 1 out of 7 images's color map bar will duplicate with image
            new_image_src = plot_calendar(
                daily_summary,
                stat_summary=stat_summary,
                unit=unit,
                username=username,
                sport_type=sport_type,
                theme=theme,
                is_parallel=False,
            )

        else:
            error_message = {"error": "No activity found in this account"}
            raise HTTPException(
                status_code=404, detail="No activity found in this Strava account"
            )

    # Cache the result
    result = {"image": new_image_src}

    response_cache[hashed_url_cache_key] = result

    print(f"Run time: {(time.time() - start):,.2f}")
    if as_image and as_image.lower() == "true":
        # Decode the base64 string to bytes
        image_data = b64decode(new_image_src[theme])
        response = StreamingResponse(io.BytesIO(image_data), media_type="image/png")
        return response

    return result


@app.get("/check_valid_uid")
def check_valid_uid(
    uid: str,
    uid_cache: TTLCache = Depends(_get_uid_cache),
):
    is_valid = False
    if uid in uid_cache:
        return {"is_valid": uid_cache[uid]}

    if ObjectId.is_valid(uid):
        user = users_collection.find_one({"_id": ObjectId(uid)})
        is_valid = user is not None and "access_token" in user
        uid_cache[uid] = is_valid
        return {"is_valid": is_valid}

    return {"is_valid": is_valid}
