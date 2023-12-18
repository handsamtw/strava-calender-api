from html2image import Html2Image

hti = Html2Image()

hti.size = (700, 400)

# screenshot an HTML file
hti.screenshot(
    html_file="map_with_polyline.html",
    # css_file="style.css",
    save_as="map_with_polyline.jpg",
)
