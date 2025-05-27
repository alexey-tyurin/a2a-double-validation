#!/bin/bash

echo "Fixing Docker permissions..."

# Check if user is in docker group
if groups $USER | grep -q '\bdocker\b'; then
    echo "User $USER is already in the docker group."
else
    echo "Adding user $USER to docker group..."
    sudo usermod -aG docker $USER
fi

# Check if Docker daemon is running
if sudo systemctl is-active --quiet docker; then
    echo "Docker daemon is running."
else
    echo "Starting Docker daemon..."
    sudo systemctl start docker
fi

echo ""
echo "Docker permissions fix applied."
echo ""
echo "IMPORTANT: You have two options to activate the group membership:"
echo ""
echo "Option 1 (Recommended): Log out and log back in, then run:"
echo "  ./deploy_to_cloud_run.sh --project your-project-id"
echo ""
echo "Option 2: Use newgrp to activate docker group in current session:"
echo "  newgrp docker"
echo "  ./deploy_to_cloud_run.sh --project your-project-id"
echo ""
echo "Option 3: Test if it works now (sometimes it does):"
echo "  docker --version"
echo "  ./deploy_to_cloud_run.sh --project your-project-id" 