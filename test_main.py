from unittest import mock

from fastapi.testclient import TestClient
from starlette import status


class TestMain:
    def setup_method(self):
        with mock.patch.dict("os.environ", {"WEB3_INFURA_PROJECT_ID": "1"}):
            from main import app
        self.client = TestClient(app)

    def test_index(self):
        """Index should be redirecting to the documentation."""
        response = self.client.get("/")
        assert response.status_code == status.HTTP_200_OK
        assert response.url == "http://testserver/redoc"
        assert "FastAPI - ReDoc" in response.text
