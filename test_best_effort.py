from BestEffort import BestEffortScanner
from util import human_readable_time
from dotenv import dotenv_values

if __name__ == "__main__":
    config = dotenv_values(".env")
    # Access environment variables
    access_token = config.get("ACCESS_TOKEN")

    best_effortScanner = BestEffortScanner(access_token=access_token)
    activity_id = 6658720673
    time = best_effortScanner.get_activity_streams_data(activity_id, series_type="time")
    distance = best_effortScanner.get_activity_streams_data(
        activity_id, series_type="distance"
    )

    best_1k_time, best_1k_index = best_effortScanner.find_best_nk(time, distance, 1)
    best_5k_time, best_5k_index = best_effortScanner.find_best_nk(time, distance, 5)

    best_1k_start, best_1k_end = human_readable_time(
        time[best_1k_index[0]]
    ), human_readable_time(time[best_1k_index[1]])
    best_5k_start, best_5k_end = human_readable_time(
        time[best_5k_index[0]]
    ), human_readable_time(time[best_5k_index[1]])

    print(
        f"Best 1k time is {human_readable_time(best_1k_time)}, start from {best_1k_start} to {best_1k_end}"
    )

    print(
        f"Best 5k time is {human_readable_time(best_5k_time)}, start from {best_5k_start} to {best_5k_end}"
    )
