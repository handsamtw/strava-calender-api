import io
import os
from base64 import b64encode
from datetime import datetime, timedelta

import requests
import numpy as np
import pandas as pd
import calplot
import concurrent.futures
import matplotlib as mpl
import matplotlib.pyplot as plt

import httpx
import asyncio

mpl.use("agg")


async def get_all_activities(activity_cache, token):
    """
    Retrieves all activities using the provided token from the Strava API.

    Args:
        token (str): Access token for Strava API.

    Returns:
        tuple: A tuple containing a list of activities and a status code.
               - If successful, returns a list of activity data and status code 200.
               - If there's an error, returns the error response and its status code.
    """

    
    if token in activity_cache:
        print("actvitiy cache hit!")
        return activity_cache[token], 200
    
    max_page_num = activity_num_estimator(token)
    # max_page_num = 11
    tasks = []
    for page_num in range(1, max_page_num):
        activity = _fetch_activities_async(token, page_num)
        
        if not activity:
            break
        tasks.append(activity)
    

    filtered_activities = await asyncio.gather(*tasks)
    result_list = []
    for filtered_activity in filtered_activities:
        if filtered_activity is not None:
            result_list.extend(filtered_activity)
    activity_cache[token] = result_list
    return result_list, 200

async def _fetch_activities_async(token, page_num):
    print("Page num: ", page_num)
    url = f"https://www.strava.com/api/v3/activities?page={page_num}&per_page=200"
    headers = {"Authorization": f"Bearer {token}"}
    required_columns = ["name", "distance", "moving_time", "type", "start_date_local"]
    async with httpx.AsyncClient(headers=headers) as client:
        response = await client.get(url)
        if response.status_code == 200:
            activities = response.json()
            filtered_activities = [
                {col: activity[col] for col in required_columns}
                for activity in activities
            ]
            return filtered_activities
            # return response.json()
        else:
            return None  # Handle error cases based on your requirements

def _fetch_activities_sync(token, page_num):
    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://www.strava.com/api/v3/activities?page={page_num}&per_page=200"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        activities = response.json()
        return activities
    else:
        return None  


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

        sports_evl_by_time = ["Yoga", "HIIT", "Weight Training", "Workout"]
        eval_metric = "distance"

        if sport_type.lower() in available_sport_type:
            filtered_sport_type = available_sport_type[sport_type.lower()]
            if filtered_sport_type in sports_evl_by_time:
                eval_metric = 'moving_time'
            df = df[df["type"] == filtered_sport_type] 
    
    print("Total activity:", df.shape[0])
    # If df is empty, return two empty dataframe
    if df.empty:
        return df, pd.DataFrame()

    # Group by date and calculate the sum for each day
    daily_summary = df.resample("D").agg({eval_metric: "sum"})
    df_activity_count = df.groupby(df.index.year).size().rename('count')

    stat_per_year = (daily_summary.groupby(daily_summary.index.year)[eval_metric].sum())
    
    stat_summary = pd.concat([df_activity_count, 
                            stat_per_year], 
                            axis=1).reset_index()
    stat_summary.columns = ["year", 'count', eval_metric]
    stat_summary["count"] = stat_summary["count"].fillna(0)
    stat_summary = stat_summary.sort_values(by='year')
    return daily_summary, stat_summary.to_dict(orient='records')


def plot_calendar(daily_summary, username, sport_type, unit="metric", theme="Reds", is_parallel=True):
    def generate_heatmap(cur_theme):

        unit_type = unit_info[unit]

        meter_to_unit_factor = unit_type["unit_factor"]
        unit_text = unit_type["unit_text"]

        if sport_type.lower() == 'swim' and unit_type["swim_factor"] is not None:
            meter_to_unit_factor = unit_type["swim_factor"]
            unit_text = unit_type["swim_text"]
        
        
        
        fig, _ = calplot.calplot(
            daily_summary.iloc[:, 0] / meter_to_unit_factor,
            suptitle = suptitle,
            suptitle_kws=suptitle_kws,
            cmap=cur_theme,
            linewidth=1,
            linecolor="white",
            edgecolor=None,
            yearlabel_kws=yearlabel_kws
        )
        
        
        poweredby_text = "Power by @handsamtw - strava-calender.vercel.app"
        fig.text(0, -0.05, poweredby_text,color='#ababab', fontsize=12)
        fig.text(0.83, -0.05, f"unit: {unit_text}",color='#ababab', fontsize=10)
        with io.BytesIO() as buffer:
            fig.savefig(buffer, bbox_inches="tight", dpi=200, format="png")
            buffer.seek(0)
            encoded_img = b64encode(buffer.getvalue()).decode("utf-8")
            image_dict[cur_theme] = encoded_img
        plt.close()

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
        "YlGn": "YlGn",
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
    unit_info = {
        "imperial": {"unit_factor": 1609, 
                     "unit_text": "mi", 
                     "swim_factor": 0.914, 
                     "swim_text": "yd"},
        "metric": {"unit_factor": 1000, 
                   "unit_text": "km", 
                   "swim_factor": None, 
                   "swim_text": None}
        }
    suptitle = f"{username}'s {sport_type} on Strava" if username and sport_type else None
    suptitle_kws = {"x":0.45, "y":1.07,"fontsize": 20, 'color': '#ababab'} if suptitle else None
    yearlabel_kws = {"fontsize": 32, "color": "Gainsboro", "fontname": "Arial"}
    # Initialize an empty dictionary to store encoded images
    image_dict = {}
    
    # Generate calendar heatmap for each theme in 'theme_to_process'
    if is_parallel:
        # Using ThreadPoolExecutor to parallelize heatmap generation
        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.map(generate_heatmap, theme_to_process)
    else:
        for theme in theme_to_process:
            generate_heatmap(theme)

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
        response = requests.post(refresh_token_url, data=refresh_data)

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

    response = requests.request("POST", url, data=payload)
    if response.status_code == 200:
        data = response.json()
        return {
            "access_token": data["access_token"],
            "refresh_token": data["refresh_token"],
            "expires_at": data["expires_at"],
        }, 200

    return response.json(), response.status_code

# Deprecated
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

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        if isinstance(data, list) and len(data) > 0 and "id" in data[0]:
            return data[0]["id"], 200

    return response.json(), response.status_code

def get_user_name(access_token):
    url = "https://www.strava.com/api/v3/athlete"
    headers = {"Authorization": f"Bearer {access_token}"}

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data["firstname"] + " " + data["lastname"]
            
    return ""

def activity_num_estimator(token):   
    tier1 = _fetch_activities_sync(token, 4)
    if not tier1:
        return 4
    else:
        tier2 = _fetch_activities_sync(token, 8)
        if not tier2:
            return 8
    return 12
    


    # if user have more than 1000 activity, we classified as heavy user

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
