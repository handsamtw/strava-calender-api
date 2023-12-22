import requests
from datetime import datetime, timedelta
import os
from chalicelib import ACTIVITIES_URL, REFRESH_TOKEN_URL
from chalice import Response
from html2image import Html2Image


# if the token hasn't expire, will return the same token
def refresh_access_token(refresh_token):
    url = REFRESH_TOKEN_URL
    refresh_data = {
        "client_id": os.getenv("CLIENT_ID"),
        "client_secret": os.getenv("CLIENT_SECRET"),
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }
    response = requests.post(url, data=refresh_data)
    if response.status_code == 200:
        return response.json()

    else:
        return Response("Failed to retrieve data.", status_code=response.status_code)


def expire_in_n_minutes(expire_timestamp, minutes=30):
    # Convert expiration timestamp to a datetime object
    expire_datetime = datetime.utcfromtimestamp(expire_timestamp)

    # Get the current time
    current_datetime = datetime.utcnow()

    # Calculate the time difference
    time_difference = expire_datetime - current_datetime

    # Check if the expiration is within 30 minutes from the current time
    return time_difference <= timedelta(minutes=minutes)


def get_most_recent_activity_id(access_token):
    url = f"{ACTIVITIES_URL}?per_page=1&page=1"
    headers = {"Authorization": f"Bearer {access_token}"}

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        if isinstance(data, list) and len(data) > 0 and "id" in data[0]:
            return data[0]["id"]

        else:
            print(f"Check response type")
            return None
    else:
        print(f"Failed to retrieve data. Status code: {response.status_code}")
        return None


def request_token(code):
    url = "https://www.strava.com/oauth/token"

    payload = {
        "client_id": os.getenv("CLIENT_ID"),
        "client_secret": os.getenv("CLIENT_SECRET"),
        "code": code,
        "grant_type": "authorization_code",
    }
    files = []
    headers = {}

    response = requests.request("POST", url, headers=headers, data=payload, files=files)
    print(response.json())
    if response.status_code == 200:
        data = response.json()
        return {
            "access_token": data["access_token"],
            "refresh_token": data["refresh_token"],
            "expires_at": data["expires_at"],
        }

    else:
        return "Error!!!"


def html_to_activity_image(activity_id):
    output_path = "/tmp"
    hti = Html2Image(output_path=output_path)

    html_content = (
        "<div class='strava-embed-placeholder' data-embed-type='activity' data-embed-id="
        + str(activity_id)
        + " data-style='standard'></div><script src='https://strava-embeds.com/embed.js'></script>"
    )

    hti.screenshot(html_str=html_content, save_as="my_image.png")
    with open(f"{output_path}/my_image.png", "rb") as file:
        image_data = file.read()
        return image_data
