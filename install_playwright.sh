#!/bin/bash

# Script to install Playwright and its browsers
echo "Installing Playwright browsers..."

# Create a custom directory for Playwright browsers
PLAYWRIGHT_BROWSERS_PATH="/opt/render/project/browsers"
mkdir -p $PLAYWRIGHT_BROWSERS_PATH
chmod -R 777 $PLAYWRIGHT_BROWSERS_PATH
echo "Created custom browsers directory at $PLAYWRIGHT_BROWSERS_PATH"

# Export the environment variable
export PLAYWRIGHT_BROWSERS_PATH=$PLAYWRIGHT_BROWSERS_PATH
echo "PLAYWRIGHT_BROWSERS_PATH=$PLAYWRIGHT_BROWSERS_PATH"

# Add to .bashrc and .profile
echo "export PLAYWRIGHT_BROWSERS_PATH=$PLAYWRIGHT_BROWSERS_PATH" >> ~/.bashrc
echo "export PLAYWRIGHT_BROWSERS_PATH=$PLAYWRIGHT_BROWSERS_PATH" >> ~/.profile

# System dependencies are already installed on Render
echo "Skipping system dependencies installation (already handled by Render)..."

# Install Playwright browsers with the custom path (without --with-deps to avoid requiring root)
echo "Installing Playwright browsers to $PLAYWRIGHT_BROWSERS_PATH..."
PLAYWRIGHT_BROWSERS_PATH=$PLAYWRIGHT_BROWSERS_PATH python -m playwright install chromium

# Try alternative installation approach
echo "Trying alternative browser installation approach..."
cat > install_browser.py << 'EOF'
from playwright.sync_api import sync_playwright
import os
import sys

# Set browsers path
browsers_path = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
if browsers_path:
    print(f"Using browsers path: {browsers_path}")
else:
    print("PLAYWRIGHT_BROWSERS_PATH not set")

try:
    with sync_playwright() as p:
        # This will trigger the browser download
        browser = p.chromium.launch()
        browser.close()
        print("Successfully launched and closed browser")
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)

print("Browser installation successful")
EOF

# Run the alternative installation script
python install_browser.py

# Verify installation
echo "Verifying installation..."
python -m playwright --version

# List installed browsers
echo "Listing installed browsers..."
ls -la $PLAYWRIGHT_BROWSERS_PATH || echo "No browsers found in $PLAYWRIGHT_BROWSERS_PATH"
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
