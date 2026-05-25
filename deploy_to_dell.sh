#!/usr/bin/env bash

# --- Configuration ---
DELL_IP="100.88.3.74"  
DELL_USER="saisi"
PROJECT_PATH="C:/Users/saisi/Documents/MarketAnalyser" 
# ---------------------

echo "Starting Deployment to Dell Windows Machine..."

echo "Compressing project files..."
tar --exclude=data --exclude=.git --exclude=__pycache__ --exclude=.env --exclude=frontend/node_modules --exclude=frontend/dist --exclude=deploy.tar.gz -czf deploy.tar.gz .

echo "Transferring to $DELL_IP over Tailscale..."
scp -o StrictHostKeyChecking=no deploy.tar.gz ${DELL_USER}@${DELL_IP}:C:/Users/saisi/deploy.tar.gz

if [ $? -eq 0 ]; then
    echo "Transfer successful."
else
    echo "Transfer failed. Ensure OpenSSH Server is running on the Dell."
    rm deploy.tar.gz
    exit 1
fi

echo "Unpacking and Restarting Docker on Dell..."
ssh -o StrictHostKeyChecking=no ${DELL_USER}@${DELL_IP} "mkdir -p ${PROJECT_PATH} && tar -xzf C:/Users/saisi/deploy.tar.gz -C ${PROJECT_PATH} && del C:\\Users\\saisi\\deploy.tar.gz && cd ${PROJECT_PATH} && docker-compose down && docker-compose up -d --build"

if [ $? -eq 0 ]; then
    echo "Deployment complete! The Dell is now running the latest code in Production mode."
else
    echo "Docker restart failed."
fi

rm deploy.tar.gz
