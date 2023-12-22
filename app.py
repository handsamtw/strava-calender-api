from pymongo import MongoClient
from gridfs import GridFS
from bson import ObjectId
import requests
from chalicelib.util import (
    expire_in_n_minutes,
    refresh_access_token,
    get_most_recent_activity_id,
    request_token,
    html_to_activity_image,
)
from chalice import Chalice, Response, CORSConfig
import os
from html2image import Html2Image

app = Chalice(app_name="strava-github-profile")
# I have to add this line to allow browser seeing the image
# Reference: https://stackoverflow.com/questions/56159447/chalice-framework-request-did-not-specify-an-accept-header-with-image-jpeg
app.api.binary_types = ["*/*"]

# # Connect to MongoDB
mongopass = os.getenv("MONGOPASS")
uri = f"mongodb+srv://samliao:{mongopass}@cluster0.cfszocb.mongodb.net/?retryWrites=true&w=majority"

client = MongoClient(uri, username="samliao", password=mongopass)
db = client["strava-github-profile"]
users_collection = db["users"]
fs = GridFS(db)

# Define CORS configuration
cors_config = CORSConfig(
    allow_origin="*",  # Change to specific origin(s) if needed
    allow_headers=["Authorization", "Content-Type"],
    max_age=600,  # Max cache time for preflight requests (in seconds)
)


@app.route("/random_image", methods=["GET"])
def random_image():
    output_path = "img"
    hti = Html2Image(output_path=output_path)

    html_content = """
<div class="strava-embed-placeholder" data-embed-type="activity" data-embed-id="10414933226" data-style="standard"></div>
<script src="https://strava-embeds.com/embed.js"></script>
"""

    hti.screenshot(html_str=html_content, save_as="my_image.png")
    with open(f"{output_path}/my_image.png", "rb") as file:
        image_data = file.read()

    return Response(
        body=image_data, status_code=200, headers={"Content-Type": "image/png"}
    )


# NOTE: The return _id will be stored in localstorage at frontend side
@app.route("/token", methods=["GET"], cors=cors_config)
def get_access_token():
    params = app.current_request.query_params
    code = params["code"]
    if not code:
        print("No code is found in redirect url. Access_token request denied")
        return "No code is found in redirect url"
    credentials = request_token(code)

    if isinstance(credentials, dict):
        result = users_collection.insert_one(credentials)
        return str(result.inserted_id)
    else:
        print(f"credentials is not an instance of dict.\n Credentials:{credentials}")
        return "Bad request"


@app.route("/{uid}", methods=["GET"])
def get_image(uid):
    user = users_collection.find_one({"_id": ObjectId(uid)})

    if not user:
        return Response(
            f"User id {uid} wasn't found in database.Check Strava authorization status",
            status_code=404,
        )
    else:
        access_token, refresh_token, expires_at = (
            user["access_token"],
            user["refresh_token"],
            user["expires_at"],
        )

        if expire_in_n_minutes(expires_at, 30):
            try:
                response = refresh_access_token(refresh_token)
                response.raise_for_status()  # Raises an HTTPError if the response status code is an error
                users_collection.update_one(
                    {"_id": id},
                    {
                        "$set": {
                            "access_token": response["access_token"],
                            "refresh_token": response["refresh_token"],
                            "expires_at": response["expires_at"],
                        }
                    },
                )
                # It is very important to replace old token with new one !!!
                access_token = response["access_token"]
            except requests.HTTPError as http_err:
                # Handling HTTP errors (4xx or 5xx status codes)
                error_message = f"HTTP error occurred: {http_err}"
                print(error_message)
                if response and response.text:
                    print("Error details:", response.text)
                return

            except Exception as err:
                # Handling other exceptions
                print("Other error occurred:", err)
                return

        # If the user exists and latest avtivity id matches activity id, return image directly
        recent_activity_id = get_most_recent_activity_id(access_token)
        if (
            "recent_activity_id" in user
            and user["recent_activity_id"] == recent_activity_id
        ):
            image_id = user["image_id"]
            image_data = fs.get(image_id).read()
            return Response(image_data, headers={"Content-Type": "image/png"})

        else:
            image_data = html_to_activity_image(recent_activity_id)
            image_id = fs.put(image_data, filename="image.png")
            if "image_id" in user:
                old_image_id = user["image_id"]
                fs.delete(ObjectId(old_image_id))
            users_collection.update_one(
                {"_id": ObjectId(uid)},
                {
                    "$set": {
                        "image_id": ObjectId(image_id),
                        "recent_activity_id": recent_activity_id,
                    }
                },
            )

            return Response(image_data, headers={"Content-Type": "image/png"})

            # activity_detail = parse_activity(recent_activity_id, access_token)
            # return activity_detail
            # if activity_detail["polyline"]:
            #     image_data = plot(
            #         polyline=activity_detail["polyline"], cropped=False
            #     )
            #     users_collection.update_one(
            #         {"_id": user["_id"]},
            #         {"$set": {"image": image_data}},
            #     )
