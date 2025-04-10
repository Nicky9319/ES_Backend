# Mongo DB Setup

sudo apt update
wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list
sudo apt update
sudo apt install -y mongodb-org
sudo systemctl start mongod
sudo systemctl enable mongod



# Rabbit MQ Setup

sudo apt update
sudo apt install docker.io -y
# sudo docker run -d --rm --name my-rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:latest
sudo docker run -d --rm --name rabbit-server -p 5672:5672 -p 15672:15672 rabbitmq:3-management

        
sudo nano /etc/rabbitmq/rabbitmq-env.conf
# Change RabbitMQ Config File as per Need


# Redis Setup

sudo apt update
sudo add-apt-repository ppa:redislabs/redis
sudo apt install redis
redis-server --version
sudo systemctl enable redis-server
sudo systemctl start redis-server

sudo nano /etc/redis/redis.conf
# Change Redis Config File to Make it run on port 10000 rather than default 6379

# Settig up Neuralperk Folders in the Server

cd /home
mkdir Neuralperk


# Python Installation

sudo apt update
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.12 python3.12-venv -y

sudo apt install python3-pip

# Creating Virtual Environment (Neuralperk_Env) inside the dedicated folder

cd /home/Neuralperk
python3.12 -m venv Neuralperk_Env


# Installing Dependencies Inside the Virtual Environment

cd /home/Neuralperk
source /Neuralperk_Env/bin/activate
pip install flask requests python-socketio eventlet pymongo gunicorn redis fastapi uvicorn aiohttp vastai aio_pika
deactivate

# Downloading and Setting up Blender

cd /
wget https://download.blender.org/release/Blender4.2/blender-4.2.0-linux-x64.tar.xz
sudo tar -xf blender-4.2.0-linux-x64.tar.xz

mv blender4.2.0-linux-x64.tar.xz Blender
apt-get update && \
apt-get install -y \
        libx11-6 \
        libx11-dev \
        libxrender1 \
        libxxf86vm1 \
        libxfixes3 \
        libxi6 \
        libxkbcommon0 \
        libsm6 \
        libgl1

ln -s /Blender/blender /usr/bin/blender



# Tmux Installation and Setup

apt update
apt install tmux
echo -e "set -g mouse on\nsetw -g mode-keys vi" >> ~/.tmux.conf




# Activate Environment and Installing en_core_web_sm after installing basic requirements into it

python -m spacy download en_core_web_sm




# Setting Up Sqlite3 Version >= 3.35.0

sudo apt update
sudo apt upgrade -y

sudo apt install -y build-essential wget

wget https://www.sqlite.org/2021/sqlite-autoconf-3350500.tar.gz
tar -xvzf sqlite-autoconf-3350500.tar.gz
cd sqlite-autoconf-3350500

./configure
make
sudo make install

sqlite3 --version



# Copy Files from Local to Remote Server [Do it Using SCP and SSH]



#--------------------------------------------------------------------END-------------------------------------------------------------------