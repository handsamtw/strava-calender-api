# from ..api.index import app  # Importing the app instance from api.index
import sys
import os

from bson import ObjectId

# Add project_root to the sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.utils import get_all_activities, refresh_access_token_if_expired
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

env = os.environ

# # Access individual variables
mongopass = env.get("MONGODB_PASSWORD")

# # # # Connect to MongoDB
uri = f"mongodb+srv://samliao:{mongopass}@cluster0.7zimm5o.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(uri, username="samliao", password=mongopass)
db = client["strava-calendar"]
users_collection = db["users"]


def test_load_secrets():
    assert env.get("REQUEST_TOKEN_URL") == "https://www.strava.com/oauth/token"
    assert env.get("REFRESH_TOKEN_URL") == "https://www.strava.com/api/v3/oauth/token"


# def test_invalid_token():
#     token = "abc"
#     error_response, status_code = get_all_activities(token)
#     expect_error_response = {
#         "message": "Authorization Error",
#         "errors": [{"resource": "Athlete", "field": "access_token", "code": "invalid"}],
#     }

#     assert error_response == expect_error_response
#     assert status_code == 401


# def test_valid_activities():
#     # uid = env.get("TEST_UID")
#     uid = os.environ.get("TEST_UID")
#     if uid:
#         # Use uid in your code
#         user = users_collection.find_one({"_id": ObjectId(uid)})
#     else:
#         print("TEST_UID environment variable is not set")
#         uid = "65985d9ef1bd9d46ad69ab66"
#         user = users_collection.find_one({"_id": ObjectId(uid)})

#     access_token = user["access_token"]
#     refresh_token_response = refresh_access_token_if_expired(user)
#     if refresh_token_response:
#         access_token = refresh_token_response["access_token"]
#     response, status_code = get_all_activities(access_token)
#     assert status_code == 200
#     assert 400 < len(response) < 500
