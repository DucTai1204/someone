"""Test nhanh cho CodeBuild: không cần MySQL, chỉ kiểm tra app khởi tạo được và /api/health trả 200."""
import os
import sys

os.environ["SKIP_DB_INIT"] = "1"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient  # noqa: E402

import main  # noqa: E402

client = TestClient(main.app)


def test_health_ok():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_create_todo_validation():
    # title rỗng bị Pydantic chặn trước khi chạm DB -> 422
    res = client.post("/api/todos", json={"title": ""})
    assert res.status_code == 422