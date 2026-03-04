#!/bin/bash
set -e

echo "=== Installing Diabeetech systemd services ==="

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR/.."

sudo cp "$PROJECT_DIR/diabeetech-server.service" /etc/systemd/system/
sudo cp "$PROJECT_DIR/diabeetech-kiosk.service" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable diabeetech-server diabeetech-kiosk

echo "=== Services installed and enabled ==="
echo "Start with: sudo systemctl start diabeetech-server && sleep 5 && sudo systemctl start diabeetech-kiosk"
