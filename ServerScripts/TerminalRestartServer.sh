/home/Avatar/bin/python3.12 StopServer.py

clear

cd ../

# Stop any running instances defined in the docker-compose file
sudo docker-compose -f ServerScripts/docker-compose.yml down
sleep 2

# Start containers via docker-compose
sudo docker-compose -f ServerScripts/docker-compose.yml up -d
sleep 10

cd ../

# Mention the Environment you want to start along with the Services
# Example: /home/Avatar/Avatar_Env/bin/python3.12 service_MainServer/mainServer.py &
#          /home/Avatar/Avatar_Env/bin/python3.12 service_LogService/loggingService.py
