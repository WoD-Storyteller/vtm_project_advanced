#!/bin/bash
set -e

# Deployment script to be called via SSH (from GitHub Actions or manually)
echo "=== VTM Bot Deploy Script ==="
cd /opt/vtm_bot/bot

echo "Pulling latest code from GitHub..."
git pull

echo "Activating virtual environment..."
source venv/bin/activate

if [ -f "requirements.txt" ]; then
  echo "Installing/updating Python dependencies from requirements.txt..."
  pip install -r requirements.txt
fi

deactivate

echo "Restarting vtm.service..."
# NOTE: This requires that the SSH user has passwordless sudo for systemctl restart vtm.service
sudo systemctl restart vtm.service

echo "Deployment complete."
