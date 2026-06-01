import io
import os
from base64 import b64encode
from datetime import datetime, timedelta
import asyncio
import tempfile
import pandas as pd
import httpx

temp_dir = tempfile.mkdtemp()
os.environ["MPLCONFIGDIR"] = temp_dir


import matplotlib as mpl
import matplotlib.pyplot as plt
from utils import calplot

mpl.use("agg")


async def get_all_activities(activity_cache, token):
    """
    Retrieves all activities using the provided token from the Strava API.
    Uses a single shared httpx client for connection reuse across all page fetches.
    """

    if token in activity_cache:
        print("actvitiy cache hit!")
        return activity_cache[token]

    headers = {"Authorization": f"Bearer {token}"}
    timeout = httpx.Timeout(timeout=30.0)
    semaphore = asyncio.Semaphore(14)

    async with httpx.AsyncClient(headers=headers, timeout=timeout) as client:
        # Probe pages 4 and 8 concurrently to estimate depth, then fetch everything
        probe4, probe8 = await asyncio.gather(
            _fetch_page(client, 4),
            _fetch_page(client, 8),
        )
        if not probe4:
            max_page_num = 4
        elif not probe8:
            max_page_num = 8
        else:
            max_page_num = 15

        # Fetch all remaining pages in parallel (probed pages are re-fetched; results are fast)
        tasks = [
            _fetch_page_with_sem(client, page_num, semaphore)
            for page_num in range(1, max_page_num)
        ]
        pages = await asyncio.gather(*tasks)

    result_list = [act for page in pages if page for act in page]
    activity_cache[token] = result_list
    return result_list


async def _fetch_page_with_sem(client, page_num, semaphore):
    async with semaphore:
        return await _fetch_page(client, page_num)


async def _fetch_page(client, page_num):
    print("Page num: ", page_num)
    url = f"https://www.strava.com/api/v3/activities?page={page_num}&per_page=200"
    required_columns = [
        "name",
        "distance",
        "moving_time",
        "type",
        "start_date_local",
        "total_elevation_gain",
    ]
    response = await client.get(url)
    if response.status_code == 200:
        activities = response.json()
        if not activities:
            return None
        return [
            {col: activity[col] for col in required_columns}
            for activity in activities
        ]
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
                eval_metric = "moving_time"
            if filtered_sport_type == "Ride":
                df = df[df["type"].isin(["Ride", "VirtualRide"])]
            elif filtered_sport_type == "Run":
                df = df[df["type"].isin(["Run", "VirtualRun"])]
            else:
                df = df[df["type"] == filtered_sport_type]

    print("Total activity:", df.shape[0])
    # If df is empty, return two empty dataframe
    if df.empty:
        return df, pd.DataFrame()

    # Group by date and calculate the sum for each day
    agg_param = {eval_metric: "sum"}
    if eval_metric == "distance":
        agg_param["total_elevation_gain"] = "sum"
    daily_summary = df.resample("D").agg(agg_param)

    df_activity_count = df.groupby(df.index.year).size().rename("count")
    df_eval_per_year = daily_summary.groupby(daily_summary.index.year)[
        eval_metric
    ].sum()
    stat_summary = pd.DataFrame(
        {"count": df_activity_count, eval_metric: df_eval_per_year}
    )
    if eval_metric == "distance":
        df_elevation_per_year = daily_summary.groupby(daily_summary.index.year)[
            "total_elevation_gain"
        ].sum()
        stat_summary["elevation"] = df_elevation_per_year

    stat_summary["count"] = stat_summary["count"].fillna(0)

    return daily_summary, stat_summary


