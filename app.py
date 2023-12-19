from flask import Flask, Response, send_file
import io
from PIL import Image
from ImageProcessor import ImageProcessor

app = Flask(__name__)


# def generate_image():
#     # Create a PIL Image object (replace this with your image generation logic)
#     width, height = 300, 200
#     image = Image.new("RGB", (width, height), "white")

#     # Save the image to a byte array
#     image_byte_array = io.BytesIO()
#     image.save(image_byte_array, format="PNG")

#     return image_byte_array.getvalue()


@app.route("/get_image")
def get_image():
    imageProcessor = ImageProcessor()
    image_data = imageProcessor.retrieve_image("6580ed702bd7702cdf4cc9b5")
    return Response(image_data, mimetype="image/png")


if __name__ == "__main__":
    app.run(debug=True)
