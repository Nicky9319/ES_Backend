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

    async def fun1(self, message: aio_pika.IncomingMessage):
        msg = message.body.decode()
        print("Fun1 " , msg)
    
    async def fun2(self, message: aio_pika.IncomingMessage):
        msg = message.body.decode()
        print("Fun2 " , msg)


    async def getServiceURL(self, serviceName):
        servicePortMapping = json.load(open("ServiceURLMapping.json"))
        return servicePortMapping[serviceName]


    async def ConfigureAPIRoutes(self):
        @self.httpServer.app.post("/UserProfile/CreateNewUser")
        async def create_new_user(
            PROFILE_PIC: UploadFile = Form(...), 
            PROFILE_BANNER: UploadFile = Form(...),  
            USER_INFO: str = Form(...)
        ):
            # print(PROFILE_PIC)
            # print(USER_INFO)


            serviceName = "MONGO_DB_SERVICE"
            serviceURL = await self.getServiceURL(serviceName)

            userID = None

            async with httpx.AsyncClient() as client:

                USER_INFO["PROFILE_PIC"] = "https://images.unsplash.com/photo-1542751371-adc38448a05e?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80"
                USER_INFO["PROFILE_BANNER"] = "https://images.unsplash.com/photo-1542751371-adc38448a05e?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80"

                response = await client.post(f"http://{serviceURL}/UserProfile/CreateNewUser", data=USER_INFO)
                responseInJson = response.json()

                userID = responseInJson["USER_ID"]

                print("Response from MongoDB Service: ", responseInJson)
        

            if PROFILE_PIC != None:
                serviceName = "BLOB_STORAGE_SERVICE"
                serviceURL = await self.getServiceURL(serviceName)

                files = {
                    "PROFILE_PIC": (PROFILE_PIC.filename, await PROFILE_PIC.read(), PROFILE_PIC.content_type),
                }
                data = {
                    "USER_ID": str(userID)
                }
    
                async with httpx.AsyncClient() as client:
                    response = await client.post(f"http://{serviceURL}/UserProfilePic/StoreImage", files=files, data=data)
                    responseInJson = response.json()

                
                serviceName = "MONGO_DB_SERVICE"
                serviceURL = await self.getServiceURL(serviceName)

                data = {
                    "USER_ID" : str(userID),
                    "PROFILE_PIC" : f"http://{self.serverIPAddress}:15000/Image/RetrieveImage?bucket=user-profile-pic&key={userID}.jpg"
                }

                async with httpx.AsyncClient() as client:
                    response = await client.post(f"http://{serviceURL}/UserProfile/UpdateUserProfilePic", data=data)
                    responseInJson = response.json()
                print("Response from MongoDB Service: ", responseInJson)


            if PROFILE_BANNER != None:
                files ={
                    "PROFILE_BANNER": (PROFILE_BANNER.filename, await PROFILE_BANNER.read(), PROFILE_BANNER.content_type)
                }
                data = {
                    "USER_ID": str(userID)
                }

                async with httpx.AsyncClient() as client:
                    response = await client.post(f"http://{serviceURL}/UserProfileBanner/StoreImage", files=files, data=data)
                    responseInJson = response.json()

                serviceName = "MONGO_DB_SERVICE"
                serviceURL = await self.getServiceURL(serviceName)

                data = {
                    "USER_ID" : str(userID),
                    "PROFILE_BANNER" : f"http://{self.serverIPAddress}:15000/Image/RetrieveImage?bucket=user-profile-banner&key={userID}.jpg"
                }

                async with httpx.AsyncClient() as client:
                    response = await client.post(f"http://{serviceURL}/UserProfileBanner/StoreImage", files=files, data=data)
                    responseInJson = response.json()
                print("Response from MongoDB Service: ", responseInJson)


            return {"message": f"Created new user with info {USER_INFO}"}
    

    async def startService(self):
        # await self.messageQueue.InitializeConnection()
        # await self.messageQueue.AddQueueAndMapToCallback("queue1", self.fun1)
        # await self.messageQueue.AddQueueAndMapToCallback("queue2", self.fun2)
        # await self.messageQueue.StartListeningToQueue()

        await self.ConfigureAPIRoutes()
        await self.httpServer.run_app()

        
async def start_service():
    service = Service('0.0.0.0', 7000)
    await service.startService()

if __name__ == "__main__":
    asyncio.run(start_service())
