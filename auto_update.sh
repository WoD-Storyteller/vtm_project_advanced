#!/bin/bash

REPO_DIR="/opt/vtm_project_advanced"
LOG="/var/log/vtm_autopull.log"

echo "====== AUTO UPDATE CHECK ======" >> $LOG
echo "$(date)" >> $LOG

cd $REPO_DIR

# Make Git safe
git config --global --add safe.directory "$REPO_DIR"

# Fetch latest changes
git fetch origin >> $LOG 2>&1

LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)

if [ "$LOCAL" != "$REMOTE" ]; then
  echo "New update found. Pulling..." >> $LOG

  git reset --hard origin/main >> $LOG 2>&1

  echo "Restarting services..." >> $LOG
  systemctl restart vtm_api.service
  systemctl restart vtm_bot.service

  echo "Update applied at $(date)" >> $LOG
else
  echo "No update available." >> $LOG
fi

echo "" >> $LOG
