#!/bin/bash
set -e

echo "=== Starting Application ==="

# Get port from environment variable or use default
PS C:\audio> railway up
  Indexed                                                                                             
  Compressed [====================] 100%                                                              
  Uploaded                                                                                            
  Build Logs: https://railway.com/project/9f5c3db6-9846-4b8b-8b3c-81d40442a847/service/21b2e088-2a83-4d6c-a40e-fa641062f0a8?id=9617d4a1-1b1e-4907-a6d2-705a1c228235&

[Region: us-west1]
=========================
Using Detected Dockerfile
=========================

context: 56c279ef37fbbeb03f06f0d83e3145a2
Deploy failed
PS C:\audio> 
PORT="${PORT:-5000}"
echo "Using port: $PORT"

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
