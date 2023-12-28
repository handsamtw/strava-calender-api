from pymongo import MongoClient
from gridfs import GridFS
from bson import ObjectId
from flask import Flask, send_file, request
from flask_cors import CORS

import io
import os
from dotenv import load_dotenv

# Load variables from .env into the environment

from utils import (
    get_all_activities,
    summarize_activity,
    plot_calander,
    request_token,
)


app = Flask(__name__)
CORS(app)
app.config["CORS_HEADERS"] = "Content-Type"

load_dotenv()
config = os.environ

# # Access individual variables
mongopass = config.get("MONGODB_PASSWORD")
# # # # Connect to MongoDB
uri = f"mongodb+srv://samliao:{mongopass}@cluster0.cfszocb.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(uri, username="samliao", password=mongopass)
db = client["strava-github-profile"]
users_collection = db["users"]
fs = GridFS(db)


# # NOTE: The return _id will be stored in localstorage at frontend side
@app.route("/token", methods=["GET"])
def get_access_token():
    code = request.args.get("code")

    if not code:
        return "No code is found in redirect url. Access_token request denied"
    credentials = request_token(code)

    if isinstance(credentials, dict):
        result = users_collection.insert_one(credentials)
        return str(result.inserted_id)
    else:
        return f"credentials is not an instance of dict.\n Credentials:{credentials}"


@app.route("/calander", methods=["GET"])
def get_activity_calander():
    data = request.get_json()
    sport_type = request.args.get("sport_type")
    theme = request.args.get("theme")
    plot_by = request.args.get("plot_by")

    if "token" not in data or "user_id" not in data:
        return "Token must be provided"
    user_id, access_token = data["user_id"], data["token"]
    if not ObjectId.is_valid(user_id):
        return f"Invalid user id: {user_id}"
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        return f"User id {user_id} wasn't found in database.Check Strava authorization status"

    activities = get_all_activities(access_token)
    print("Total activity: ", len(activities))
    if len(activities) > 0:
        daily_summary = summarize_activity(activities, sport_type=sport_type)
        # if "heatmap_image_id" in user:
        #     heatmap_image_id = user["heatmap_image_id"]
        #     image_data = fs.get(heatmap_image_id).read()
        #     return send_file(io.BytesIO(image_data), mimetype='image/png')

        image_data = plot_calander(
            daily_summary,
            theme=theme,
            plot_by=plot_by,
        )
        return send_file(io.BytesIO(image_data), mimetype="image/png")


#         # heatmap_image_id = fs.put(image_data, filename="my-heatmap.png")
#         # users_collection.update_one(
#         #     {"_id": ObjectId(uid)},
#         #     {
#         #         "$set": {
#         #             "heatmap_image_id": heatmap_image_id,
#         #         }
#         #     },
#         # )


# # @app.route("/{uid}", methods=["GET"], cors=cors_config)
# # def get_image(uid):
# #     if not ObjectId.is_valid(uid):
# #         return f"Invalid user id: {uid}"
# #     user = users_collection.find_one({"_id": ObjectId(uid)})
# #     if not user:
# #         return Response(
# #             f"User id {uid} wasn't found in database.Check Strava authorization status",
# #             status_code=404,
# #         )
# #     else:
# #         access_token, refresh_token, expires_at = (
# #             user["access_token"],
# #             user["refresh_token"],
# #             user["expires_at"],
# #         )
# #         if expire_in_n_minutes(expires_at, 30):
# #             response = refresh_access_token(refresh_token)
# #             if isinstance(response, dict):
# #                 users_collection.update_one(
# #                     {"_id": ObjectId(uid)},
# #                     {
# #                         "$set": {
# #                             "access_token": response["access_token"],
# #                             "refresh_token": response["refresh_token"],
# #                             "expires_at": response["expires_at"],
# #                         }
# #                     },
# #                 )
# #                 # It is very important to replace old token with new one !!!
# #                 access_token = response["access_token"]
# #             else:
# #                 return "Failed to refresh access_token"

# #         # If the user exists and latest avtivity id matches activity id, return image directly
# #         recent_activity_id = get_most_recent_activity_id(access_token)
# #         if (
# #             "recent_activity_id" in user
# #             and user["recent_activity_id"] == recent_activity_id
# #         ):
# #             image_id = user["image_id"]
# #             image_data = fs.get(image_id).read()
# #             return Response(image_data, headers={"Content-Type": "image/png"})

# #         else:
# #             image_data = html_to_activity_image(recent_activity_id)
# #             image_file_name = f"image-{uid}.png"
# #             print(image_file_name)
# #             image_id = fs.put(image_data, filename=image_file_name)
# #             if "image_id" in user:
# #                 old_image_id = user["image_id"]
# #                 fs.delete(ObjectId(old_image_id))
# #             users_collection.update_one(
# #                 {"_id": ObjectId(uid)},
# #                 {
# #                     "$set": {
# #                         "image_id": ObjectId(image_id),
# #                         "recent_activity_id": recent_activity_id,
# #                     }
# #                 },
# #             )

# #             return Response(image_data, headers={"Content-Type": "image/png"})


if __name__ == "__main__":
    app.run(debug=True)
