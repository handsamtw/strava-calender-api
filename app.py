from flask import Flask, Response, request
import io
from DatabaseConnector import DatabaseConnector
from RecentActivity import RecentActivity
from RoutePlot import RoutePlot
from ScreenShotter import ScreenShotter
from pymongo import MongoClient
from gridfs import GridFS
from bson import ObjectId
import io

app = Flask(__name__)
# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["strava_github_profile"]
users_collection = db["users"]
fs = GridFS(db)


@app.route("/get_image")
def get_image():
    access_token = request.args.get("access_token")
    refresh_token = request.args.get("refresh_token")
    user_data = users_collection.find_one({"access_token": access_token})
    recent_activity_worker = RecentActivity(access_token=access_token)
    recent_activity_id = recent_activity_worker.get_most_recent_activity_id()

    # If the user exists and latest avtivity id = activity id, return image,
    if user_data and user_data["recent_activity_id"] == recent_activity_id:
        image_id = user_data["image_id"]
    else:
        # save token and image to database -> return image
        activity_detail = recent_activity_worker.parse_activity(recent_activity_id)
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
        databaseConnector = DatabaseConnector()
        image_id = databaseConnector.save_img("img/map_with_polyline.png")
        credential_data = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "recent_activity_id": recent_activity_id,
            "image_id": ObjectId(image_id),
        }
        if not user_data:
            users_collection.insert_one(credential_data)
        else:
            old_imagee_id = user_data["image_id"]
            fs.delete(ObjectId(old_imagee_id))
            users_collection.update_one(
                {"access_token": access_token},
                {"$set": {"image_id": ObjectId(image_id)}},
            )

    image_data = fs.get(image_id).read()
    return Response(image_data, mimetype="image/png")


if __name__ == "__main__":
    app.run(debug=True)
