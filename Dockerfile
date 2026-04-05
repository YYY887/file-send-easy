FROM node:22-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm config set fetch-retries 5 \
 && npm config set fetch-retry-mintimeout 2000 \
 && npm config set fetch-retry-maxtimeout 15000 \
 && npm ci --registry=https://registry.npmjs.org
COPY frontend ./
RUN npm run build

FROM python:3.12-slim AS backend
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PIP_REQUIRE_HASHES=0
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
 && pip install --no-cache-dir \
    --trusted-host pypi.org \
    --trusted-host files.pythonhosted.org \
    --trusted-host pypi.python.org \
    -r requirements.txt
COPY backend ./backend
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist
RUN mkdir -p /app/data/storage
WORKDIR /app/backend
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health')"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
