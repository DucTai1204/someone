import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  // Đọc biến từ frontend/.env (và .env.[mode]); biến môi trường hệ thống được ưu tiên hơn.
  const env = { ...loadEnv(mode, process.cwd(), ""), ...process.env };

  // Khi dev: /api được proxy sang backend chạy bằng `python main.py` (mặc định cổng 8001).
  // Cổng 8000 dành cho backend trong Docker.
  const apiTarget = env.API_TARGET || "http://127.0.0.1:8001";

  return {
    plugins: [react()],
    server: {
      port: 5173,
      proxy: {
        "/api": apiTarget,
      },
    },
  };
});
