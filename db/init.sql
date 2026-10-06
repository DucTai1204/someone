SET NAMES utf8mb4;

CREATE DATABASE IF NOT EXISTS todo_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE todo_db;

CREATE TABLE IF NOT EXISTS todos (
  id INT AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(255) NOT NULL,
  done BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO todos (title, done) VALUES
  ('Chạy thử MySQL bằng docker compose', TRUE),
  ('Chạy backend FastAPI', FALSE),
  ('Chạy frontend React', FALSE);
