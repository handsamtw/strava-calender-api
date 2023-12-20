import requests
from math import radians, log10, pi, sin, cos, atan2, sqrt
from dotenv import dotenv_values
from datetime import datetime, timedelta
from constants import REFRESH_TOKEN_URL
import folium
from PIL import Image


import io


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


def calculate_distance(coord1, coord2):
    # Calculate distance (in kilometers) between two coordinates using Haversine formula
    R = 6371.0  # Earth radius in kilometers

    lat1, lon1 = radians(coord1[0]), radians(coord1[1])
    lat2, lon2 = radians(coord2[0]), radians(coord2[1])

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c
    return distance * 1000  # Convert to meters


def calculate_radius(coordinates):
    total_distance = 0
    # Calculate the total distance covered by the route
    for i in range(len(coordinates) - 1):
        total_distance += calculate_distance(coordinates[i], coordinates[i + 1])

    # Approximate the radius using the total distance
    radius = total_distance / (2 * pi)  # Divide by 2π to get an approximate radius
    return radius


def get_zoom_start(radius):
    scale = radius / 500
    zoomLevel = int((17 - log10(scale) / log10(2)))
    return zoomLevel


def calculate_center(coordinates):
    # Ensure coordinates are not empty
    if not coordinates:
        return None

    # Extract latitudes and longitudes into separate lists
    latitudes = [coord[0] for coord in coordinates]
    longitudes = [coord[1] for coord in coordinates]

    # Calculate average latitudes and longitudes
    avg_lat = sum(latitudes) / len(coordinates)
    avg_lon = sum(longitudes) / len(coordinates)

    return [avg_lat, avg_lon]


# if the token hasn't expire, will return the same token
def refresh_access_token(refresh_token):
    config = dotenv_values(".env")
    url = REFRESH_TOKEN_URL
    refresh_data = {
        "client_id": config.get("CLIENT_ID"),
        "client_secret": config.get("CLIENT_SECRET"),
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


def plot(polyline):
    coordinates = decode_polyline(polyline)
    radius = calculate_radius(coordinates)
    zoom_start = get_zoom_start(radius)
    center = calculate_center(coordinates)

    # Create a folium map centered at a location
    # tiles='https://{s}.tiles.example.com/{z}/{x}/{y}.png'
    m = folium.Map(location=center, zoom_start=zoom_start)

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

    img_data = m._to_png(0.3)
    img = Image.open(io.BytesIO(img_data))
    width, height = img.size
    # Calculate the top-left corner to extract the center
    size = min(width, height) * 0.9

    # Calculate the coordinates to crop the square
    left = (width - size) / 2
    top = (height - size) / 2
    right = (width + size) / 2
    bottom = (height + size) / 2

    # Cropped image of above dimension
    # (It will not change original image)
    cropped_image = img.crop((left, top, right, bottom))
    return image_to_byte_array(cropped_image)
