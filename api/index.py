import sys
import os
import time
from base64 import b64decode
from pymongo import MongoClient

from bson import ObjectId
from quart import Quart, request, jsonify, Response

# from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from quart_cors import cors

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
    # plot_calendar_parallel,
)


app = Quart(__name__)
app = cors(app)
# CORS(app)

load_dotenv()
env = os.environ


mongopass = env.get("MONGODB_PASSWORD")

# Connect to MongoDB
uri = f"mongodb+srv://samliao:{mongopass}@cluster0.7zimm5o.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(uri, username="samliao", password=mongopass)
db = client["strava-calendar"]
users_collection = db["users"]


# # NOTE: The return _id will be stored in localstorage at frontend side
@app.route("/uid", methods=["GET"])
def generate_user_id():
    code = request.args.get("code")

    if not code:
        error_message = {"error": "No code is found in redirect url"}
        return jsonify(error_message), 400

    credentials, status_code = request_token(code)
    if status_code == 200:
        result = users_collection.insert_one(credentials)
        return {"uid": str(result.inserted_id)}

    error_message = {"error": credentials}
    return jsonify(error_message), 400


# Ref: stackoverflow flask-cache-memoize-url-query-string-parameters-as-well
@app.route("/calendar", methods=["GET"])
async def get_activity_calendar():
    start = time.time()
    uid = request.args.get("uid")
    print(uid)
    if not uid:
        error_message = {"error": "User id not found"}
        return jsonify(error_message), 404

    if not ObjectId.is_valid(uid):
        error_message = {"error": "Invalid user id"}
        return jsonify(error_message), 400

    user = users_collection.find_one({"_id": ObjectId(uid)})
    if not user:
        error_message = {"error": "User was not found in database"}
        return jsonify(error_message), 404
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

    sport_type, theme, as_image = (
        request.args.get("sport_type"),
        request.args.get("theme"),
        request.args.get("as_image"),
    )
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
    else:
        activities, status_code = await get_all_activities(access_token)

        if status_code == 200 and len(activities) > 0:
            daily_summary = summarize_activity(
                activities, sport_type=sport_type.split(",") if sport_type else None
            )

            new_image_src = plot_calendar(daily_summary, theme="All")

            users_collection.update_one(
                {"_id": ObjectId(uid)},
                {
                    "$set": {
                        cache_key: new_image_src,
                        "last_activity_id": last_activity_id,
                    }
                },
            )
        else:
            error_message = {"error": "No activity found in this account"}
            return jsonify(error_message), 404

    print("Run time:", time.time() - start)
    if as_image and as_image.lower() == "true":
        # Decode the base64 string to bytes
        image_data = b64decode(new_image_src[theme])

        # Set the appropriate content type for the response
        response = Response(image_data, mimetype="image/png")

        return response

    return new_image_src


if __name__ == "__main__":
    app.run(debug=True)
