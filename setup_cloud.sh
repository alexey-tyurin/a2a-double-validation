#!/bin/bash

# Exit on error
set -e

echo "Starting cloud environment setup..."

# Update package list
echo "Updating package list..."
sudo apt-get update

# Check if Python 3.10+ is installed
if command -v python3 >/dev/null 2>&1; then
    python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    if (( $(echo "$python_version < 3.10" | bc -l) )); then
        echo "Python version $python_version is less than 3.10"
        echo "Installing Python 3.10..."
        
        # Install Python 3.10 (method depends on the cloud environment)
        # For Ubuntu/Debian-based systems:
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
    sudo apt-get install -y software-properties-common
    sudo add-apt-repository -y ppa:deadsnakes/ppa
    sudo apt-get update
    sudo apt-get install -y python3.10 python3.10-venv python3.10-dev
fi

# Install Docker if not present
if ! command -v docker >/dev/null 2>&1; then
    echo "Docker not found, installing Docker..."
    
    # Remove any old Docker packages
    sudo apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true
    
    # Install required packages
    sudo apt-get install -y ca-certificates curl gnupg lsb-release
    
    # Add Docker's official GPG key (updated method)
    sudo mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    sudo chmod a+r /etc/apt/keyrings/docker.gpg
    
    # Set up the repository
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
      sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Update package list and install Docker
    sudo apt-get update
    
    # Install Docker packages
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    
    # Add current user to docker group
    sudo usermod -aG docker $USER
    
    # Start and enable Docker service
    sudo systemctl start docker
    sudo systemctl enable docker
    
    echo "Docker installed successfully. You may need to log out and back in for group changes to take effect."
    echo "Testing Docker installation..."
    sudo docker run hello-world || echo "Docker test failed, but installation may still be successful"
else
    echo "Docker is already installed"
fi

# Install Google Cloud CLI if not present
if ! command -v gcloud >/dev/null 2>&1; then
    echo "Google Cloud CLI not found, installing..."
    
    # Install using the official installation script (more reliable)
    curl https://sdk.cloud.google.com | bash
    
    # Add gcloud to PATH for current session
    export PATH="$HOME/google-cloud-sdk/bin:$PATH"
    
    echo "Google Cloud CLI installed. Please run 'gcloud auth login' to authenticate."
    echo "You may need to restart your shell or run: source ~/.bashrc"
else
    echo "Google Cloud CLI is already installed"
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
pip install --no-cache-dir -r requirements.txt

# Apply Python 3.10 compatibility patch if needed
if [ -f "python310_compatibility_patch.py" ]; then
    echo "Applying Python 3.10 compatibility patch..."
    python python310_compatibility_patch.py
fi

# Run the application
echo "Setup complete. Starting the application..."
python main.py &