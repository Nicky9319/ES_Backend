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
from fastapi.middleware.cors import CORSMiddleware

class Service():
    def __init__(self,httpServerHost, httpServerPort):
        self.messageQueue = MessageQueue("amqp://guest:guest@localhost/","/")
        self.httpServer = HTTPServer(httpServerHost, httpServerPort)

        self.serverIPAddress = os.getenv("SERVER_IP_ADDRESS")

        self.httpServer.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )


    async def getServiceURL(self, serviceName):
            PROFILE_BANNER: UploadFile = Form(...),  
            MENTOR_INFO: str = Form(...)
        ):
            serviceName = "MONGO_DB_SERVICE"
            serviceURL = await self.getServiceURL(serviceName)

            mentorID = None

            MENTOR_INFO = json.loads(MENTOR_INFO)

            async with httpx.AsyncClient() as client:

                MENTOR_INFO["PROFILE_PIC"] = "https://images.unsplash.com/photo-1542751371-adc38448a05e?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80"
                MENTOR_INFO["PROFILE_BANNER"] = "https://images.unsplash.com/photo-1542751371-adc38448a05e?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80"

                response = await client.post(f"http://{serviceURL}/MentorProfile/CreateNewMentor", json=MENTOR_INFO)
                responseInJson = response.json()


                # print("Response from MongoDB Service: ", responseInJson)
                # print()
                mentorID = responseInJson["MENTOR_ID"]

            print("Mentor ID: ", mentorID)

            if PROFILE_PIC != None:
                serviceName = "BLOB_STORAGE_SERVICE"
                serviceURL = await self.getServiceURL(serviceName)

                files = {
                    "PROFILE_PIC": (PROFILE_PIC.filename, await PROFILE_PIC.read(), PROFILE_PIC.content_type),
                }
                data = {
                    "MENTOR_ID": str(mentorID)
                }
    
                async with httpx.AsyncClient() as client:
                    response = await client.post(f"http://{serviceURL}/MentorProfilePic/StoreImage", files=files, data=data)
                    responseInJson = response.json()

                
                serviceName = "MONGO_DB_SERVICE"
                serviceURL = await self.getServiceURL(serviceName)

                data = {
                    "MENTOR_ID" : str(mentorID),
                    "PROFILE_PIC" : f"http://{self.serverIPAddress}:15000/Image/RetrieveImage?bucket=mentor-profile-pic&key={mentorID}.jpg"
                }

                async with httpx.AsyncClient() as client:
                    response = await client.put(f"http://{serviceURL}/MentorProfile/Update/ProfilePic", json=data)
                    responseInJson = response.json()
                print("Response from MongoDB Service: ", responseInJson)

            print("Profile Pic Updated")

            if PROFILE_BANNER != None:
                serviceName = "BLOB_STORAGE_SERVICE"
                serviceURL = await self.getServiceURL(serviceName)

                files = {
                    "PROFILE_BANNER": (PROFILE_BANNER.filename, await PROFILE_BANNER.read(), PROFILE_BANNER.content_type),
                }
                data = {
                    "MENTOR_ID": str(mentorID)
                }
    
                async with httpx.AsyncClient() as client:
                    response = await client.post(f"http://{serviceURL}/MentorProfileBanner/StoreImage", files=files, data=data)
                    responseInJson = response.json()

                
                serviceName = "MONGO_DB_SERVICE"
                serviceURL = await self.getServiceURL(serviceName)

                data = {
                    "MENTOR_ID" : str(mentorID),
                    "PROFILE_BANNER" : f"http://{self.serverIPAddress}:15000/Image/RetrieveImage?bucket=mentor-profile-banner&key={mentorID}.jpg"
                }

                async with httpx.AsyncClient() as client:
                    response = await client.put(f"http://{serviceURL}/MentorProfile/Update/ProfileBanner", json=data)
                    responseInJson = response.json()
                print("Response from MongoDB Service: ", responseInJson)

            print("Profile Banner Updated")

            return {"MENTOR_ID": mentorID}

        @self.httpServer.app.get("/MentorProfile/GetAllMentorProfiles")
        async def get_all_mentor_profiles():
            serviceName = "MONGO_DB_SERVICE"
            serviceURL = await self.getServiceURL(serviceName)

            async with httpx.AsyncClient() as client:
                response = await client.get(f"http://{serviceURL}/MentorProfile/GetAllMentorProfiles")
                responseInJson = response.json()

            return responseInJson

        @self.httpServer.app.get("/MentorProfile/GetMentorProfile")
        async def get_mentor_profile(
            MENTOR_ID: str,
        ):
            serviceName = "MONGO_DB_SERVICE"
            serviceURL = await self.getServiceURL(serviceName)

            async with httpx.AsyncClient() as client:
                response = await client.get(f"http://{serviceURL}/MentorProfile/GetMentorProfile?MENTOR_ID={MENTOR_ID}")
                responseInJson = response.json()

            return responseInJson
    

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
