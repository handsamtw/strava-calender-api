import bisect
import requests
from util import calculate_pace, get_city_state_from_coordinates


class RecentActivity:
    def __init__(self, access_token):
        self.access_token = access_token

    def get_most_recent_activity_id(self):
        url = "https://www.strava.com/api/v3/activities?per_page=1&page=1"
        headers = {"Authorization": f"Bearer {self.access_token}"}

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

    def parse_activity(self, id):
        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = requests.get(
            f"https://www.strava.com/api/v3/activities/{id}", headers=headers
        )
        data = response.json()
        pace = calculate_pace(data["distance"], data["moving_time"])
        city, state = None, None
        if "segment_effort" in data:
            first_segment = data["segment_effort"][0]["segment"]
            city, state = first_segment["city"], first_segment["state"]

        # city, state = get_city_state_from_coordinates(
        #     data["start_latlng"][0], data["start_latlng"][1]
        # )

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
