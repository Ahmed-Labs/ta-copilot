#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/home/ubuntu/course-support-backend"

sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip nginx

cd "$APP_DIR"

python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

sudo cp deploy/ec2/course-support-backend.service /etc/systemd/system/course-support-backend.service
sudo cp deploy/ec2/course-support-backend.nginx.conf /etc/nginx/sites-available/course-support-backend
sudo ln -sf /etc/nginx/sites-available/course-support-backend /etc/nginx/sites-enabled/course-support-backend
sudo rm -f /etc/nginx/sites-enabled/default

sudo systemctl daemon-reload
sudo systemctl enable course-support-backend
sudo systemctl restart course-support-backend
sudo nginx -t
sudo systemctl restart nginx

echo "Deployment complete."
echo "Check backend status with: sudo systemctl status course-support-backend"
echo "Check nginx status with: sudo systemctl status nginx"
