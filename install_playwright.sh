#!/bin/bash

# Script to install Playwright and its browsers
echo "Installing Playwright browsers..."

# Install system dependencies
echo "Installing system dependencies..."
apt-get update && apt-get install -y \
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libatspi2.0-0 \
    libx11-6 \
    libxcb1 \
    libxext6 \
    libx11-xcb1

# Install Playwright browsers
echo "Installing Playwright browsers..."
python -m playwright install --with-deps chromium

# Verify installation
echo "Verifying installation..."
python -m playwright --version

# List installed browsers
echo "Listing installed browsers..."
ls -la ~/.cache/ms-playwright/ || echo "No browsers found in ~/.cache/ms-playwright/"
ls -la /opt/render/.cache/ms-playwright/ || echo "No browsers found in /opt/render/.cache/ms-playwright/"

# Create a debug file with installation information
echo "Creating debug information file..."
DEBUG_FILE="playwright_install_debug.txt"
{
  echo "Date: $(date)"
  echo "Playwright version:"
  python -m playwright --version
  echo "System information:"
  uname -a
  echo "Python version:"
  python --version
  echo "Installed browsers in ~/.cache/ms-playwright/:"
  ls -la ~/.cache/ms-playwright/ 2>/dev/null || echo "No browsers found in ~/.cache/ms-playwright/"
  echo "Installed browsers in /opt/render/.cache/ms-playwright/:"
  ls -la /opt/render/.cache/ms-playwright/ 2>/dev/null || echo "No browsers found in /opt/render/.cache/ms-playwright/"
  echo "Environment variables:"
  env | grep -i playwright
} > "$DEBUG_FILE"

echo "Debug information saved to $DEBUG_FILE"
echo "Playwright installation complete!"
