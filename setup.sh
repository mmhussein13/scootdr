#!/bin/bash

# ScootDR Setup Script for Replit
echo "Setting up ScootDR environment..."

# Update system packages
echo "Updating system packages..."
apt-get update

# Install git if not available
if ! command -v git &> /dev/null; then
    echo "Installing git..."
    apt-get install -y git
fi

# Install PostgreSQL client tools
echo "Installing PostgreSQL client tools..."
apt-get install -y postgresql-client

# Install Python dependencies for common packages
echo "Installing common Python packages..."
pip install --upgrade pip

# Make deploy script executable
chmod +x deploy.py

# Run the deployment
echo "Running deployment script..."
python deploy.py

echo "Setup completed!"
echo "The ScootDR repository has been cloned and set up."
echo "Please check the deployment output for any additional configuration needed."
