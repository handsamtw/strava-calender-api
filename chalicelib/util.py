import requests
from math import log2, floor
from datetime import datetime, timedelta
import os
import folium
from PIL import Image
from geopy.distance import great_circle
import io
from chalicelib import ACTIVITIES_URL, REFRESH_TOKEN_URL


def human_readable_time(seconds):
    minutes = int(seconds // 60)  # Calculate the number of minutes
    remaining_seconds = int(seconds % 60)  # Calculate the remaining seconds
    if minutes == 0:
        return f"{remaining_seconds} s"
    elif remaining_seconds == 0:
        return f"{minutes} m"
    else:
        return f"{minutes} m {remaining_seconds} s"


def calculate_pace(distance_meters, duration_seconds):
    # Convert distance from meters to kilometers
    distance_kms = distance_meters / 1000

    # Convert duration from seconds to minutes
    duration_minutes = duration_seconds / 60

    # Calculate pace in minutes per kilometer
    pace_decimal = duration_minutes / distance_kms

    # Convert pace to minutes and seconds
    pace_minutes = int(pace_decimal)
    pace_seconds = int((pace_decimal * 60) % 60)

    # Format the pace as "MM:SS/km"
    formatted_pace = f"{pace_minutes}:{pace_seconds:02d}/km"

    return formatted_pace


def decode_polyline(polyline_str):
    index = 0
    coordinates = []
    current_lat = 0
    current_lng = 0

    while index < len(polyline_str):
        shift = 0
        result = 0

        while True:
            byte = ord(polyline_str[index]) - 63
            index += 1
            result |= (byte & 0x1F) << shift
            shift += 5
            if byte < 0x20:
                break

        d_lat = ~(result >> 1) if result & 1 else (result >> 1)
        current_lat += d_lat

        shift = 0
        result = 0

        while True:
            byte = ord(polyline_str[index]) - 63
            index += 1
            result |= (byte & 0x1F) << shift
            shift += 5
            if byte < 0x20:
                break

        d_lng = ~(result >> 1) if result & 1 else (result >> 1)
        current_lng += d_lng

        coordinates.append((current_lat / 1e5, current_lng / 1e5))

    return coordinates


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
        print(f"Failed to retrieve data. Status code: {response.status_code}")


def expire_in_n_minutes(expire_timestamp, minutes=30):
    # Convert expiration timestamp to a datetime object
    expire_datetime = datetime.utcfromtimestamp(expire_timestamp)

    # Get the current time
    current_datetime = datetime.utcnow()

    # Calculate the time difference
    time_difference = expire_datetime - current_datetime

    # Check if the expiration is within 30 minutes from the current time
    return time_difference <= timedelta(minutes=minutes)


def image_to_byte_array(image: Image) -> bytes:
    # BytesIO is a file-like buffer stored in memory
    imgByteArr = io.BytesIO()
    # image.save expects a file-like as a argument
    image.save(imgByteArr, format="PNG")
    # Turn the BytesIO object back into a bytes object
    imgByteArr = imgByteArr.getvalue()
    return imgByteArr


def calculate_zoom_for_coordinates(coordinates, map_width_px=1450):
    # Extract latitude and longitude values from the coordinates
    latitudes = [coord[0] for coord in coordinates]
    longitudes = [coord[1] for coord in coordinates]

    # Calculate the bounding box of the coordinates
    min_lat, max_lat = min(latitudes), max(latitudes)
    min_lon, max_lon = min(longitudes), max(longitudes)
    center = [(min_lat + max_lat) / 2, (min_lon + max_lon) / 2]

    # Calculate the distance in meters between the diagonal corners of the bounding box
    diagonal_distance = great_circle((min_lat, min_lon), (max_lat, max_lon)).meters

    # Estimate the pixel width of the map (Google Maps assumes 256px tiles)
    scaling_factor = log2(diagonal_distance / map_width_px)

    # Calculate the initial zoom level based on the diagonal distance and pixel width
    zoom_level = floor(16 - scaling_factor)
    print(f"diagonal_distance: {diagonal_distance}, zoom_level: {zoom_level}")
    return center, zoom_level


def plot(polyline, cropped=True):
    coordinates = decode_polyline(polyline)
    center, zoom_level = calculate_zoom_for_coordinates(coordinates)

    # Create a folium map centered at a location
    # tiles='https://{s}.tiles.example.com/{z}/{x}/{y}.png'
    m = folium.Map(location=center, zoom_start=zoom_level)

    # folium.TileLayer(
    #     tiles=xyz.CartoDB.Positron.url, attr=xyz.CartoDB.Positron.attribution
    # ).add_to(m)
    folium.TileLayer(tiles="CartoDB positron").add_to(m)

    # Add a polyline to the map
    folium.PolyLine(
        locations=coordinates,
        color="orange",
        line_cap="round",
    ).add_to(m)
    # m.save(f"{saved_name}.html")

    img_data = m._to_png(0.3)
    if cropped:
        img = Image.open(io.BytesIO(img_data))
        width, height = img.size
        # Calculate the top-left corner to extract the center
        size = min(width, height) * 0.9

        # Calculate the coordinates to crop the square
        left = (width - size) / 2
        top = (height - size) / 2
        right = (width + size) / 2
        bottom = (height + size) / 2
        cropped_image = img.crop((left, top, right, bottom))
        return image_to_byte_array(cropped_image)
    else:
        return img_data


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


def parse_activity(id, access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"{ACTIVITIES_URL}/{id}"
    response = requests.get(url, headers=headers)
    data = response.json()
    pace = calculate_pace(data["distance"], data["moving_time"])
    city, state = None, None

    if "segment_efforts" in data:
        first_segment = data["segment_efforts"][0]["segment"]
        city, state = first_segment["city"], first_segment["state"]

    return {
        "type": data["type"],
        "start_date_local": data["start_date_local"],
        "locations": {"city": city, "state": state},
        "name": data["name"],
        "description": data["description"],
        "distance": data["distance"],
        "pace": pace,
        "time": data["moving_time"],
        "total_elevation_gain": data["total_elevation_gain"],
        "polyline": data["map"]["polyline"],
    }
