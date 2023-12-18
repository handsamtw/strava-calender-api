import requests


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


def get_city_state_from_coordinates(latitude, longitude):
    # Initialize Nominatim geocoder
    # geolocator = Nominatim(user_agent="geoapiExercises")

    # # Reverse geocoding to get address details
    # location = geolocator.reverse((latitude, longitude), exactly_one=True)
    url = f"https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat={latitude}&lon={longitude}&zoom=13&addressdetails=1"
    response = requests.get(url)

    if response.status_code == 200:
        location = response.json()
        if "address" in location:
            address = location["address"]
            return address["city"], address["state"]
        else:
            print("No 'address' field found in the response.")
            return None, None
    else:
        print(f"Failed to retrieve data. Status code: {response.status_code}")
        return None, None
