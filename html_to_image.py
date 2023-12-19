from html2image import Html2Image
import time

hti = Html2Image()

hti.size = (700, 400)

# screenshot an HTML file
time.sleep(0.5)
hti.screenshot(
    html_file="map_with_polyline.html",
    # css_file="style.css",
    save_as="ap_with_polyline2.jpg",
)
