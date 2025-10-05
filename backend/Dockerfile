# Use Python slim image
FROM python:3.11-slim

# Install system deps for OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg libsm6 libxext6 \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY backend /app

# Env
ENV PORT=5001 \
    PYTHONUNBUFFERED=1 \
    CORS_ORIGINS="*"

# Run with gunicorn in production (or override CMD to use Flask for dev)
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5001", "api_server:app"]
