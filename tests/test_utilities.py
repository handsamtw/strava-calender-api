import sys
import os
from bson import ObjectId
from dotenv import load_dotenv
from pymongo import MongoClient

# Add project_root to the sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.utils import get_all_activities, refresh_access_token_if_expired


load_dotenv()
env = os.environ


# # # # Connect to MongoDB
MONGODB_PASSWORD = env.get("MONGODB_PASSWORD")
uri = f"mongodb+srv://samliao:{MONGODB_PASSWORD}@cluster0.7zimm5o.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(uri, username="samliao", password=MONGODB_PASSWORD)
db = client["strava-calendar"]
users_collection = db["users"]


def test_invalid_token():
    """Test case to verify handling of invalid token."""
    token = "abc"
    error_response, status_code = get_all_activities(token)
    expect_error_response = {
        "message": "Authorization Error",
        "errors": [{"resource": "Athlete", "field": "access_token", "code": "invalid"}],
    }

    assert error_response == expect_error_response
    assert status_code == 401


def test_valid_activities():
    """Test case to verify retrieval of valid activities."""
    uid = env.get("TEST_UID")
    user = users_collection.find_one({"_id": ObjectId(uid)})
    access_token = user["access_token"]
    print(access_token)
    refresh_token_response = refresh_access_token_if_expired(user)
    if refresh_token_response:
        print(refresh_token_response)
        access_token = refresh_token_response["access_token"]
    response, status_code = get_all_activities(access_token)
    assert status_code == 200
    assert 400 < len(response) < 500
