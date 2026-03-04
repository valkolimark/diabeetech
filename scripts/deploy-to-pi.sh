#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PI_HOST="${1:-diabeetech.local}"

echo "=== Building frontend ==="
cd "$SCRIPT_DIR/../frontend"
npm run build
rm -rf "$SCRIPT_DIR/../server/static"
cp -r out "$SCRIPT_DIR/../server/static"

echo "=== Deploying to Pi ($PI_HOST) ==="
rsync -avz --exclude='node_modules' --exclude='.next' --exclude='__pycache__' \
  --exclude='.env' \
  "$SCRIPT_DIR/../" \
  "markt@$PI_HOST:/home/markt/Desktop/diabeetech-web/"

echo "=== Restarting server on Pi ==="
ssh "markt@$PI_HOST" "sudo systemctl restart diabeetech-server"

echo "=== Deploy complete ==="
