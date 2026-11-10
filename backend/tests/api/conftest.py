from typing import TYPE_CHECKING

import pytest
from api_client import make_client

if TYPE_CHECKING:
    from fastapi.testclient import TestClient


@pytest.fixture
def client() -> TestClient:
    return make_client()
