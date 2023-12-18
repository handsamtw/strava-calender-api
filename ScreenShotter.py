from selenium import webdriver
import time
import os


class ScreenShooter:
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

        # Initialize Chrome driver
        # driver = webdriver.Chrome(executable_path=driver_path, options=chrome_options)
        driver = webdriver.Chrome()
        # the current window size
        window_size = driver.get_window_size()

        resize_ratio = 0.9
        new_height = int(window_size["height"] * resize_ratio)
        new_width = int(window_size["width"] * resize_ratio)
        driver.set_window_size(new_width, new_height)
        # Open the HTML file in Chrome
        driver.get(html_path)
        time.sleep(0.25)
        # Take a screenshot of the loaded HTML file
        driver.save_screenshot(export_path)

        # Close the browser
        driver.quit()
