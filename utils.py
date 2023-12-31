from base64 import b64encode
import requests
import numpy as np
import pandas as pd
import io
import calmap
import os

os.environ["MPLCONFIGDIR"] = os.getcwd() + "/configs/"

from datetime import datetime, timedelta
import matplotlib

matplotlib.use("agg")


def get_all_activities(token):
    payload = {}
    headers = {"Authorization": f"Bearer {token}"}
    activities = []
    per_page = 200
    required_columns = ["name", "distance", "moving_time", "type", "start_date_local"]
    for page_num in range(1, 10):
        print(f"Page: {page_num}")
        response = requests.request(
            "GET",
            f"https://www.strava.com/api/v3/activities?page={page_num}&per_page={per_page}",
            headers=headers,
            data=payload,
        )
        if response.status_code != 200:
            print(response.status_code, response.content)
            break
        else:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                for activity in result:
                    selected_data = {col: activity[col] for col in required_columns}
                    activities.append(selected_data)
                if len(result) < 200:
                    print("We have fetched all the data. Yaho")
                    break
            else:
                print("No valid result")
                break

    return activities


def summarize_activity(activities, sport_type=None):
    ACTIVITY_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
    available_sport_type = ["Run", "Ride", "Swim", "Walk"]
    # Convert to DataFrame
    df = pd.DataFrame(activities)

    # Convert 'start_date_local' to datetime and set it as the index
    df["start_date_local"] = pd.to_datetime(
        df["start_date_local"], format=ACTIVITY_FORMAT
    )
    df.set_index("start_date_local", inplace=True)

    # if sport_type and sport_type in valid_sport_type:
    if sport_type and all(sport in available_sport_type for sport in sport_type):
        df = df[df["type"].isin(sport_type)]

    # Group by date and calculate the sum for each day
    daily_summary = df.resample("D").agg({"moving_time": "sum", "distance": "sum"})
    daily_summary.rename(columns={"moving_time": "time"}, inplace=True)
    # clip all outliers to make visualization more intuitive
    outlier_std = 3
    for col in daily_summary.columns:
        max_val = int(
            np.mean(daily_summary[col]) + outlier_std * np.std(daily_summary[col])
        )
        daily_summary[col].clip(0, max_val, inplace=True)

    return daily_summary


def plot_calendar(daily_summary, plot_by="time", theme="Reds", batch_process=False):
    batch_process = theme == "All"
    CMAP = {
        "Reds": "Reds",
        "BuGn": "BuGn",
        "Greens": "Greens",
        "Blues": "Blues",
        "PuBu": "PuBu",
        "RdPu": "RdPu",
        "twilight": "twilight",
    }
    if plot_by not in ["time", "distance"]:
        plot_by = "time"

    if theme not in CMAP:
        theme = "Reds"

    theme_to_process = list(CMAP.keys()) if batch_process else [theme]
    encoded_imges = []

    for cur_theme in theme_to_process:
        fig, ax = calmap.calendarplot(
            daily_summary[plot_by],
            daylabels=["M", "TU", "W", "TH", "F", "SA", "SU"],
            cmap=cur_theme,
            linewidth=1,
            linecolor="white",
            fig_kws=dict(figsize=(8, 5)),
        )

        with io.BytesIO() as buffer:  # use buffer memory
            fig.savefig(buffer, format="png")
            buffer.seek(0)
            encoded_img = b64encode(buffer.getvalue()).decode("utf-8")

            encoded_imges.append({"theme": cur_theme, "imageUrl": encoded_img})
    return encoded_imges


#     # Save plot

#     # fig.savefig(out_file, dpi=600)
#     # with open(out_file, "rb") as file:
#     #     image_data = file.read()
#     #     return image_data


# # if the token hasn't expire, will return the same token
def refresh_access_token_if_expired(user):
    if expire_in_n_minutes(user["expires_at"], 30):
        url = os.getenv("REFRESH_TOKEN_URL")
        refresh_data = {
            "client_id": os.getenv("CLIENT_ID"),
            "client_secret": os.getenv("CLIENT_SECRET"),
            "grant_type": "refresh_token",
            "refresh_token": user["refresh_token"],
        }
        response = requests.post(url, data=refresh_data)
        return response.json()


def expire_in_n_minutes(expire_timestamp, minutes=30):
    # Convert expiration timestamp to a datetime object
    expire_datetime = datetime.utcfromtimestamp(expire_timestamp)

    # Get the current time
    current_datetime = datetime.utcnow()

    # Calculate the time difference
    time_difference = expire_datetime - current_datetime

    # Check if the expiration is within 30 minutes from the current time
    return time_difference <= timedelta(minutes=minutes)


# def get_most_recent_activity_id(access_token):
#     url = f"{ACTIVITIES_URL}?per_page=1&page=1"
#     headers = {"Authorization": f"Bearer {access_token}"}

#     response = requests.get(url, headers=headers)

#     if response.status_code == 200:
#         data = response.json()
#         if isinstance(data, list) and len(data) > 0 and "id" in data[0]:
#             return data[0]["id"]

#         else:
#             print(f"Check response type")
#             return None
#     else:
#         print(f"Failed to retrieve data. Status code: {response.status_code}")
#         return None


def request_token(code):
    config = os.environ
    url = config.get("REQUEST_TOKEN_URL")
    client_id = config.get("CLIENT_ID")
    client_secret = config.get("CLIENT_SECRET")

    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "grant_type": "authorization_code",
    }

    response = requests.request("POST", url, data=payload)
    if response.status_code == 200:
        data = response.json()
        return {
            "access_token": data["access_token"],
            "refresh_token": data["refresh_token"],
            "expires_at": data["expires_at"],
        }

    else:
        return "Error!!!"


# def html_to_activity_image(activity_id):
#     output_path = "/tmp"
#     hti = Html2Image(output_path=output_path)

#     html_content = (
#         "<div class='strava-embed-placeholder' data-embed-type='activity' data-embed-id="
#         + str(activity_id)
#         + " data-style='standard'></div><script src='https://strava-embeds.com/embed.js'></script>"
#     )

#     hti.screenshot(html_str=html_content, save_as="my_image.png")
#     with open(f"{output_path}/my_image.png", "rb") as file:
#         image_data = file.read()
#         return image_data
