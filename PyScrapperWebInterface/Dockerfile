# --- build: compile the Vite app into static files ---------------------------
FROM node:22-alpine AS build
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund

COPY . .
RUN npm run build

# --- runtime: nginx serves the build and proxies the API to the LocalServer ---
FROM nginx:1.27-alpine

# The official image runs envsubst over /etc/nginx/templates/*.template at start,
# so BACKEND_URL can be set per container without rebuilding.
ENV BACKEND_URL=http://host.docker.internal:8765
COPY docker/default.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
