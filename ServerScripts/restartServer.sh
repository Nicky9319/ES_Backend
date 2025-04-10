clear

sudo docker stop rabbit-server
sleep 1

sudo docker run -d --rm --name rabbit-server -p 5672:5672 -p 15672:15672 rabbitmq:3-management
sleep 10

clear

# Mention the Services you want to restart
# Example: systemctl restart MainServer.service

