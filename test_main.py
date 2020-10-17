from unittest import mock

from fastapi.testclient import TestClient
from starlette import status


class TestMain:
    def setup_method(self):
        with mock.patch.dict("os.environ", {"WEB3_INFURA_PROJECT_ID": "1"}):
            from main import app
        self.app = app
        self.client = TestClient(app)

    def test_urls(self):
        """Checks URL patterns."""
        assert self.app.url_path_for("index") == "/"
        address = "0x0000000000000000000000000000000000000000"
        path_params = {"address": address}
        assert (
            self.app.url_path_for("portfolio", **path_params)
            == "/portfolio/0x0000000000000000000000000000000000000000"
        )

    def test_index(self):
        """Index should be redirecting to the documentation."""
        url = self.app.url_path_for("index")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.url == "http://testserver/redoc"
        assert "FastAPI - ReDoc" in response.text
