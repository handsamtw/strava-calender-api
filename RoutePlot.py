import folium
from util import decode_polyline
import xyzservices.providers as xyz
from math import radians, sin, cos, sqrt, atan2, log2


class RoutePlot:
    def __init__(self):
        pass

    def calculate_center(self, coordinates):
        # Ensure coordinates are not empty
        if not coordinates:
            return None

        # Extract latitudes and longitudes into separate lists
        latitudes = [coord[0] for coord in coordinates]
        longitudes = [coord[1] for coord in coordinates]

        # Calculate average latitudes and longitudes
        avg_lat = sum(latitudes) / len(coordinates)
        avg_lon = sum(longitudes) / len(coordinates)

        return [avg_lat, avg_lon]

    def get_zoom_start(self, radius):
        scale = radius / 500
        zoomLevel = int((16 - log2(scale) / log2(2)))
        return zoomLevel

    def exec(self, polyline):
        def calculate_distance(coord1, coord2):
            # Calculate distance (in kilometers) between two coordinates using Haversine formula
            R = 6371.0  # Earth radius in kilometers

            lat1, lon1 = radians(coord1[0]), radians(coord1[1])
            lat2, lon2 = radians(coord2[0]), radians(coord2[1])

            dlon = lon2 - lon1
            dlat = lat2 - lat1

            a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
            c = 2 * atan2(sqrt(a), sqrt(1 - a))

            distance = R * c
            return distance * 1000  # Convert to meters

        def calculate_radius(coordinates):
            total_distance = 0
            # Calculate the total distance covered by the route
            for i in range(len(coordinates) - 1):
                total_distance += calculate_distance(coordinates[i], coordinates[i + 1])

            # Approximate the radius using the total distance
            radius = total_distance / (
                2 * 3.14159
            )  # Divide by 2π to get an approximate radius
            return radius

        coordinates = decode_polyline(polyline)
        radius = calculate_radius(coordinates)
        print(radius)
        zoom_start = self.get_zoom_start(radius)

        print(zoom_start)

        center = self.calculate_center(coordinates)

        # Create a folium map centered at a location
        # tiles='https://{s}.tiles.example.com/{z}/{x}/{y}.png'
        m = folium.Map(location=center, zoom_start=zoom_start + 1)

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
        m.save("map_with_polyline.html")
        # coordinates = [
        #     [37.7749, -122.4194],  # Example coordinate 1 (San Francisco, CA)
        #     [34.0522, -118.2437],  # Example coordinate 2 (Los Angeles, CA)
        #     [40.7128, -74.0060],  # Example coordinate 3 (New York City, NY)
        #     [41.8781, -87.6298],  # Example coordinate 4 (Chicago, IL)
        # ]

        # # Create a folium map with a specific tileset
        # m = folium.Map(
        #     location=[37.7749, -122.4194], zoom_start=4, tiles="Cartodb dark_matter"
        # )

        # # Add a polyline to the map
        # folium.PolyLine(locations=coordinates, color="blue").add_to(m)

        # # Save the map as an HTML file
        # m.save("simple_map_with_polyline.html")
