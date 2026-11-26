#!/bin/bash
# 🎙️ One-Click Launcher for VoiceStudio in GitHub Codespaces
echo "=== Starting VoiceStudio Web Server in Codespaces ==="

# Stop existing container if running
docker stop voicestudio 2>/dev/null || true
docker rm voicestudio 2>/dev/null || true

# Run VoiceStudio stable container on port 3900
docker run -d \
  --name voicestudio \
  -p 3900:3900 \
  -e OMNIVOICE_SERVER_MODE=1 \
  -e OMNIVOICE_ANALYTICS_DISABLED=1 \
  -e OMNIVOICE_DATA_DIR=/app/omnivoice_data \
  -v "$(pwd)/voices:/app/voices" \
  -v voicestudio-data:/app/omnivoice_data \
  ghcr.io/debpalash/voicestudio:stable

echo "=========================================================="
echo "🎉 VoiceStudio is now running on Port 3900!"
echo "👉 Codespaces will show a popup: 'Open in Browser'"
echo "   Or click the Ports tab -> Port 3900 -> Open in Browser"
echo "=========================================================="
