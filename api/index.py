import sys
import os
from pymongo import MongoClient

from bson import ObjectId
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from flask_caching import Cache

from datetime import datetime, timedelta


from base64 import b64decode
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
)


config = {
    "DEBUG": True,  # some Flask specific configs
    "CACHE_TYPE": "SimpleCache",  # Flask-Caching related configs
    "CACHE_DEFAULT_TIMEOUT": 300,
    "CORS_HEADERS": "Content-Type",
}
app = Flask(__name__)
# tell Flask to use the above defined config
app.config.from_mapping(config)

CORS(app)

load_dotenv()
env = os.environ
cache = Cache(app)

# # Access individual variables
mongopass = env.get("MONGODB_PASSWORD")

# # # # Connect to MongoDB
uri = f"mongodb+srv://samliao:{mongopass}@cluster0.7zimm5o.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(uri, username="samliao", password=mongopass)
db = client["strava-calendar"]
users_collection = db["users"]


@app.route("/", methods=["GET"])
def hello_world():
    return "Hello, World!"


@app.route("/users/count", methods=["GET"])
def count_users():
    count = users_collection.count_documents({})
    return {"users-count": count}


# # NOTE: The return _id will be stored in localstorage at frontend side
@app.route("/uid", methods=["GET"])
def generate_user_id():
    code = request.args.get("code")

    if not code:
        return "No code is found in redirect url. Access_token request denied"
    credentials = request_token(code)

    if isinstance(credentials, dict):
        result = users_collection.insert_one(credentials)
        return {"uid": str(result.inserted_id)}
    else:
        return f"credentials is not an instance of dict.\n Credentials:{credentials}"


# Ref: https://stackoverflow.com/questions/9413566/flask-cache-memoize-url-query-string-parameters-as-well/47181782#47181782
@app.route("/calendar", methods=["GET"])
@cache.cached(timeout=30, query_string=True)
def get_activity_calendar():
    uid = request.args.get("uid")
    if not uid:
        return "User id must be provided"
    if not ObjectId.is_valid(uid):
        return f"Invalid user id: {uid}"
    user = users_collection.find_one({"_id": ObjectId(uid)})
    if not user:
        return f"User wasn't found in database.Check Strava authorization status"
    access_token = user["access_token"]
    refresh_token_response = refresh_access_token_if_expired(user)
    if refresh_token_response and "access_token" in refresh_token_response:
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

    sport_type, theme, as_image = (
        request.args.get("sport_type"),
        request.args.get("theme"),
        request.args.get("as_image"),
    )

    activities = get_all_activities(access_token)
    if len(activities) > 0:
        daily_summary = summarize_activity(
            activities, sport_type=sport_type.split(",") if sport_type else None
        )
        if daily_summary.empty:
            return "No activities found within the period"

        existing_data = users_collection.find_one({"_id": ObjectId(uid)})
        current_image_src = existing_data.get(f"{sport_type}-imageSrc", {})
        new_image_src = plot_calendar(
            daily_summary,
            theme=theme,
        )

        merged_image_dict = {**current_image_src, **new_image_src}

        users_collection.update_one(
            {"_id": ObjectId(uid)},
            {"$set": {f"{sport_type}-imageSrc": merged_image_dict}},
        )

        if as_image and as_image.lower() == "true":
            # Decode the base64 string to bytes
            image_data = b64decode(new_image_src[theme])

            # Set the appropriate content type for the response
            response = Response(image_data, mimetype="image/png")

            return response

        return new_image_src


if __name__ == "__main__":
    app.run(debug=True)
