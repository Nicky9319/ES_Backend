clear

# Restart other services via docker-compose
sudo docker-compose -f ServerScripts/docker-compose.yml down
sleep 2

sudo docker-compose -f ServerScripts/docker-compose.yml up -d
sleep 10

clear

# Additional service restart commands
# Example: systemctl restart MainServer.service

