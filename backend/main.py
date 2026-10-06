import os
import time
from datetime import datetime
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Boolean, Column, DateTime, Integer, String, create_engine, func
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, declarative_base, sessionmaker

# Dùng chung file .env ở thư mục root với frontend.
# Không ghi đè biến đã có sẵn (vd. biến do docker-compose truyền vào).
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"))

DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "123456")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "todo_db")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class Todo(Base):
    __tablename__ = "todos"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    done = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())


class TodoCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)


class TodoUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    done: Optional[bool] = None


class TodoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    done: bool
    created_at: datetime


def init_db(retries: int = 30, delay: float = 2.0) -> None:
    """Chờ MySQL sẵn sàng rồi tạo bảng (nếu chưa có)."""
    for attempt in range(1, retries + 1):
        try:
            Base.metadata.create_all(bind=engine)
            print("Đã kết nối MySQL.")
            return
        except OperationalError as exc:
            print(f"[{attempt}/{retries}] Chưa kết nối được MySQL: {exc.orig}")
            time.sleep(delay)
    raise RuntimeError("Không kết nối được MySQL, kiểm tra docker compose / biến môi trường.")


init_db()

app = FastAPI(title="Todo API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/todos", response_model=List[TodoOut])
def list_todos(db: Session = Depends(get_db)):
    return db.query(Todo).order_by(Todo.id.desc()).all()


@app.post("/api/todos", response_model=TodoOut, status_code=201)
def create_todo(payload: TodoCreate, db: Session = Depends(get_db)):
    todo = Todo(title=payload.title.strip(), done=False)
    db.add(todo)
    db.commit()
    db.refresh(todo)
    return todo


@app.patch("/api/todos/{todo_id}", response_model=TodoOut)
def update_todo(todo_id: int, payload: TodoUpdate, db: Session = Depends(get_db)):
    todo = db.get(Todo, todo_id)
    if todo is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy todo")
    if payload.title is not None:
        todo.title = payload.title.strip()
    if payload.done is not None:
        todo.done = payload.done
    db.commit()
    db.refresh(todo)
    return todo


@app.delete("/api/todos/{todo_id}", status_code=204)
def delete_todo(todo_id: int, db: Session = Depends(get_db)):
    todo = db.get(Todo, todo_id)
    if todo is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy todo")
    db.delete(todo)
    db.commit()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=int(os.getenv("PORT", "8001")), reload=True)
