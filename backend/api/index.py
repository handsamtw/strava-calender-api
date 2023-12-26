from pymongo import MongoClient
from gridfs import GridFS
from bson import ObjectId
from flask import Flask

# from api._utils.common import get_all_activities, summarize_activity
from utils import get_all_activities, summarize_activity

# from chalicelib.util import (
#     expire_in_n_minutes,
#     refresh_access_token,
#     get_most_recent_activity_id,
#     request_token,
#     html_to_activity_image,
#     get_all_activities,
#     summarize_activity,
#     plot_heatmap,
# )
import os
from dotenv import dotenv_values
import calmap

# Load variables from .env file
config = dotenv_values(".env")
# Access individual variables
mongopass = config.get("MONGODB_PASSWORD")
# # # Connect to MongoDB
# mongopass = os.getenv("MONGOPASS")
uri = f"mongodb+srv://samliao:{mongopass}@cluster0.cfszocb.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(uri, username="samliao", password=mongopass)
db = client["strava-github-profile"]
users_collection = db["users"]
pins_collection = db["pins"]
fs = GridFS(db)

# Define CORS configuration
# cors_config = CORSConfig(
#     allow_origin=FRONTEND_DEV_URL,
#     allow_headers=["Authorization", "Content-Type"],
#     max_age=600,  # Max cache time for preflight requests (in seconds)
# )
app = Flask(__name__)


# # NOTE: The return _id will be stored in localstorage at frontend side
# @app.route("/token", methods=["GET"], cors=cors_config)
# def get_access_token():
#     params = app.current_request.query_params
#     code = params["code"]
#     if not code:
#         print("No code is found in redirect url. Access_token request denied")
#         return "No code is found in redirect url"
#     credentials = request_token(code)

#     if isinstance(credentials, dict):
#         result = users_collection.insert_one(credentials)
#         return str(result.inserted_id)
#     else:
#         print(f"credentials is not an instance of dict.\n Credentials:{credentials}")
#         return "Bad request"


@app.route("/", methods=["GET"])
def get_activity_heatmap():
    token = config.get("ACCESS_TOKEN")
    activities = get_all_activities(token)
    print("Total activity: ", len(activities))
    if len(activities) > 0:
        daily_summary = summarize_activity(activities)
        print(daily_summary)
        return activities[:5]
    else:
        print("activities is empty")
    return "activities is empty"
    # print(daily_summary)


# @app.route("/{uid}/heatmap", methods=["GET"])
# def get_activity_heatmap(uid):
#     user = users_collection.find_one({"_id": ObjectId(uid)})
#     if "heatmap_image_id" in user:
#         heatmap_image_id = user["heatmap_image_id"]
#         image_data = fs.get(heatmap_image_id).read()
#         return Response(image_data, headers={"Content-Type": "image/png"})

#     token = STRAVA_ACCESS_TOKEN
#     activities = get_all_activities(token)
#     print("Total activity: ", len(activities))
#     if len(activities) > 0:
#         daily_summary = summarize_activity(activities)
#         print(daily_summary.head())
#         image_data = plot_heatmap(daily_summary)
#         heatmap_image_id = fs.put(image_data, filename="my-heatmap.png")
#         users_collection.update_one(
#             {"_id": ObjectId(uid)},
#             {
#                 "$set": {
#                     "heatmap_image_id": heatmap_image_id,
#                 }
#             },
#         )

#         return Response(image_data, headers={"Content-Type": "image/png"})

#         # print(daily_summary)
#     else:
#         print("activities is empty")


# @app.route("/{uid}", methods=["GET"], cors=cors_config)
# def get_image(uid):
#     if not ObjectId.is_valid(uid):
#         return f"Invalid user id: {uid}"
#     user = users_collection.find_one({"_id": ObjectId(uid)})
#     if not user:
#         return Response(
#             f"User id {uid} wasn't found in database.Check Strava authorization status",
#             status_code=404,
#         )
#     else:
#         access_token, refresh_token, expires_at = (
#             user["access_token"],
#             user["refresh_token"],
#             user["expires_at"],
#         )
#         if expire_in_n_minutes(expires_at, 30):
#             response = refresh_access_token(refresh_token)
#             if isinstance(response, dict):
#                 users_collection.update_one(
#                     {"_id": ObjectId(uid)},
#                     {
#                         "$set": {
#                             "access_token": response["access_token"],
#                             "refresh_token": response["refresh_token"],
#                             "expires_at": response["expires_at"],
#                         }
#                     },
#                 )
#                 # It is very important to replace old token with new one !!!
#                 access_token = response["access_token"]
#             else:
#                 return "Failed to refresh access_token"

#         # If the user exists and latest avtivity id matches activity id, return image directly
#         recent_activity_id = get_most_recent_activity_id(access_token)
#         if (
#             "recent_activity_id" in user
#             and user["recent_activity_id"] == recent_activity_id
#         ):
#             image_id = user["image_id"]
#             image_data = fs.get(image_id).read()
#             return Response(image_data, headers={"Content-Type": "image/png"})

#         else:
#             image_data = html_to_activity_image(recent_activity_id)
#             image_file_name = f"image-{uid}.png"
#             print(image_file_name)
#             image_id = fs.put(image_data, filename=image_file_name)
#             if "image_id" in user:
#                 old_image_id = user["image_id"]
#                 fs.delete(ObjectId(old_image_id))
#             users_collection.update_one(
#                 {"_id": ObjectId(uid)},
#                 {
#                     "$set": {
#                         "image_id": ObjectId(image_id),
#                         "recent_activity_id": recent_activity_id,
#                     }
#                 },
#             )

#             return Response(image_data, headers={"Content-Type": "image/png"})


# # @app.route(
# #     "/pin",
# #     methods=["POST"],
# # )
# # def pin_activities():
# #     body = app.current_request.json_body
# #     if "uid" in body:
# #         uid = body["uid"]
# #         print(uid)
# #     if "activity_ids" in body and isinstance(body["activity_ids"], list):
# #         activity_ids = body["activity_ids"]
# #         for activity_id in activity_ids:
# #             pass

# #     return body


# # @app.route("/pin", methods=["GET"])
# # def get_pin_activities():
# #     params = app.current_request.query_params
# #     uid = params["uid"]
# #     return uid


if __name__ == "__main__":
    app.run(debug=True)
