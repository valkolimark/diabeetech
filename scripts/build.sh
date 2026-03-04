#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Building Diabeetech Web Frontend ==="

cd "$SCRIPT_DIR/../frontend"
npm run build

echo "Copying static export to server..."
rm -rf "$SCRIPT_DIR/../server/static"
cp -r out "$SCRIPT_DIR/../server/static"

echo "=== Build Complete ==="
