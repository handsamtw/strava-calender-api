import pymongo
from gridfs import GridFS
from PIL import Image
import io
from bson import ObjectId  # Import ObjectId from bson library


class ImageProcessor:
    def __init__(self):
        self.client, self.db, self.fs = self.connect_mongodb()

    def connect_mongodb(self):
        # MongoDB connection
        client = pymongo.MongoClient("mongodb://localhost:27017/")
        db = client[
            "strava_github_profile"
        ]  # Replace "mydatabase" with your database name
        fs = GridFS(db)
        return client, db, fs

    def save_img(self, image_path="path/to/your/image.jpg"):
        # Read the image file as bytes
        with open(image_path, "rb") as image_file:
            image_data = image_file.read()

        # Store the image data in MongoDB using GridFS
        img_id = self.fs.put(image_data, filename="image.jpg")
        return img_id

    def save_credential(self, access_token, refresh_token, image_id):
        # Collection to store user tokens and image IDs
        users_collection = self.db["users"]

        # Example data: Access Token, Refresh Token, and Image ID
        user_data = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "image_id": ObjectId(image_id),
        }
        users_collection.insert_one(user_data)

    def retrieve_image(self, image_id):
        # ID of the image you want to retrieve as an ObjectId
        stored_file_id = ObjectId(image_id)

        # Retrieve the image from MongoDB using GridFS by its ObjectId
        file_data = self.fs.get(stored_file_id)

        # Read the image data from the GridFS file object
        image_data = file_data.read()
        return image_data

        # # Convert the bytes back to an image (PIL Image in this example)
        # img = Image.open(io.BytesIO(image_data))

        # # Display or save the retrieved image as needed
        # img.show()  # Display the image
