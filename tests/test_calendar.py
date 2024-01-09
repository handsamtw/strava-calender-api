import sys
import os

# Add project_root to the sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from api.index import app


class TestApp:
    """Test cases for the Flask app."""

    def setup_method(self):
        """Setup method executed before each test method."""
        self.client = app.test_client()

    def teardown_method(self):
        """Teardown method executed after each test method."""

    def test_no_uid(self):
        """Test case for handling the absence of user id."""
        response = self.client.get("/calendar")
        assert response.status_code == 404
        assert b"User id not found" in response.data

    def test_invalid_uid(self):
        """Test case for handling an invalid user id."""
        invalid_uid = os.urandom(13).hex()

        url = f"/calendar?uid={invalid_uid}"
        response = self.client.get(url)
        assert response.status_code == 400
        assert b"Invalid user id" in response.data
