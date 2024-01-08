# from ..api.index import app  # Importing the app instance from api.index
import pytest
import sys
import os

# Add project_root to the sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


# append the path of the
# parent directory
# sys.path.append("..")
from api.index import app


@pytest.fixture
def client():
    with app.test_client() as client:
        yield client


def test_index(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Hello, World!" in response.data
