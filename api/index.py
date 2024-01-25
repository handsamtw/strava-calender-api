import sys
import os
import io
import time
from base64 import b64decode
from pymongo import MongoClient

from bson import ObjectId
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.responses import StreamingResponse
from cachetools import TTLCache
from fastapi import FastAPI, Depends, Request
import hashlib


cache = TTLCache(maxsize=256, ttl=60)

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
    get_last_activity_id,
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
    "http://127.0.0.1:4200",  
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
# Dependency to use caching in your route
def _get_cache():
    return cache
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
    
    # code = request.args.get("code")

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
    theme='All',
    as_image=False,
    hashed_url_cache_key: str = Depends(_get_hashed_url),
    cache: TTLCache = Depends(_get_cache)
):
    start = time.time()
    cached_result = cache.get(hashed_url_cache_key)
    
    if cached_result:
        print("Cache hit!")
        new_image_src, stat_summary = cached_result["image"], cached_result["stat"]
        
    else:
        print('Cache miss')
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

        
        cache_key = f"{sport_type.lower()}-imageSrc"
        last_activity_id, status_code = get_last_activity_id(access_token)
        if (
            status_code == 200
            and "last_activity_id" in user
            and user["last_activity_id"] == last_activity_id
            and cache_key in user
        ):
            print("No new activity found")
            new_image_src = user[cache_key]["image_src"]
            stat_summary = user[cache_key]["stat"]
        else:
            activities, status_code = await get_all_activities(access_token)

            if status_code == 200 and len(activities) > 0:
                daily_summary, stat_summary = summarize_activity(
                    activities, sport_type=sport_type.split(",") if sport_type else None
                )
                #bug: currently, if set is_parallel to True, 1 out of 7 images's color map bar will duplicate with image 
                new_image_src = plot_calendar(daily_summary, theme="All", is_parallel=False)

                users_collection.update_one(
                    {"_id": ObjectId(uid)},
                    {
                        "$set": {
                            "last_activity_id": last_activity_id,
                            cache_key: {"image_src":new_image_src,
                                        "stat": stat_summary
                                        }   
                        }
                    },
                )
            else:
                error_message = {"error": "No activity found in this account"}
                return JSONResponse(error_message), 404

    # Cache the result
    result = {"image":new_image_src, "stat":stat_summary}
    cache[hashed_url_cache_key] = result
    print("Run time:", round(time.time() - start, 3))
    if as_image and as_image.lower() == "true":
        # Decode the base64 string to bytes
        image_data = b64decode(new_image_src[theme])
        response = StreamingResponse(io.BytesIO(image_data), media_type="image/png")
        return response
    
    return result


@app.get("/check_valid_uid")
def check_valid_uid(uid: str):
    is_valid = False
    if ObjectId.is_valid(uid):
        user = users_collection.find_one({"_id": ObjectId(uid)})
        is_valid = user and "access_token" in user
        return {"is_valid": is_valid}
    
    return {"is_valid": is_valid}
