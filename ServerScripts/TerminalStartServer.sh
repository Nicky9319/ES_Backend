clear

sudo docker stop rabbit-server
sleep 1

cd ../

sudo docker-compose -f ServerScripts/docker-compose.yml up -d
sleep 10



# Mention the Environment you want to start along with the Services
# Example: /home/Avatar/Avatar_Env/bin/python3.12 service_MainServer/mainServer.py &
#          /home/Avatar/Avatar_Env/bin/python3.12 service_LogService/loggingService.py 

# Example: ../.venv/bin/python3.12 service_MainServer/mainServer.py (When Trying to Run from Local venv)