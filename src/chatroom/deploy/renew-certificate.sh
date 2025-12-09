#!/bin/bash

DOMAIN="chatroom.blundr.razvanalbu.com"
TLS_DIR="/etc/letsencrypt/live/$DOMAIN"
CONTAINER_NAME="chatroom"

echo "Starting certificate renewal for $DOMAIN..."

# Renew certificate in standalone mode
sudo certbot certonly --standalone -d "$DOMAIN" --non-interactive --agree-tos -m gusalbura@student.gu.se 

if [ $? -eq 0 ]; then
    echo "Certificate renewed successfully."
    echo "Restarting Docker container $CONTAINER_NAME..."
    sudo docker restart "$CONTAINER_NAME"

    if [ $? -eq 0 ]; then
        echo "Docker container restarted successfully."
    else
        echo "Failed to restart Docker container $CONTAINER_NAME."
        exit 1
    fi
else
    echo "Certificate renewal failed!"
    exit 1
fi

echo "Done."
