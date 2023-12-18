import folium
from util import decode_polyline, calculate_radius, get_zoom_start, calculate_center
import xyzservices.providers as xyz
from math import log10


class RoutePlot:
    def __init__(self):
        pass

    def plot(self, polyline, saved_file_name="map_with_polyline.html"):
        coordinates = decode_polyline(polyline)
        radius = calculate_radius(coordinates)

        zoom_start = get_zoom_start(radius)
        print("radius: ", radius, "zoom_start: ", zoom_start)

        center = calculate_center(coordinates)

        # Create a folium map centered at a location
        # tiles='https://{s}.tiles.example.com/{z}/{x}/{y}.png'
        m = folium.Map(location=center, zoom_start=zoom_start)

        # folium.TileLayer(
        #     tiles=xyz.CartoDB.Positron.url, attr=xyz.CartoDB.Positron.attribution
        # ).add_to(m)
        folium.TileLayer(tiles="CartoDB positron").add_to(m)

        # Add a polyline to the map
        folium.PolyLine(
            locations=coordinates,
            color="orange",
            line_cap="round",
        ).add_to(m)

        # Save the map as an HTML file
        m.save(saved_file_name)
