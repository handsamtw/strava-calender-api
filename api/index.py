import sys
import os
import io
import time
from base64 import b64decode
from pymongo import MongoClient

from bson import ObjectId
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.responses import StreamingResponse
from cachetools import TTLCache
from fastapi import FastAPI, Depends, Request
from hashlib import sha256
from functools import partial
from typing import Optional


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


# def _get_hashed_url(request: Request):
#     # Use a hash function to generate the hash from the URL
#     url = request.url._url
#     hashed_url = hashlib.sha256(url.encode()).hexdigest()
#     return hashed_url
def _get_hashed_url(
    uid: str,
    sport_type: str,
    unit: Optional[str] = "metric",
) -> str:
    data_to_hash = f"{uid}-{sport_type}-{unit}"
    return sha256(data_to_hash.encode("utf-8")).hexdigest()


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
    background_tasks: BackgroundTasks,
    unit="metric",
    theme="All",
    hashed_url_cache_key: str = Depends(_get_hashed_url),
    response_cache: TTLCache = Depends(_get_response_cache),
    activity_cache: TTLCache = Depends(_get_activity_cache),
):
    start = time.time()
    cached_result = response_cache.get(hashed_url_cache_key, {}).get(theme)

    if cached_result is not None:
        print("Cache hit!")
        plot_result = cached_result

    else:
        print("Cache miss")
        if not uid:
            raise HTTPException(
                status_code=404,
                detail="uid is required in query parameter",
            )

        if not ObjectId.is_valid(uid):
            raise HTTPException(
                status_code=400,
                detail="Invalid user id",
            )

        user = users_collection.find_one({"_id": ObjectId(uid)})
        if not user:
            raise HTTPException(
                status_code=404,
                detail="User was not found in database",
            )

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

        activities = await get_all_activities(activity_cache, access_token)
        if len(activities) <= 0:
            raise HTTPException(
                status_code=404,
                detail="No activity found in this Strava account",
            )

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

        plot_result = plot_calendar(
            daily_summary=daily_summary,
            stat_summary=stat_summary,
            username=username,
            sport_type=sport_type,
            cmap=theme,
            unit=unit,
            cache_key=hashed_url_cache_key,
            cache=response_cache,
        )
        c_map = ["Reds", "YlGn", "Greens", "Blues", "PuBu", "RdPu", "twilight"]
        filtered_c_map = [c for c in c_map if c != theme]
        for cmap in filtered_c_map:
            background_tasks.add_task(
                plot_calendar,
                daily_summary,
                stat_summary,
                username,
                sport_type,
                cmap,
                unit,
                hashed_url_cache_key,
                response_cache,
            )

    # Decode the base64 string to bytes
    image_data = b64decode(plot_result)
    response = StreamingResponse(io.BytesIO(image_data), media_type="image/png")
    print(f"Run time: {(time.time() - start):,.2f}")
    return response


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
