import io
from Activity import Activity
from RoutePlot import RoutePlot
from ScreenShotter import ScreenShotter
from pymongo import MongoClient
from gridfs import GridFS
from bson import ObjectId
import io
from util import expire_in_n_minutes, refresh_access_token
from chalice import Chalice, Response

# Here are a few more examples:
#
# @app.route('/hello/{name}')
# def hello_name(name):
#    # '/hello/james' -> {"hello": "james"}
#    return {'hello': name}
#
# @app.route('/users', methods=['POST'])
# def create_user():
#     # This is the JSON body the user sent in their POST request.
#     user_as_json = app.current_request.json_body
#     # We'll echo the json body back to the user in a 'user' key.
#     return {'user': user_as_json}
#
app = Chalice(app_name="strava-github-profile")


@app.route("/")
def index():
    return {"hello": "world"}


# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["strava_github_profile"]
users_collection = db["users"]
fs = GridFS(db)


@app.route("/get_image")
def get_image():
    params = app.current_request.query_params

    if not params or not params.get("username"):
        return Response("username must be provided in the your markdown")
    username = params.get("username")
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

        recent_activity_id = Activity.get_most_recent_activity_id(access_token)
        image_id = user["image_id"]
        # If the user exists and latest avtivity id matches activity id, return image directly
        if user["recent_activity_id"] != recent_activity_id:
            # save token and image to database -> return image
            activity_detail = Activity.parse_activity(recent_activity_id, access_token)
            print("activity_detail", activity_detail)
            if activity_detail["polyline"]:
                routePlot = RoutePlot()
                # this will generate an html
                routePlot.plot(polyline=activity_detail["polyline"])
                screenShotter = ScreenShotter()
                # take screenshot of the html with webdriver
                screenShotter.take_screenshot(
                    html_file_name="map_with_polyline.html",
                    export_image_name="img/map_with_polyline.png",
                )
                with open("img/map_with_polyline.png", "rb") as image_file:
                    image_data = image_file.read()

                image_id = fs.put(image_data, filename="image.jpg")

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

    image_data = fs.get(image_id).read()
    return Response(image_data, headers={"Content-Type": "image/png"})
