import asyncio
from fastapi import FastAPI, Response, Request, Form, UploadFile
import uvicorn

import requests

import asyncio
import aio_pika

import json
import uuid
import httpx

import sys
import os

from dotenv import load_dotenv
load_dotenv()

sys.path.append(os.path.join(os.path.dirname(__file__), "../ServiceTemplates/Basic"))


from HTTP_SERVER import HTTPServer
from MESSAGE_QUEUE import MessageQueue

class Service():
    def __init__(self,httpServerHost, httpServerPort):
        self.messageQueue = MessageQueue("amqp://guest:guest@localhost/","/")
        self.httpServer = HTTPServer(httpServerHost, httpServerPort)

        self.serverIPAddress = os.getenv("SERVER_IP_ADDRESS")


    async def getServiceURL(self, serviceName):
        servicePortMapping = json.load(open("ServiceURLMapping.json"))
        return servicePortMapping[serviceName]



    async def ConfigureAPIRoutes(self):
        @self.httpServer.app.post("/MentorProfile/CreateNewMentor")
        async def create_new_mentor(
            PROFILE_PIC: UploadFile = Form(...), 
            PROFILE_BANNER: UploadFile = Form(...),  
            USER_INFO: str = Form(...)
        ):
            serviceName = "MONGO_DB_SERVICE"
            serviceURL = await self.getServiceURL(serviceName)

            userID = None
    

    async def startService(self):
        # await self.messageQueue.InitializeConnection()
        # await self.messageQueue.AddQueueAndMapToCallback("queue1", self.fun1)
        # await self.messageQueue.AddQueueAndMapToCallback("queue2", self.fun2)
        # await self.messageQueue.StartListeningToQueue()

        await self.ConfigureAPIRoutes()
        await self.httpServer.run_app()

        
async def start_service():
    service = Service('0.0.0.0', 10000)
    await service.startService()

if __name__ == "__main__":
    asyncio.run(start_service())
