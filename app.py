from pymongo import MongoClient
from gridfs import GridFS
from bson import ObjectId


from chalicelib.util import (
    expire_in_n_minutes,
    refresh_access_token,
    plot,
    get_most_recent_activity_id,
    parse_activity,
)
from chalice import Chalice, Response
import os

app = Chalice(app_name="strava-github-profile")


# # Connect to MongoDB
mongopass = os.getenv("MONGOPASS")
uri = f"mongodb+srv://samliao:{mongopass}@cluster0.cfszocb.mongodb.net/?retryWrites=true&w=majority"

client = MongoClient(uri, username="samliao", password=mongopass)
db = client["strava-github-profile"]
users_collection = db["users"]
fs = GridFS(db)


@app.route("/", methods=["GET"])
def hello_world():
    return {"message": f"Hello world"}


# @app.route("/{username}", methods=["GET"])
# def get_name(username):
#     return {"message": f"Hello {username}"}


@app.route("/{username}", methods=["GET"])
def get_image(username):
    # return {"message": f"Hello {username}"}

    #     params = app.current_request.query_params

    # if not params or not params.get("username"):
    #     return Response("username must be provided in the your markdown")
    # username = params.get("username")
    user = users_collection.find_one({"username": username})

    if not user:
        return Response(
            f"No user {username} found in our service, wheck typo or authorization status"
        )
    else:
        access_token, refresh_token, expires_at = (
            user["access_token"],
            user["refresh_token"],
            user["expires_at"],
        )
        # return {"access_token": access_token}

        if expire_in_n_minutes(expires_at, 30):
            resp = refresh_access_token(refresh_token)
            users_collection.update_one(
                {"username": username},
                {
                    "$set": {
                        "access_token": resp["access_token"],
                        "refresh_token": resp["refresh_token"],
                        "expires_at": resp["expires_at"],
                    }
                },
            )
            # It is very important to replace old token with new one !!!
            access_token = resp["access_token"]

        recent_activity_id = get_most_recent_activity_id(access_token)
        image_id = user["image_id"]
        # If the user exists and latest avtivity id matches activity id, return image directly
        if user["recent_activity_id"] == recent_activity_id:
            image_data = fs.get(image_id).read()
            return Response(image_data, headers={"Content-Type": "image/png"})

        else:
            activity_detail = parse_activity(recent_activity_id, access_token)
            if activity_detail["polyline"]:
                image_data = plot(polyline=activity_detail["polyline"], cropped=False)
                image_id = fs.put(image_data, filename="image.png")

            old_image_id = user["image_id"]
            fs.delete(ObjectId(old_image_id))
            users_collection.update_one(
                {"username": username, "access_token": access_token},
                {
                    "$set": {
                        "image_id": ObjectId(image_id),
                        "recent_activity_id": recent_activity_id,
                    }
                },
            )

        return Response(image_data, headers={"Content-Type": "image/png"})
