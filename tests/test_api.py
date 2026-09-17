from fastapi.testclient import TestClient

from app.main import app


def test_todo_lifecycle(tmp_path, monkeypatch):
    monkeypatch.setenv("TODO_DATABASE", str(tmp_path / "test.db"))
    with TestClient(app) as client:
        assert client.get("/api/todos").json() == []
        created = client.post("/api/todos", json={"title": "Ship the little list"})
        assert created.status_code == 201
        todo = created.json()
        assert todo["title"] == "Ship the little list"
        assert todo["completed"] is False
        assert client.patch(f"/api/todos/{todo['id']}", json={"completed": True}).json()["completed"] is True
        assert client.delete(f"/api/todos/{todo['id']}").status_code == 204


def test_rejects_blank_and_missing_todos(tmp_path, monkeypatch):
    monkeypatch.setenv("TODO_DATABASE", str(tmp_path / "test.db"))
    with TestClient(app) as client:
        assert client.post("/api/todos", json={"title": "   "}).status_code == 422
        assert client.patch("/api/todos/404", json={"completed": True}).status_code == 404
