# Frontend là HTML/CSS/JS thuần: không cần Node, nginx phục vụ trực tiếp, proxy /api sang backend
FROM nginx:1.27-alpine
# Image nginx tự thay ${BACKEND_URL} trong file template lúc khởi động.
COPY nginx.conf /etc/nginx/templates/default.conf.template
ENV BACKEND_URL=http://backend:8000
COPY index.html style.css app.js /usr/share/nginx/html/
EXPOSE 80
