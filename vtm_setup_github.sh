#!/bin/bash
set -e

echo "==============================================="
echo "   GCP Setup Script – VTM Bot (GitHub + SSH)"
echo "==============================================="

# Update system
sudo apt update -y
sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3 python3-pip python3-venv git screen tmux unzip curl wget ufw

echo "==============================================="
echo "Creating bot base folder at /opt/vtm_bot..."
echo "==============================================="
sudo mkdir -p /opt/vtm_bot
sudo chmod 777 /opt/vtm_bot

cd /opt/vtm_bot

# Clone repo if not already present
if [ ! -d "bot" ]; then
  echo "Cloning GitHub repository WoD-Storyteller/vtm_project_advanced into /opt/vtm_bot/bot ..."
  git clone https://github.com/WoD-Storyteller/vtm_project_advanced.git bot
else
  echo "/opt/vtm_bot/bot already exists, skipping clone."
fi

cd /opt/vtm_bot/bot

echo "==============================================="
echo "Creating Python virtual environment..."
echo "==============================================="
python3 -m venv venv

# Activate venv
source venv/bin/activate

echo "Upgrading pip inside venv..."
pip install --upgrade pip

echo "Installing dependencies..."
if [ -f "requirements.txt" ]; then
  pip install -r requirements.txt
else
  pip install discord.py google-generativeai python-dotenv aiohttp requests
fi

deactivate

echo "==============================================="
echo "Creating .env file for VTM Bot keys"
echo "==============================================="
read -p "Enter your Discord Bot Token: " DISCORD_TOKEN
read -p "Enter your Gemini API Key: " GEMINI_API_KEY
read -p "Enter your Discord Owner/User ID: " OWNER_ID

sudo tee /opt/vtm_bot/bot/.env >/dev/null << EOF
DISCORD_TOKEN="$DISCORD_TOKEN"
GEMINI_API_KEY="$GEMINI_API_KEY"
OWNER_ID="$OWNER_ID"
EOF

sudo chmod 600 /opt/vtm_bot/bot/.env

echo "==============================================="
echo "Installing systemd service vtm.service"
echo "==============================================="
# Copy service file from repo into systemd
if [ -f "vtm.service" ]; then
  sudo cp vtm.service /etc/systemd/system/vtm.service
  sudo systemctl daemon-reload
  sudo systemctl enable vtm.service
  sudo systemctl restart vtm.service || true
  echo "vtm.service installed and (re)started."
else
  echo "WARNING: vtm.service not found in repo root; please copy it manually to /etc/systemd/system/"
fi

echo "==============================================="
echo "Setup complete!"
echo "Bot location: /opt/vtm_bot/bot"
echo "To start manually: cd /opt/vtm_bot/bot && source venv/bin/activate && python3 main.py"
echo "==============================================="
