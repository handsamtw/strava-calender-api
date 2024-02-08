import sys
import os
import io
import time
from base64 import b64decode
from pymongo import MongoClient

from bson import ObjectId
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.responses import StreamingResponse
from cachetools import TTLCache


activity_cache = TTLCache(maxsize=256, ttl=600)
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


def _get_activity_cache():
    return activity_cache


@app.get("/")
async def root():
    print("here")
    cache_headers = {"Cache-Control": "public, max-age=600"}
    result = {"Welcome to Strava-calendar-api": "Thank you for the contribution!"}
    return JSONResponse(content=result, headers=cache_headers)


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
    activity_cache: TTLCache = Depends(_get_activity_cache),
):
    start = time.time()
    cached_result = None
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
        )

    # Decode the base64 string to bytes
    image_data = b64decode(plot_result)
    cache_headers = {"Cache-Control": "public, max-age=300"}
    response = StreamingResponse(
        io.BytesIO(image_data), media_type="image/png", headers=cache_headers
    )
    print(f"Run time: {(time.time() - start):,.2f}")
    return response


@app.get("/check_valid_uid")
def check_valid_uid(
    uid: str,
):
    is_valid = False

    if ObjectId.is_valid(uid):
        user = users_collection.find_one({"_id": ObjectId(uid)})
        is_valid = user is not None and "access_token" in user
    cache_headers = {"Cache-Control": "public, max-age=600"}
    return JSONResponse(content={"is_valid": is_valid}, headers=cache_headers)
