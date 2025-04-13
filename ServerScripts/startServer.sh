clear

sudo docker-compose -f ServerScripts/docker-compose.yml up -d
sleep 10

# Mention the Services you want to restart
# Example: systemctl start MainServer.service
