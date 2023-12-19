from selenium import webdriver
import time
import os


class ScreenShotter:
    def __init__(self):
        pass

    def take_sreenshot(self, html_file_name, export_image_name):
        # Path to your HTML file

        html_path = f"file://{os.path.join(os.getcwd(), html_file_name)}"
        # export_path = os.path.join(os.getcwd(), export_image_name)
        export_path = export_image_name
        print(html_path, export_path)
        # Path to your ChromeDriver executable (download and specify the correct path)

        # Configure Chrome options
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument(
            "--headless"
        )  # Run Chrome in headless mode (without opening a window)

        chrome_options.add_argument(
            "--disable-gpu"
        )  # Disable GPU acceleration, which is recommended in headless mode

        # Initialize Chrome driver
        driver = webdriver.Chrome(options=chrome_options)

        driver.get(html_path)
        time.sleep(0.25)
        # the current window size
        window_size = driver.get_window_size()
        resize_ratio = 0.9

        # Calculate the dimensions for an 80% square from the center
        min_side = int(
            min(window_size["width"], window_size["height"]) * resize_ratio
        )  # 80% of the minimum side length
        x = int(
            (window_size["width"] - min_side) / 2
        )  # X coordinate for the left edge of the square
        y = int(
            (window_size["height"] - min_side) / 2
        )  # Y coordinate for the top edge of the square

        # Set the window size to capture the desired square area
        driver.set_window_size(min_side, min_side)

        # Scroll to the calculated coordinates (optional)
        driver.execute_script(f"window.scrollTo({x}, {y});")

        # Take a screenshot of the loaded HTML file
        driver.save_screenshot(export_path)

        # Close the browser
        driver.quit()
