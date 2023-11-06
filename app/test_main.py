from app.main import app
import pytest
from fastapi.testclient import TestClient
@pytest.fixture
def client():
    client = TestClient(app, "http://0.0.0.0:3000")
    yield client
class TestServerAPI():
    def test_get_me(self):
        assert 1 == 1