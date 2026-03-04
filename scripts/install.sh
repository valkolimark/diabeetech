#!/bin/bash
set -e

echo "=== Diabeetech Web - Installation ==="

# itiflux and diabeetech-web are SIBLING directories on the Desktop
ITIFLUX="/home/markt/Desktop/itiflux"
DEST="/home/markt/Desktop/diabeetech-web"

# Verify itiflux exists (the reference app we're migrating from)
if [ ! -d "$ITIFLUX" ]; then
    echo "ERROR: itiflux directory not found at $ITIFLUX"
    echo "The existing app must be present for asset copying."
    exit 1
fi

echo "Copying Picovoice models..."
cp -r "$ITIFLUX/models/"*.ppn "$DEST/server/models/"
cp -r "$ITIFLUX/pico/"*.rhn "$DEST/server/pico/"
cp "$ITIFLUX/pico/glucose_logbook.yml" "$DEST/server/pico/"

echo "Copying sounds..."
cp "$ITIFLUX/sounds/"*.wav "$DEST/server/sounds/"

echo "Copying fonts..."
cp "$ITIFLUX/fonts/ProximaNovaBlack.otf" "$DEST/frontend/public/fonts/"
cp "$ITIFLUX/fonts/ProximaNovaBlack.ttf" "$DEST/frontend/public/fonts/"
cp "$ITIFLUX/fonts/pointersregular.ttf" "$DEST/frontend/public/fonts/"
cp "$ITIFLUX/fonts/Poppins-Regular.ttf" "$DEST/frontend/public/fonts/"
cp "$ITIFLUX/fonts/fa-solid-900.ttf" "$DEST/frontend/public/fonts/"

echo "Copying data files..."
cp "$ITIFLUX/settings.json" "$DEST/server/data/"
cp "$ITIFLUX/contacts.json" "$DEST/server/data/" 2>/dev/null || echo '[]' > "$DEST/server/data/contacts.json"
cp "$ITIFLUX/config.json" "$DEST/server/data/"
cp "$ITIFLUX/saved_credentials.json" "$DEST/server/data/" 2>/dev/null || echo '{}' > "$DEST/server/data/saved_credentials.json"

echo "Copying .env (get full OpenAI key)..."
cp "$ITIFLUX/.env" "$DEST/server/.env"

echo "Copying images..."
mkdir -p "$DEST/frontend/public/images"
cp "$ITIFLUX/images/glucocom-logo.png" "$DEST/frontend/public/images/" 2>/dev/null || true

echo "Installing Python dependencies..."
cd "$DEST/server"
pip install -r requirements.txt

echo "Installing frontend dependencies..."
cd "$DEST/frontend"
npm install

echo "=== Installation Complete ==="
