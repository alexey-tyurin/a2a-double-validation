#!/bin/bash

# Exit on error
set -e

echo "Starting cloud environment setup..."

# Check if Python 3.10+ is installed
if command -v python3 >/dev/null 2>&1; then
    python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    if (( $(echo "$python_version < 3.10" | bc -l) )); then
        echo "Python version $python_version is less than 3.10"
        echo "Installing Python 3.10..."
        
        # Install Python 3.10 (method depends on the cloud environment)
        # For Ubuntu/Debian-based systems:
        sudo apt-get update
        sudo apt-get install -y software-properties-common
        sudo add-apt-repository -y ppa:deadsnakes/ppa
        sudo apt-get update
        sudo apt-get install -y python3.10 python3.10-venv python3.10-dev
    else
        echo "Python $python_version is already installed"
    fi
else
    echo "Python 3 not found, installing Python 3.10..."
    # Install Python 3.10
    sudo apt-get update
    sudo apt-get install -y software-properties-common
    sudo add-apt-repository -y ppa:deadsnakes/ppa
    sudo apt-get update
    sudo apt-get install -y python3.10 python3.10-venv python3.10-dev
fi

# Create virtual environment
echo "Creating virtual environment..."
python3.10 -m venv venv
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt

# Run the application
echo "Setup complete. Starting the application..."
python main.py 