#!/bin/bash
set -e

echo "=== Starting Application ==="

# Get port from environment variable or use default
PORT="${PORT:-8000}"
echo "Using port: $PORT"

# Wait for database to be ready
echo "Waiting for database..."
python << END
import sys
import time
import psycopg2
import os

db_url = os.getenv('DATABASE_URL')
if not db_url:
    print("DATABASE_URL environment variable not set!")
    sys.exit(1)

max_retries = 30
retry_interval = 10
current_attempt = 0

while current_attempt < max_retries:
    try:
        print(f"Attempting database connection ({current_attempt + 1}/{max_retries})...")
        conn = psycopg2.connect(db_url)
        conn.close()
        print("Successfully connected to database!")
        sys.exit(0)
    except psycopg2.OperationalError as e:
        print(f"Database connection failed: {str(e)}")
        current_attempt += 1
        if current_attempt < max_retries:
            print(f"Retrying in {retry_interval} seconds...")
            time.sleep(retry_interval)
        else:
            print("Max retries reached. Could not connect to database.")
            sys.exit(1)
END

# Initialize database
echo "Initializing database..."
python init_db.py || {
    echo "Database initialization failed!"
    exit 1
}

# Start Gunicorn
echo "Starting Gunicorn on port $PORT..."
exec gunicorn wsgi:app \
    --config gunicorn.conf.py \
    --log-level debug \
    --capture-output \
    --enable-stdio-inheritance \
    --timeout 300 \
    --workers 2 \
    --preload \
    --worker-class sync \
    --bind "0.0.0.0:$PORT"
