# backend/Dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Install system dependencies if needed by your VLM code (e.g., for OpenCV)
# RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ./VLM ./VLM
COPY ./app ./app

# Expose the port Gunicorn will listen on (must match CMD)
EXPOSE 8000

# Use Gunicorn to run Uvicorn workers
# Adjust '-w 4' (workers) based on expected load and container resources. Start with 2 or 4.
# Ensure app.main:app points to your FastAPI instance
CMD ["gunicorn", "-w", "2", "-k", "uvicorn.workers.UvicornWorker", "app.main:app", "--bind", "0.0.0.0:8000"]