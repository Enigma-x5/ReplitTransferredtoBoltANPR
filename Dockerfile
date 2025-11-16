# ==============================
#  ANPR 2.0 - Backend Runtime
# ==============================

FROM python:3.11-slim AS base

WORKDIR /app

# --- System dependencies ---
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# --- Improve pip reliability ---
ENV PIP_DEFAULT_TIMEOUT=240 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

# --- Install Python dependencies ---
COPY requirements.txt .
RUN python -m pip install --upgrade pip setuptools wheel \
 && pip install --timeout 240 --retries 10 -r requirements.txt

# --- Copy source code ---
COPY . .

# --- Environment setup ---
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# --- Default CMD ---
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
