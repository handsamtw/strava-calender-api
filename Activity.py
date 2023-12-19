import bisect
import requests
from util import calculate_pace
from constants import ACTIVITIES_URL


class Activity:
    @classmethod
    def get_most_recent_activity_id(cls, access_token):
        url = f"{{ACTIVITIES_URL}}?per_page=1&page=1"
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

    @classmethod
    def parse_activity(cls, id, access_token):
        headers = {"Authorization": f"Bearer {access_token}"}
        url = f"{{ACTIVITIES_URL}}/{id}"
        response = requests.get(url, headers=headers)
        data = response.json()
        pace = calculate_pace(data["distance"], data["moving_time"])
        city, state = None, None
        if "segment_effort" in data:
            first_segment = data["segment_effort"][0]["segment"]
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