def plot_calendar(daily_summary, stat_summary, username, sport_type, cmap, unit):

    def generate_heatmap(cmap):
        fig, _ = calplot.calplot(
            daily_summary.iloc[:, 0] / unit_factor,
            yearascending=False,
            ax_title=stat_text_dict,
            suptitle=suptitle,
            suptitle_kws=suptitle_kws,
            cmap=cmap,
            linewidth=1,
            linecolor="white",
            edgecolor=None,
            yearlabel_kws=yearlabel_kws,
        )
        poweredby_text = "Power by @handsamtw - strava-calender.vercel.app"
        fig.text(0.05, -0.05, poweredby_text, color="#ababab", fontsize=10)
        fig.text(0.79, -0.05, f"unit: {unit_text}", color="#ababab", fontsize=9)
        with io.BytesIO() as buffer:
            fig.savefig(buffer, bbox_inches="tight", dpi=150, format="png")
            buffer.seek(0)
            encoded_img = b64encode(buffer.getvalue()).decode("utf-8")
            plt.close()
            return encoded_img

    unit_info = {
        "imperial": {
            "distance_unit_factor": 1609,
            "distance_unit_text": "mi",
            "elev_unit_factor": 0.3048,
            "elev_unit_text": "ft",
            "distance_swim_factor": 0.914,
            "distance_swim_text": "yd",
        },
        "metric": {
            "distance_unit_factor": 1000,
            "distance_unit_text": "km",
            "elev_unit_factor": 1,
            "elev_unit_text": "m",
            "distance_swim_factor": None,
            "distance_swim_text": None,
        },
    }

    if "distance" not in stat_summary:
        unit_factor = 60
        unit_text = "min"
        stat_text_dict = stat_summary.apply(
            lambda row: f"{row['count']:,.0f} Activities "
            f"({row['moving_time']/unit_factor:,.0f} {unit_text})",
            axis=1,
        ).to_dict()
    else:

        unit_type = unit_info[unit.lower()]
        unit_factor = unit_type["distance_unit_factor"]
        unit_text = unit_type["distance_unit_text"]
        elev_unit_factor = unit_type["elev_unit_factor"]
        elev_unit_text = unit_type["elev_unit_text"]

        if (
            sport_type.lower() == "swim"
            and unit_type["distance_swim_factor"] is not None
        ):
            unit_factor = unit_type["distance_swim_factor"]
            unit_text = unit_type["distance_swim_text"]

        stat_text_dict = stat_summary.apply(
            lambda row: f"{row['count']:,.0f} Activities "
            f"({row['distance']/unit_factor:,.0f} {unit_text} / "
            f"{row['elevation']/elev_unit_factor:,.0f} {elev_unit_text} elev)",
            axis=1,
        ).to_dict()

    suptitle = (
        f"{username}'s {sport_type} on Strava" if username and sport_type else None
    )
    suptitle_kws = (
        {"x": 0.45, "y": 1.04, "fontsize": 20, "color": "#ababab"} if suptitle else None
    )
    yearlabel_kws = {"fontsize": 32, "color": "Gainsboro", "fontname": "Arial"}

    image = generate_heatmap(cmap)

    return image


async def refresh_access_token_if_expired(user):
    """
    Refreshes the access token if the provided user's token is expired or about to expire within 30 minutes.
    """
    if expire_in_n_minutes(user["expires_at"], 30):
        refresh_token_url = os.getenv("REFRESH_TOKEN_URL")
        refresh_data = {
            "client_id": os.getenv("CLIENT_ID"),
            "client_secret": os.getenv("CLIENT_SECRET"),
            "grant_type": "refresh_token",
            "refresh_token": user["refresh_token"],
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(refresh_token_url, data=refresh_data)
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
    Uses synchronous httpx since this is called from a sync FastAPI endpoint (runs in threadpool).
    """
    env = os.environ
    url = env.get("REQUEST_TOKEN_URL")

    payload = {
        "client_id": env.get("CLIENT_ID"),
        "client_secret": env.get("CLIENT_SECRET"),
        "code": code,
        "grant_type": "authorization_code",
    }

    response = httpx.post(url, data=payload)

    if response.status_code == 200:
        data = response.json()
        username = _get_user_name_sync(data["access_token"])
        return {
            "access_token": data["access_token"],
            "refresh_token": data["refresh_token"],
            "expires_at": data["expires_at"],
            "username": username,
        }, 200

    return response.json(), response.status_code


def _get_user_name_sync(access_token):
    """Sync version used only by request_token (called from threadpool endpoint)."""
    url = "https://www.strava.com/api/v3/athlete"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = httpx.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data["firstname"] + " " + data["lastname"]
    return ""


async def get_user_name(access_token):
    url = "https://www.strava.com/api/v3/athlete"
    headers = {"Authorization": f"Bearer {access_token}"}

    async with httpx.AsyncClient(headers=headers) as client:
        response = await client.get(url)
    if response.status_code == 200:
        data = response.json()
        return data["firstname"] + " " + data["lastname"]

    return ""




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
