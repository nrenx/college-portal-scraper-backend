#!/bin/bash

# Script to set up Chrome and ChromeDriver on Render

echo "Setting up Chrome and ChromeDriver..."

# Create directory for Chrome
mkdir -p /opt/render/chrome

# Download and install Chrome
echo "Downloading Chrome..."
wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
apt-get update
apt-get install -y ./google-chrome-stable_current_amd64.deb
rm google-chrome-stable_current_amd64.deb

# Create a symlink to the Chrome binary
ln -sf /usr/bin/google-chrome-stable /opt/render/chrome/chrome

# Get Chrome version
CHROME_VERSION=$(google-chrome-stable --version | awk '{print $3}' | cut -d. -f1-3)
echo "Chrome version: $CHROME_VERSION"

# Download matching ChromeDriver
echo "Downloading ChromeDriver..."
CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROME_VERSION")
echo "ChromeDriver version: $CHROMEDRIVER_VERSION"
wget -q "https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip"
unzip -q chromedriver_linux64.zip
chmod +x chromedriver
mv chromedriver /usr/local/bin/
rm chromedriver_linux64.zip

# Set environment variables
echo "Setting environment variables..."
echo "export CHROME_PATH=/opt/render/chrome/chrome" >> ~/.bashrc
echo "export CHROMEDRIVER_PATH=/usr/local/bin/chromedriver" >> ~/.bashrc

# Verify installation
echo "Verifying installation..."
google-chrome-stable --version
chromedriver --version

echo "Chrome and ChromeDriver setup complete!"
