import os
import time
from datetime import datetime
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Boolean, Column, DateTime, Integer, String, create_engine, func, text
from sqlalchemy.engine import URL
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, declarative_base, sessionmaker

# Đọc backend/.env khi chạy `python main.py`.
# Không ghi đè biến đã có sẵn (vd. biến do docker-compose truyền vào qua env_file).
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

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
    # Kết nối vào server (chưa chọn database) để tạo DB_NAME nếu chưa có, vd. RDS mới tạo.
    # (url.set(database=None) không xoá được database, nên dựng lại URL không có database.)
    u = engine.url
    server_url = URL.create(
        drivername=u.drivername, username=u.username, password=u.password,
        host=u.host, port=u.port, query=u.query,
    )
    server_engine = create_engine(server_url, pool_pre_ping=True)
    for attempt in range(1, retries + 1):
        try:
            with server_engine.connect() as conn:
                conn.execute(text(
                    f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` "
                    "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                ))
            Base.metadata.create_all(bind=engine)
            print("Đã kết nối MySQL.")
            seed_data()
            return
        except OperationalError as exc:
            print(f"[{attempt}/{retries}] Chưa kết nối được MySQL: {exc.orig}")
            time.sleep(delay)
    raise RuntimeError("Không kết nối được MySQL, kiểm tra docker compose / biến môi trường.")


# Dữ liệu mẫu, chỉ thêm khi bảng todos đang trống (lần đầu tạo CSDL).
SEED_TODOS = [
    ("Đẩy image frontend, backend lên Amazon ECR", True),
    ("Tạo ALB và ECS service trên Fargate", True),
    ("Kết nối backend với RDS MySQL", False),
]


def seed_data() -> None:
    db = SessionLocal()
    try:
        if db.query(Todo).count() > 0:
            return
        db.add_all([Todo(title=title, done=done) for title, done in SEED_TODOS])
        db.commit()
        print(f"Đã thêm {len(SEED_TODOS)} dòng dữ liệu mẫu.")
    finally:
        db.close()


init_db()

app = FastAPI(title="Todo API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        # VS Code Live Server
        "http://localhost:5500",
        "http://127.0.0.1:5500",
    ],
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

    uvicorn.run("main:app", host="127.0.0.1", port=int(os.getenv("PORT", "8000")), reload=True)