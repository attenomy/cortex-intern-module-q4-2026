import os
import sys
import pytest
from fastapi.testclient import TestClient

# Ensure API directory is accessible in sys.path
API_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if API_DIR not in sys.path:
    sys.path.insert(0, API_DIR)

from main import app

@pytest.fixture
def client():
    return TestClient(app)

