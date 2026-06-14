import os

os.environ["DATABASE_URL"] = "sqlite:///./test_gradeops.db"
os.environ["USE_MOCK_AI"] = "true"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.auth import seed_demo_users
from app.database import Base, engine, get_db
from app.main import app

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    seed_demo_users(db)
    db.close()
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def auth_header(client, email, password):
    res = client.post("/api/auth/login", data={"username": email, "password": password})
    assert res.status_code == 200, res.text
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_health(client):
    assert client.get("/api/health").json()["status"] == "ok"


def test_demo_flow(client):
    h = auth_header(client, "instructor@gradeops.edu", "instructor123")
    demo = client.post("/api/exams/demo", headers=h)
    assert demo.status_code == 200
    assert demo.json()["exam_id"] > 0

    ta_h = auth_header(client, "ta@gradeops.edu", "ta123456")
    queue = client.get("/api/review/queue", headers=ta_h)
    assert queue.status_code == 200
    items = queue.json()
    assert len(items) > 0

    grade_id = items[0]["grade_id"]
    approve = client.post(
        f"/api/review/{grade_id}/action",
        headers=ta_h,
        json={"action": "approve"},
    )
    assert approve.status_code == 200
    assert approve.json()["status"] == "approved"


def test_plagiarism_detected(client):
    h = auth_header(client, "instructor@gradeops.edu", "instructor123")
    client.post("/api/exams/demo", headers=h)
    ta_h = auth_header(client, "ta@gradeops.edu", "ta123456")
    stats = client.get("/api/review/stats", headers=ta_h).json()
    assert stats["plagiarism_flags"] >= 1
