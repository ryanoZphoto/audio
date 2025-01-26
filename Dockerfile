# Stage 1: Unified Build Environment
FROM python:3.10-slim-bookworm AS builder

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    make \
    cmake \
    libssl-dev \
    libgomp1 \
    libopenblas-dev \
    curl \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install Modern Rust
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y \
    --default-toolchain stable
ENV PATH="/root/.cargo/bin:${PATH}"

# Build-Specific Environment
ENV CARGO_NET_GIT_FETCH_WITH_CLI=true \
    RUSTFLAGS="-C target-cpu=native" \
    OPENSSL_DIR=/usr/lib/ssl

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel
RUN pip install --user -r requirements.txt \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    --no-cache-dir \
    --use-deprecated=legacy-resolver \
    --no-build-isolation

# Stage 2: Optimized Runtime
FROM python:3.10-slim-bookworm
COPY --from=builder /root/.local /root/.local

# Create app directory and set permissions
RUN mkdir -p /app/static /app/static/img
WORKDIR /app

# Copy application files
COPY . .

# Ensure proper permissions
RUN chown -R root:root /app && \
    chmod -R 755 /app/static

# Runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    libopenblas0 \
    ffmpeg \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Final configuration
ENV PATH="/root/.local/bin:${PATH}" \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=wsgi.py \
    FLASK_ENV=production \
    PORT=8000

EXPOSE 8000
CMD ["gunicorn", "wsgi:application", "--config", "gunicorn.conf.py"]
