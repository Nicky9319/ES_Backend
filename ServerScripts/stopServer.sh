clear

cd ../

# Stop docker-compose containers
sudo docker-compose -f ServerScripts/docker-compose.yml down
sleep 2

# Mention the Services you want to stop
# Example: systemctl stop MainServer.service
