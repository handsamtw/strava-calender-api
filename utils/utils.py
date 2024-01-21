import io
import os
from base64 import b64encode
from datetime import datetime, timedelta

import requests
import numpy as np
import pandas as pd
import calmap
import calplot
import concurrent.futures
import aiohttp
import asyncio

import matplotlib as mpl


mpl.use("agg")


# def get_all_activities(token):
#     """
#     Retrieves all activities using the provided token from the Strava API.

#     Args:
#         token (str): Access token for Strava API.

#     Returns:
#         tuple: A tuple containing a list of activities and a status code.
#                - If successful, returns a list of activity data and status code 200.
#                - If there's an error, returns the error response and its status code.
#     """
#     payload = {}
#     headers = {"Authorization": f"Bearer {token}"}
#     activities = []
#     per_page = 200
#     required_columns = ["name", "distance", "moving_time", "type", "start_date_local"]

#     # Iterate through a maximum of 10 pages, which is 2000 activities (suppose to applied to most users)
#     for page_num in range(1, 10):
#         print(f"Page: {page_num}")
#         # Make a GET request to fetch activities
#         response = requests.request(
#             "GET",
#             f"https://www.strava.com/api/v3/activities?page={page_num}&per_page={per_page}",
#             headers=headers,
#             data=payload,
#             timeout=5,
#         )
#         if response.status_code != 200:
#             return response.json(), response.status_code

#         result = response.json()

#         if isinstance(result, list) and len(result) > 0:
#             for activity in result:
#                 selected_data = {col: activity[col] for col in required_columns}
#                 activities.append(selected_data)
#             # Break the loop if all data has been fetched
#             if len(result) < per_page:
#                 break
#         else:
#             break

#     return activities, 200


async def fetch_activity_page(session, token, page_num, per_page):
    url = (
        f"https://www.strava.com/api/v3/activities?page={page_num}&per_page={per_page}"
    )
    headers = {"Authorization": f"Bearer {token}"}

    async with session.get(url, headers=headers) as response:
        if response.status == 200:
            return await response.json()
        else:
            return {"error": await response.text()}, response.status


async def get_all_activities(token):
    payload = {}
    per_page = 200
    required_columns = ["name", "distance", "moving_time", "type", "start_date_local"]

    activities = []
    tasks = []

    async with aiohttp.ClientSession() as session:
        for page_num in range(1, 5):
            print(f"Page: {page_num}")
            task = fetch_activity_page(session, token, page_num, per_page)
            tasks.append(task)

        # Gather all tasks concurrently
        responses = await asyncio.gather(*tasks)

    for result in responses:
        if isinstance(result, list) and len(result) > 0:
            for activity in result:
                selected_data = {col: activity[col] for col in required_columns}
                activities.append(selected_data)
            # Break the loop if all data has been fetched
            if len(result) < per_page:
                break
        else:
            return result, 500  # Adjust the status code as needed

    return activities, 200


