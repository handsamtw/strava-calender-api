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
@app.get("/")
async def root():
    return {"message": "Hello world!"}


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
async def get_activity_calendar(uid, sport_type, theme='All', as_image=False):
    start = time.time()
    print("uid: ", uid)
    if not uid:
        error_message = {"error": "User id not found"}
        return JSONResponse(error_message), 404

    if not ObjectId.is_valid(uid):
        error_message = {"error": "Invalid user id"}
        return JSONResponse(error_message), 400

    user = users_collection.find_one({"_id": ObjectId(uid)})
    if not user:
        error_message = {"error": "User was not found in database"}
        return JSONResponse(error_message), 404
        # return f"User wasn't found in database.Check Strava authorization status"
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
        print("Return cache")
        new_image_src = user[cache_key]
        stat_summary = user["stat_summary"]
    else:
        activities, status_code = await get_all_activities(access_token)

        if status_code == 200 and len(activities) > 0:
            daily_summary, stat_summary = summarize_activity(
                activities, sport_type=sport_type.split(",") if sport_type else None
            )
            print(stat_summary)
            new_image_src = plot_calendar(daily_summary, theme="All")

            users_collection.update_one(
                {"_id": ObjectId(uid)},
                {
                    "$set": {
                        cache_key: new_image_src,
                        "last_activity_id": last_activity_id,
                        "stat_summary": stat_summary
                    }
                },
            )
        else:
            error_message = {"error": "No activity found in this account"}
            return JSONResponse(error_message), 404

    print("Run time:", time.time() - start)
    if as_image and as_image.lower() == "true":
        # Decode the base64 string to bytes
        image_data = b64decode(new_image_src[theme])

        # Set the appropriate content type for the response
        # response = JSONResponse(image_data, mimetype="image/png")
        response = StreamingResponse(io.BytesIO(image_data), media_type="image/png")
        return response

    return {"image":new_image_src, "stat":stat_summary}


# handler = Mangum(app)  # optionally set debug=True
