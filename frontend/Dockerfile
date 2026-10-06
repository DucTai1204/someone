# Build React app
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

# Serve bằng nginx, proxy /api sang backend
FROM nginx:1.27-alpine
# Image nginx tự thay ${BACKEND_URL} trong file template lúc khởi động.
COPY nginx.conf /etc/nginx/templates/default.conf.template
ENV BACKEND_URL=http://backend:8000
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