def summarize_activity(activities, sport_type=None):
    """
    Summarizes activities based on provided activity data, optionally filtered by sport types.

    Args:
        activities (list): A list containing activity data, each element as a dictionary.
        sport_type (list, optional): A list of sport types to filter the activities.
            If specified, only activities matching the selected sport types will be summarized.
            Defaults to None, indicating no filtering.

    Returns:
        pandas.DataFrame: A DataFrame summarizing the daily activity distances based on the provided data.

    """

    # Convert activities list to a DataFrame
    df = pd.DataFrame(activities)

    # Convert 'start_date_local' to datetime and set it as the index
    df["start_date_local"] = pd.to_datetime(
        df["start_date_local"], format="%Y-%m-%dT%H:%M:%SZ"
    )
    earliest_date = df["start_date_local"].min()
    latest_date = df["start_date_local"].max()
    df.set_index("start_date_local", inplace=True)

    # Filter activities by sport type if specified
    if sport_type:
        available_sport_type = {
            "run": "Run",
            "ride": "Ride",
            "swim": "Swim",
            "walk": "Walk",
            "hike": "Hike",
            "trail run": "Trail Run",
            "alpine ski": "Alpine Ski",
            "yoga": "Yoga",
            "hiit": "HIIT",
            "weight training": "Weight Training",
            "workout": "Workout",
        }

        sports_evl_by_time = ["yoga", "hiit", "weight training", "workout"]
        filtered_sport_type = []
        loop_broken = False  # Flag to check if the loop breaks prematurely
        eval_metric = "distance"
        for sport in sport_type:
            if sport.lower() in available_sport_type:
                filtered_sport_type.append(available_sport_type[sport.lower()])
                if sport.lower() in sports_evl_by_time:
                    eval_metric = "moving_time"
            else:
                loop_broken = True
                break
        if not loop_broken:
            df = df[df["type"].isin(filtered_sport_type)]
    # If df is empty, create a DataFrame with zeros so users could still get an empty calendar
    if df.empty:
        return (
            pd.DataFrame(
                {eval_metric: [0]},
                index=pd.date_range(start=earliest_date, end=latest_date, freq="D"),
            )
            .resample("D")
            .agg({eval_metric: "sum"})
        )

    # Group by date and calculate the sum for each day
    daily_summary = df.resample("D").agg({eval_metric: "sum"})

    # Clip outliers in the distance values for visualization clarity
    outlier_std = 3
    max_val = int(
        np.mean(daily_summary[eval_metric])
        + outlier_std * np.std(daily_summary[eval_metric])
    )
    daily_summary[eval_metric].clip(0, max_val, inplace=True)
    return daily_summary


def plot_calendar(daily_summary, theme="Reds"):
    """
    Plots a calendar heatmap based on the daily summary data.

    Args:
        daily_summary (pandas.DataFrame): A DataFrame containing daily summary data
        theme (str, optional): The color theme for the calendar heatmap. Default is 'Reds'.
            Available themes: 'Reds', 'BuGn', 'Greens', 'Blues', 'PuBu', 'RdPu', 'twilight',
            or 'All' to generate images for all available themes.

    Returns:
        dict: A dictionary containing base64 encoded images of calendar heatmaps generated
            based on the provided daily summary data and selected theme(s).
    """

    # Initialize a color map dictionary for different themes
    c_map = {
        "Reds": "Reds",
        "BuGn": "BuGn",
        "Greens": "Greens",
        "Blues": "Blues",
        "PuBu": "PuBu",
        "RdPu": "RdPu",
        "twilight": "twilight",
    }
    # Determine which theme(s) to process
    theme_to_process = (
        list(c_map.keys())
        if theme == "All"
        else [theme]
        if theme in c_map
        else ["Reds"]
    )

    # Initialize an empty dictionary to store encoded images
    image_dict = {}

    # Generate calendar heatmap for each theme in 'theme_to_process'
    for cur_theme in theme_to_process:
        fig, _ = calplot.calplot(
            daily_summary.iloc[:, 0],
            cmap=cur_theme,
            linewidth=1,
            linecolor="white",
            edgecolor=None,
            yearlabel_kws={"fontsize": 32, "color": "Gainsboro", "fontname": "Arial"},
        )
        # fig, _ = calmap.calendarplot(
        #     daily_summary.iloc[:, 0],
        #     cmap=cur_theme,
        #     linewidth=1,
        #     linecolor="white",
        #     edgecolor=None,
        # )

        # Encode the generated image to base64 and store it in 'image_dict'
        with io.BytesIO() as buffer:
            # fig.savefig(buffer, bbox_inches="tight", dpi=150, format="png")
            fig.savefig(buffer, bbox_inches="tight", format="png")
            buffer.seek(0)
            encoded_img = b64encode(buffer.getvalue()).decode("utf-8")
            image_dict[cur_theme] = encoded_img

    return image_dict


def plot_calendar_parallel(daily_summary, theme="Reds"):
    c_map = {
        "Reds": "Reds",
        "BuGn": "BuGn",
        "Greens": "Greens",
        "Blues": "Blues",
        "PuBu": "PuBu",
        "RdPu": "RdPu",
        "twilight": "twilight",
    }

    theme_to_process = (
        list(c_map.keys())
        if theme == "All"
        else [theme]
        if theme in c_map
        else ["Reds"]
    )

    image_dict = {}

    def generate_heatmap(cur_theme):
        fig, _ = calplot.calplot(
            daily_summary.iloc[:, 0],
            cmap=cur_theme,
            linewidth=1,
            linecolor="white",
            edgecolor=None,
            yearlabel_kws={"fontsize": 32, "color": "Gainsboro", "fontname": "Arial"},
        )

        with io.BytesIO() as buffer:
            fig.savefig(buffer, bbox_inches="tight", dpi=150, format="png")
            buffer.seek(0)
            encoded_img = b64encode(buffer.getvalue()).decode("utf-8")
            image_dict[cur_theme] = encoded_img

    # Using ThreadPoolExecutor to parallelize heatmap generation
    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.map(generate_heatmap, theme_to_process)

    return image_dict


