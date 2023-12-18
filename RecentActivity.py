import bisect
import requests


class RecentActivity:
    def __init__(self, access_token):
        self.access_token = access_token

    def get_most_recent_activity(self):
        url = "https://www.strava.com/api/v3/activities?per_page=1&page=1"
        headers = {"Authorization": f"Bearer {self.access_token}"}

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                return data[0]

            else:
                print(f"Check response type")
                return None
        else:
            print(f"Failed to retrieve data. Status code: {response.status_code}")
            return None
