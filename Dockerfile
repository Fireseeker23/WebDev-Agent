
FROM node:20-slim AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build


FROM python:3.12-slim
WORKDIR /app


COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv


RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*



COPY pyproject.toml .

RUN uv pip install --system -r pyproject.toml


COPY api/ ./api/
COPY agent/ ./agent/
COPY config.py .

RUN mkdir -p WorkingDirectory


COPY --from=frontend-builder /app/frontend/dist ./frontend/dist


EXPOSE 8000


CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
