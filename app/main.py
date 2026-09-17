"""FastAPI application and JSON API for Little List."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, field_validator

from app.database import connection, initialise_database

ROOT = Path(__file__).parent


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialise_database()
    yield


app = FastAPI(title="Little List", version="1.0.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
templates = Jinja2Templates(directory=ROOT / "templates")


class TodoCreate(BaseModel):
    title: Annotated[str, Field(min_length=1, max_length=160)]

    @field_validator("title")
    @classmethod
    def strip_title(cls, title: str) -> str:
        title = title.strip()
        if not title:
            raise ValueError("A task needs a title")
        return title


class TodoUpdate(BaseModel):
    completed: bool


class Todo(BaseModel):
    id: int
    title: str
    completed: bool
    created_at: str


def as_todo(row: object) -> Todo:
    record = dict(row)  # sqlite.Row
    record["completed"] = bool(record["completed"])
    return Todo(**record)


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.get("/api/todos", response_model=list[Todo])
def list_todos() -> list[Todo]:
    with connection() as conn:
        rows = conn.execute(
            "SELECT id, title, completed, created_at FROM todos ORDER BY completed, id DESC"
        ).fetchall()
    return [as_todo(row) for row in rows]


@app.post("/api/todos", response_model=Todo, status_code=status.HTTP_201_CREATED)
def create_todo(payload: TodoCreate) -> Todo:
    with connection() as conn:
        cursor = conn.execute(
            "INSERT INTO todos (title) VALUES (?)", (payload.title,)
        )
        row = conn.execute(
            "SELECT id, title, completed, created_at FROM todos WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
    return as_todo(row)


@app.patch("/api/todos/{todo_id}", response_model=Todo)
def update_todo(todo_id: int, payload: TodoUpdate) -> Todo:
    with connection() as conn:
        cursor = conn.execute(
            "UPDATE todos SET completed = ? WHERE id = ?", (int(payload.completed), todo_id)
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Todo not found")
        row = conn.execute(
            "SELECT id, title, completed, created_at FROM todos WHERE id = ?", (todo_id,)
        ).fetchone()
    return as_todo(row)


@app.delete("/api/todos/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(todo_id: int) -> Response:
    with connection() as conn:
        cursor = conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Todo not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.delete("/api/todos", status_code=status.HTTP_204_NO_CONTENT)
def clear_completed() -> Response:
    with connection() as conn:
        conn.execute("DELETE FROM todos WHERE completed = 1")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
