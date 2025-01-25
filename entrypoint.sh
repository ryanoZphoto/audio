#!/bin/bash
set -e

echo "=== Starting Application ==="

# Wait for database to be ready
echo "Waiting for database..."
python << END
import sys
import time
import psycopg2
from app.utils.config_utils import get_secret

db_url = get_secret('DATABASE_URL')
max_retries = 30
retry_interval = 10

for i in range(max_retries):
    try:
        conn = psycopg2.connect(db_url)
        conn.close()
        print("Database is ready!")
        sys.exit(0)
    except psycopg2.OperationalError as e:
        print(f"Database not ready (attempt {i+1}/{max_retries}). Retrying in {retry_interval}s...")
        time.sleep(retry_interval)

print("Could not connect to database")
sys.exit(1)
END

# Initialize database
echo "Initializing database..."
python init_db.py

# Start Gunicorn
echo "Starting Gunicorn..."
exec gunicorn wsgi:app \
    --config gunicorn.conf.py \
    --log-level debug \
    --capture-output \
    --enable-stdio-inheritance \
    --timeout 120 \
    --workers 2 \
    --preload \
    --worker-class sync
