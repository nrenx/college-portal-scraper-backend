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
  "/opt/google/chrome/chrome"
  "/opt/render/project/.render/chrome/chrome"
  "/opt/render/chrome/chrome"
)

# Try to find Chrome using which
WHICH_CHROME=$(which google-chrome-stable 2>/dev/null || which google-chrome 2>/dev/null || which chromium-browser 2>/dev/null || which chromium 2>/dev/null)
if [ -n "$WHICH_CHROME" ]; then
  echo "Found Chrome using which: $WHICH_CHROME"
  CHROME_PATHS+=("$WHICH_CHROME")
fi

# Look for Chrome in PATH
echo "PATH: $PATH"
IFS=':' read -ra PATH_DIRS <<< "$PATH"
for dir in "${PATH_DIRS[@]}"; do
  for name in "google-chrome-stable" "google-chrome" "chromium-browser" "chromium"; do
    if [ -f "$dir/$name" ]; then
      echo "Found Chrome in PATH: $dir/$name"
      CHROME_PATHS+=("$dir/$name")
    fi
  done
done

CHROME_PATH=""
for path in "${CHROME_PATHS[@]}"; do
  if [ -f "$path" ]; then
    CHROME_PATH="$path"
    echo "Using Chrome binary: $CHROME_PATH"
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
  "/opt/render/project/.render/chromedriver/chromedriver"
  "/opt/render/chromedriver/chromedriver"
)

# Try to find ChromeDriver using which
WHICH_CHROMEDRIVER=$(which chromedriver 2>/dev/null)
if [ -n "$WHICH_CHROMEDRIVER" ]; then
  echo "Found ChromeDriver using which: $WHICH_CHROMEDRIVER"
  CHROMEDRIVER_PATHS+=("$WHICH_CHROMEDRIVER")
fi

# Look for ChromeDriver in PATH
IFS=':' read -ra PATH_DIRS <<< "$PATH"
for dir in "${PATH_DIRS[@]}"; do
  if [ -f "$dir/chromedriver" ]; then
    echo "Found ChromeDriver in PATH: $dir/chromedriver"
    CHROMEDRIVER_PATHS+=("$dir/chromedriver")
  fi
done

# Try to install ChromeDriver using webdriver-manager
echo "Attempting to install ChromeDriver using webdriver-manager..."
python -c "from webdriver_manager.chrome import ChromeDriverManager; print(ChromeDriverManager().install())" > chromedriver_path.txt 2>/dev/null
if [ $? -eq 0 ]; then
  WEBDRIVER_MANAGER_PATH=$(cat chromedriver_path.txt)
  if [ -n "$WEBDRIVER_MANAGER_PATH" ]; then
    echo "Found ChromeDriver using webdriver-manager: $WEBDRIVER_MANAGER_PATH"
    CHROMEDRIVER_PATHS+=("$WEBDRIVER_MANAGER_PATH")
  fi
fi

CHROMEDRIVER_PATH=""
for path in "${CHROMEDRIVER_PATHS[@]}"; do
  if [ -f "$path" ]; then
    CHROMEDRIVER_PATH="$path"
    echo "Using ChromeDriver binary: $CHROMEDRIVER_PATH"
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
  ls -la /usr/bin | grep -i chrome 2>/dev/null || echo "No Chrome found in /usr/bin"
  echo "Directory listing of /usr/local/bin (grep chrome):"
  ls -la /usr/local/bin | grep -i chrome 2>/dev/null || echo "No Chrome found in /usr/local/bin"
  echo "Directory listing of /opt/render (find chrome):"
  find /opt/render -name "*chrome*" 2>/dev/null || echo "No Chrome found in /opt/render"
  echo "Directory listing of /opt/render/project (find chrome):"
  find /opt/render/project -name "*chrome*" 2>/dev/null || echo "No Chrome found in /opt/render/project"
  echo "Directory listing of /opt (find chrome):"
  find /opt -name "*chrome*" 2>/dev/null || echo "No Chrome found in /opt"
  echo "Directory listing of /usr/bin (find chromedriver):"
  find /usr/bin -name "*chromedriver*" 2>/dev/null || echo "No ChromeDriver found in /usr/bin"
  echo "Directory listing of /usr/local/bin (find chromedriver):"
  find /usr/local/bin -name "*chromedriver*" 2>/dev/null || echo "No ChromeDriver found in /usr/local/bin"
  echo "Directory listing of /opt/render (find chromedriver):"
  find /opt/render -name "*chromedriver*" 2>/dev/null || echo "No ChromeDriver found in /opt/render"
  echo "PATH environment variable:"
  echo "$PATH"
  echo "Checking for Chrome packages:"
  dpkg -l | grep -i chrome 2>/dev/null || echo "No Chrome packages found with dpkg"
  apt list --installed | grep -i chrome 2>/dev/null || echo "No Chrome packages found with apt"
} > "$DEBUG_FILE"

echo "Debug information saved to $DEBUG_FILE"