def refresh_access_token_if_expired(user):
    """
    Refreshes the access token if the provided user's token is expired or about to expire within 30 minutes.

    Args:
        user (dict): A dictionary containing user information including 'expires_at' and 'refresh_token'.

    Returns:
        dict or None: If the access token is refreshed successfully, returns the updated token information
            (access token, refresh token, expires_at). Returns None if no token refresh was performed.
    """
    if expire_in_n_minutes(user["expires_at"], 30):
        refresh_token_url = os.getenv("REFRESH_TOKEN_URL")
        refresh_data = {
            "client_id": os.getenv("CLIENT_ID"),
            "client_secret": os.getenv("CLIENT_SECRET"),
            "grant_type": "refresh_token",
            "refresh_token": user["refresh_token"],
        }
        response = requests.post(refresh_token_url, data=refresh_data, timeout=5)

        return response.json(), response.status_code

    return {}, 200


def expire_in_n_minutes(expire_timestamp, minutes=30):
    """
    Checks if the provided expiration timestamp is within a certain number of minutes from the current time.

    Args:
        expire_timestamp (int): The expiration timestamp in seconds since the epoch.
        minutes (int, optional): The duration in minutes to check against expiration.
            Defaults to 30 minutes if not specified.

    Returns:
        bool: True if the expiration is within the specified number of minutes from the current time, otherwise False.
    """
    # Convert expiration timestamp to a datetime object
    expire_datetime = datetime.utcfromtimestamp(expire_timestamp)

    # Get the current time
    current_datetime = datetime.utcnow()

    # Calculate the time difference
    time_difference = expire_datetime - current_datetime

    # Check if the expiration is within 30 minutes from the current time
    return time_difference <= timedelta(minutes=minutes)


def request_token(code):
    """
    Requests access and refresh tokens from an OAuth2 server using the provided authorization code.

    Args:
        code (str): The authorization code obtained from the authentication flow.

    Returns:
        tuple: A tuple containing token information and HTTP status code.
            The token information is a dictionary with keys:
                - 'access_token' (str): The access token for accessing protected resources.
                - 'refresh_token' (str): The refresh token to obtain a new access token.
                - 'expires_at' (str): The timestamp indicating token expiration.
            The HTTP status code indicates the success or failure of the token request.

    Raises:
        None
    """
    env = os.environ
    url = env.get("REQUEST_TOKEN_URL")

    client_id = env.get("CLIENT_ID")
    client_secret = env.get("CLIENT_SECRET")

    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "grant_type": "authorization_code",
    }

    response = requests.request("POST", url, data=payload, timeout=5)
    if response.status_code == 200:
        data = response.json()
        return {
            "access_token": data["access_token"],
            "refresh_token": data["refresh_token"],
            "expires_at": data["expires_at"],
        }, 200

    return response.json(), response.status_code


def get_last_activity_id(access_token):
    """
    Fetches the ID of the last activity using the provided Strava access token.

    Parameters:
    - access_token (str): The Strava access token for authentication.

    Returns:
    Tuple[int, int] or Tuple[dict, int]: A tuple containing the last activity ID and HTTP status code (200),
    or a tuple containing the error response JSON and the corresponding HTTP status code.
    """
    url = "https://www.strava.com/api/v3/activities?per_page=1&page=1"
    headers = {"Authorization": f"Bearer {access_token}"}

    response = requests.get(url, headers=headers, timeout=5)

    if response.status_code == 200:
        data = response.json()
        if isinstance(data, list) and len(data) > 0 and "id" in data[0]:
            return data[0]["id"], 200

    return response.json(), response.status_code


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
