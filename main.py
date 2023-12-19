from RecentActivity import RecentActivity
from RoutePlot import RoutePlot
from ScreenShotter import ScreenShotter
from ImageProcessor import ImageProcessor
from dotenv import dotenv_values

if __name__ == "__main__":
    config = dotenv_values(".env")

    # Access environment variables
    access_token = config.get("ACCESS_TOKEN")
    refresh_token = config.get("REFRESH_TOKEN")
    # TODO: check whether shot-live access token is about to expire
    if not access_token:
        pass
    recent_activity_worker = RecentActivity(access_token=access_token)
    recent_activity_id = recent_activity_worker.get_most_recent_activity_id()

    activity_detail = recent_activity_worker.parse_activity(recent_activity_id)
    # print("Finished parsing activity detail")
    if activity_detail["polyline"]:
        routePlot = RoutePlot()
        routePlot.plot(polyline=activity_detail["polyline"])
        # print("Finish plotting route")
        screenShotter = ScreenShotter()
        screenShotter.take_sreenshot(
            html_file_name="map_with_polyline.html",
            export_image_name="img/map_with_polyline.png",
        )
        # print("FInish taking screenshot")

    imageProcessor = ImageProcessor()
    image_id = imageProcessor.save_img("img/map_with_polyline.png")
    imageProcessor.save_credential(access_token, refresh_token, image_id)
    imageProcessor.retrieve_image(image_id)
