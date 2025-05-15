#!/bin/bash

# Script to set up Chrome and ChromeDriver on Render
# This script assumes Chrome is already installed on Render
# and focuses on finding and configuring the paths

echo "Setting up Chrome and ChromeDriver for Render..."

# Create directory for Chrome if it doesn't exist
mkdir -p /opt/render/chrome

# Find Chrome binary
CHROME_PATHS=(
  "/usr/bin/google-chrome-stable"
  "/usr/bin/google-chrome"
  "/usr/bin/chromium-browser"
  "/usr/bin/chromium"
)

CHROME_PATH=""
for path in "${CHROME_PATHS[@]}"; do
  if [ -f "$path" ]; then
    CHROME_PATH="$path"
    break
  fi
done

if [ -z "$CHROME_PATH" ]; then
  echo "Chrome binary not found in standard locations. Using 'which' to search..."
  CHROME_PATH=$(which google-chrome-stable 2>/dev/null || which google-chrome 2>/dev/null || which chromium-browser 2>/dev/null || which chromium 2>/dev/null)
fi

if [ -z "$CHROME_PATH" ]; then
  echo "WARNING: Chrome binary not found. The application may not work correctly."
else
  echo "Found Chrome at: $CHROME_PATH"

  # Create a symlink to the Chrome binary
  ln -sf "$CHROME_PATH" /opt/render/chrome/chrome

  # Get Chrome version
  CHROME_VERSION=$("$CHROME_PATH" --version 2>/dev/null | awk '{print $3}' | cut -d. -f1-3)
  echo "Chrome version: $CHROME_VERSION"

  # Set environment variables
  echo "Setting environment variables..."
  export CHROME_PATH="$CHROME_PATH"
  echo "export CHROME_PATH=\"$CHROME_PATH\"" >> ~/.bashrc

  # Verify Chrome installation
  echo "Verifying Chrome installation..."
  "$CHROME_PATH" --version
fi

# Find ChromeDriver binary
CHROMEDRIVER_PATHS=(
  "/usr/local/bin/chromedriver"
  "/usr/bin/chromedriver"
)

CHROMEDRIVER_PATH=""
for path in "${CHROMEDRIVER_PATHS[@]}"; do
  if [ -f "$path" ]; then
    CHROMEDRIVER_PATH="$path"
    break
  fi
done

if [ -z "$CHROMEDRIVER_PATH" ]; then
  echo "ChromeDriver binary not found in standard locations. Using 'which' to search..."
  CHROMEDRIVER_PATH=$(which chromedriver 2>/dev/null)
fi

if [ -z "$CHROMEDRIVER_PATH" ]; then
  echo "WARNING: ChromeDriver binary not found. The application may not work correctly."
else
  echo "Found ChromeDriver at: $CHROMEDRIVER_PATH"

  # Set environment variables
  export CHROMEDRIVER_PATH="$CHROMEDRIVER_PATH"
  echo "export CHROMEDRIVER_PATH=\"$CHROMEDRIVER_PATH\"" >> ~/.bashrc

  # Verify ChromeDriver installation
  echo "Verifying ChromeDriver installation..."
  "$CHROMEDRIVER_PATH" --version
fi

echo "Chrome and ChromeDriver setup complete!"
echo "CHROME_PATH=$CHROME_PATH"
echo "CHROMEDRIVER_PATH=$CHROMEDRIVER_PATH"

# Create a debug file with system information
echo "Creating debug information file..."
DEBUG_FILE="chrome_setup_debug.txt"
{
  echo "Date: $(date)"
  echo "Chrome path: $CHROME_PATH"
  echo "ChromeDriver path: $CHROMEDRIVER_PATH"
  echo "Chrome version: $("$CHROME_PATH" --version 2>/dev/null || echo 'Not available')"
  echo "ChromeDriver version: $("$CHROMEDRIVER_PATH" --version 2>/dev/null || echo 'Not available')"
  echo "System information:"
  uname -a
  echo "Directory listing of /usr/bin (grep chrome):"
  ls -la /usr/bin | grep -i chrome
  echo "Directory listing of /usr/local/bin (grep chrome):"
  ls -la /usr/local/bin | grep -i chrome
  echo "PATH environment variable:"
  echo "$PATH"
} > "$DEBUG_FILE"

echo "Debug information saved to $DEBUG_FILE"
