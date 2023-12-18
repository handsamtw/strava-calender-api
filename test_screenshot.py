from BestEffort import BestEffortScanner
from ScreenShotter import ScreenShooter

if __name__ == "__main__":
    screenShooter = ScreenShooter()

    screenShooter.take_sreenshot(
        "map_with_polyline.html",
        "img/map_with_polyline.png",
    )
