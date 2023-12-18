from RecentActivity import RecentActivity
from util import human_readable_time, calculate_pace, get_city_state_from_coordinates
import requests
from dotenv import dotenv_values

if __name__ == "__main__":
    # Load variables from .env file into a dictionary
    config = dotenv_values(".env")

    # Access environment variables
    access_token = config.get("ACCESS_TOKEN")
    print("access_token: ", access_token)
    if not access_token:
        pass
    recent_activity_worker = RecentActivity(access_token=access_token)

    data = recent_activity_worker.get_most_recent_activity()
    pace = calculate_pace(data["distance"], data["moving_time"])
    city, state = get_city_state_from_coordinates(
        data["start_latlng"][0], data["start_latlng"][1]
    )

    print(f"--- Most recent activity ---")

    if city and state:
        print(f"{city}, {state}.")
    else:
        print("City and state not found.")

    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(
        f"https://www.strava.com/api/v3/activities/{data['id']}", headers=headers
    )
    description = response.json()["description"]

    print(
        f"{data['name']}\n距離: {data['distance']/1000} km \n配速: {pace} \n時間: {human_readable_time(data['moving_time'])} \nDescription: {description}"
    )
