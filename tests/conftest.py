import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["DATABASE_URL"] = f"sqlite:///{ROOT}/test-interviewlens.db"
os.environ.pop("GEMINI_API_KEY", None)

from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def clean_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def session_id(client):
    response = client.post("/api/sessions", json={
        "role": "Backend Developer",
        "level": "Entry level",
        "interview_type": "mixed",
        "job_description": "Python FastAPI SQL PostgreSQL Docker",
        "question_count": 5,
    })
    assert response.status_code == 201
    return response.json()["id"]
