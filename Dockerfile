# ── Stage 1: Build the React Frontend ──
FROM node:20-slim AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
# Set the backend URL for the production build if needed
# ENV VITE_API_URL=https://your-backend-url.com
RUN npm run build

# Setup the Python Backend
FROM python:3.12-slim
WORKDIR /app

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install system dependencies (needed for some python packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*


# Copy python dependency files
COPY pyproject.toml .
# Install dependencies
RUN uv pip install --system -r pyproject.toml

# Copy the backend code
COPY api/ ./api/
COPY agent/ ./agent/
COPY config.py .

# Create the WorkingDirectory
RUN mkdir -p WorkingDirectory

# Copy the built frontend from Stage 1
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Expose the port FastAPI runs on
EXPOSE 8000

# Start the application
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
