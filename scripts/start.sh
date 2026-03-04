#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/../server"

echo "=== Starting Diabeetech Server ==="
uvicorn main:app --host 0.0.0.0 --port 8080 --reload
