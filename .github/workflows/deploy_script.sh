#!/bin/bash

set -e

echo "Starting deployment..."

# Create backup of current deployment if exists
if [ -d "/data/miaoxiang_web/backup" ]; then
    rm -rf /data/miaoxiang_web/backup
fi

if [ -d "/data/miaoxiang_web" ]; then
    mv /data/miaoxiang_web /data/miaoxiang_web/backup
fi

# Create new deployment directory
mkdir -p /data/miaoxiang_web

# Move new files from temp to deployment directory
mv /tmp/miaoxiang_deploy/frontend /data/miaoxiang_web/
mv /tmp/miaoxiang_deploy/backend /data/miaoxiang_web/

# Setup Python virtual environment
cd /data/miaoxiang_web/backend
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

deactivate

# Cleanup temp files
rm -rf /tmp/miaoxiang_deploy

# Kill any existing process on port 8001
echo "Stopping existing backend process..."
pkill -f "uvicorn.*:8001" || true
sleep 2

# Start the backend service
echo "Starting backend service on port 8001..."
cd /data/miaoxiang_web/backend
source venv/bin/activate
nohup uvicorn app.main:app --host 0.0.0.0 --port 8001 --forwarded-allow-ips='*' > /data/miaoxiang_web/backend.log 2>&1 &
deactivate

echo "Backend started with PID: $!"

# Verify backend is running
sleep 3
if curl -s http://localhost:8001 > /dev/null 2>&1; then
    echo "Backend is running successfully on port 8001"
else
    echo "Warning: Backend may not be responding yet. Check logs at /data/miaoxiang_web/backend.log"
fi

echo "Deployment completed successfully!"
