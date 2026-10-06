import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import { fileURLToPath } from "node:url";

// Dùng chung file .env ở thư mục root với backend.
const envDir = fileURLToPath(new URL("..", import.meta.url));

export default defineConfig(({ mode }) => {
  // Đọc biến từ .env (và .env.[mode]); biến môi trường hệ thống được ưu tiên hơn.
  const env = { ...loadEnv(mode, envDir, ""), ...process.env };

  // Khi dev: /api được proxy sang backend chạy bằng `python main.py` (mặc định cổng 8001).
  // Cổng 8000 dành cho backend trong Docker.
  const apiTarget = env.API_TARGET || "http://127.0.0.1:8001";

  return {
    envDir,
    plugins: [react()],
    server: {
      port: 5173,
      proxy: {
        "/api": apiTarget,
      },
    },
  };
});
