import bisect
import requests


class BestEffortScanner:
    def __init__(self, access_token):
        self.access_token = access_token

    def find_closest_greater(self, sorted_array, target):
        index = bisect.bisect_right(sorted_array, target)
        return index if index < len(sorted_array) else -1

    def find_closest_greater(self, sorted_array, target):
        index = bisect.bisect_right(sorted_array, target)
        return index if index < len(sorted_array) else -1

    def find_best_nk(self, time, distance, n):
        index_of_nk = self.find_closest_greater(distance, n * 1000)
        if index_of_nk == -1:
            return -1, (-1, -1)

        best_nk_time = float("inf")
        best_nk_index = (0, 0)
        l = 0
        for r in range(index_of_nk, len(time)):
            # distance_diff = distance[r] - distance[l]
            time_diff = time[r] - time[l]
            if time_diff < best_nk_time:
                best_nk_time = time_diff
                best_nk_index = (l, r)
            l += 1

        return best_nk_time, best_nk_index

    def get_activity_streams_data(self, activity_id, series_type="distance"):
        url = f"https://www.strava.com/api/v3/activities/{activity_id}/streams?series_type={series_type}"

        headers = {"Authorization": f"Bearer {self.access_token}"}

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0 and "data" in data[0]:
                return data[0]["data"]
            else:
                print("No 'data' field found in the response.")
                return None
        else:
            print(f"Failed to retrieve data. Status code: {response.status_code}")
            return None
