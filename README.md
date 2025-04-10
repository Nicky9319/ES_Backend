# Microservices Server Template

## Overview
This is template to Build the Server in the Microservices from the Start, It makes it easy to Deploy it in microservices in Future.
This is not as complex to Setup and Really Easy to Use.

## Key Features
This has been made taking into consideration the following:
1. The Server should be able to handle the large number of requests. (Whole Server is Asynchronous)
2. Different Services Can Communication with Each other both in Request Response Method and also in Message Queue Method.
3. It is easy for Anyone to Transfer the Files to the Remote Server and Deploy the Services.
4. People can Choose Which Language they want to use to build the Services. (Python or JS)

## Technical Stack
### Backend Framework
- We are Using fastapi for the API and uvicorn for the server. (Python, Feel Free to Adjust the Framework that meet your needs)

### Message Queue
- We are Using Rabbit MQ as our Messaging Queue System.
  > Note: We are Running Rabbit MQ using Docker at the default Port 5672, if you want to change the Port, you can change the Port in the Docker Compose File.

## Setup and Configuration

### Environment Setup
#### Requirements.txt
1. Mention all the Dependencies in the Requirements.txt File.
2. There Are Some Dependencies that are Project Dependent, You can mention them in the Requirements.txt File.
3. Some of the Dependencies are Already Mentioned in the ServerScripts/setupServer.sh File, these are needed to run the Server with the Current Configuration.

#### .env
1. Mention all the Environment Variables in the env.json File.
2. One Common Use would be mentioning the IP Address of the MongodDB server here.
3. Can mention RabbitMQ ports and other service configurations here to notify all Services.

### Database Configuration
#### MongoDB Setup
1. Setup the Schema in the MongoSchema.json File.
2. In Each service take the Reference from this file to Setup the Schema for the MongoDB in the Service.

> Note: You Can pass this schema to the AI and Ask it to Complete a Function for the Service, hence making it Easy to Develop the Server.

## Development Guide

### Adding New Services
1. Create a new folder in the Services Folder. Idealy Follow the Naming Convention as service_<ServiceName>
2. Add the Service in the ServiceURLMapping.json File.
3. Add all the Necesary files Needed for the Service in the Service Folder.

### Running Services

#### Running Locally
##### Full Server
1. Go the Folder Named ServerScripts
2. Run the TerminalStartServer.sh File. (Note Use the TerminalRestartServer.sh to restart the Whole Server)

##### Individual Service
1. Go the Folder Named Service_<ServiceName>
2. Run the TerminalStartServer.sh File.

#### Remote Deployment
##### Setting Up Remote Server
1. Go the Folder Named ServerScripts
2. Read the setupServer.sh file, it contains Commands to Setup Different Components in the Server.

##### Transferring Files to Remote Server
1. Mention the Files you want to transfer to the Remote Server alongiside with the Remote Server IP Address and the Remote Server Directory
2. Run the CopyFilesToRemoteServer.sh File.

## Testing
### Local Testing
1. Go the Folder Named Testing
2. Run the publisher.py file to send the message to the Server.
3. Run the subscriber.py file to receive the message from the Server.
4. Create Necessary Testing Files Here so that it is Easy to Review the Test and All

## Activating Environment
### Python
1. Create a Venv inside the Local Directory itself and Use it rather than creating it in any other place
2. If Need Different Environment for Different Services Create a venv inside each Service Folder and run the service using that ENV.



