import asyncio
from fastapi import FastAPI, Response, Request, Form, UploadFile, HTTPException
import uvicorn

import asyncio
import aio_pika

from fastapi.middleware.cors import CORSMiddleware

import json
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

        self.httpServer.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Allows all origins
            allow_credentials=True,
            allow_methods=["*"],  # Allows all methods
            allow_headers=["*"],  # Allows all headers
        )

        self.serverIPAddress = os.getenv("SERVER_IP_ADDRESS")

    # async def fun1(self, message: aio_pika.IncomingMessage):
    #     msg = message.body.decode()
    #     print("Fun1 " , msg)
    
    # async def fun2(self, message: aio_pika.IncomingMessage):
    #     msg = message.body.decode()
    #     print("Fun2 " , msg)

    async def getServiceURL(self, serviceName):
        servicePortMapping = json.load(open("ServiceURLMapping.json"))
        return servicePortMapping[serviceName]

    async def ConfigureAPIRoutes(self):
        @self.httpServer.app.post("/Events/CreateNewEvent")
        async def create_new_event(
            IMAGE: UploadFile = Form(...),  
            EVENT_INFO: str = Form(...)
        ):
            serviceName = "MONGO_DB_SERVICE"
            serviceURL = await self.getServiceURL(serviceName)

            eventID = None

            EVENT_INFO = json.loads(EVENT_INFO)

            async with httpx.AsyncClient() as client:
                EVENT_INFO["IMAGE"] = "https://images.unsplash.com/photo-1542751371-adc38448a05e?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80"

                response = await client.post(f"http://{serviceURL}/Events/CreateNewEvent", json=EVENT_INFO)
                responseInJson = response.json()

                eventID = responseInJson["EVENT_ID"]

            
            print("Event ID : ", eventID)

            if IMAGE != None:
                serviceName = "BLOB_STORAGE_SERVICE"
                serviceURL = await self.getServiceURL(serviceName)

                files = {
                    "EVENT_BANNER": (IMAGE.filename, await IMAGE.read(), IMAGE.content_type),
                }
                data = {
                    "EVENT_ID": str(eventID)
                }

                async with httpx.AsyncClient() as client:
                    response = await client.post(f"http://{serviceURL}/Event/StoreImage", files=files, data=data)
                    responseInJson = response.json()

                serviceName = "MONGO_DB_SERVICE"
                serviceURL = await self.getServiceURL(serviceName)
     
                data = {
                    "EVENT_ID" : str(eventID),
                    "EVENT_BANNER" : f"http://{self.serverIPAddress}:15000/Image/RetrieveImage?bucket=event-banner&key={eventID}.jpg"
                }

                async with httpx.AsyncClient() as client:
                    response = await client.put(f"http://{serviceURL}/Events/Update/EventBanner", json=data)
                    responseInJson = response.json()

                print("Response from MongoDB Service: ", responseInJson)


            return {"EVENT_ID" : eventID}

        @self.httpServer.app.get("/Events/AllEvents")
        async def get_all_events():
            serviceName = "MONGO_DB_SERVICE"
            serviceURL = await self.getServiceURL(serviceName)

            async with httpx.AsyncClient() as client:
                response = await client.get(f"http://{serviceURL}/Events/AllEvents")
                responseInJson = response.json()

            return responseInJson

        @self.httpServer.app.get("/Events/GetEventInfo")
        async def get_event_info(
            EVENT_ID: str,
        ):

            serviceName = "MONGO_DB_SERVICE"
            serviceURL = await self.getServiceURL(serviceName)

            async with httpx.AsyncClient() as client:
                response = await client.get(f"http://{serviceURL}/Events/GetEventInfo?EVENT_ID={EVENT_ID}")
                responseInJson = response.json()

            if responseInJson["EVENT_ID"] == None:
                raise HTTPException(status_code=404, detail="Event not found")

            return responseInJson

        @self.httpServer.app.get("/Events/Organized/User/AllEvents")
        async def get_all_organized_events(
            USER_ID: str,
            request: Request
        ):
            serviceName = "MONGO_DB_SERVICE"
            serviceURL = await self.getServiceURL(serviceName)

            async with httpx.AsyncClient() as client:
                response = await client.get(f"http://{serviceURL}/Events/GetEventInfo?USER_ID={USER_ID}")
                responseInJson = response.json()

            if responseInJson["EVENT_ID"] == None:
                raise HTTPException(status_code=404, detail="Event not found")

            return responseInJson

        @self.httpServer.app.delete("/Events/DeleteEvent")
        async def delete_event(
            EVENT_ID: str,
        ):
            serviceName = "MONGO_DB_SERVICE"
            serviceURL = await self.getServiceURL(serviceName)

            async with httpx.AsyncClient() as client:
                response = await client.delete(f"http://{serviceURL}/Events/DeleteEvent?EVENT_ID={EVENT_ID}")
                responseInJson = response.json()

            if responseInJson["EVENT_ID"] == None:
                raise HTTPException(status_code=404, detail="Event not found")

            return responseInJson

        @self.httpServer.app.post("/Events/Discussion/AddNewQuestion")
        async def add_new_question(
            EVENT_ID: str,
            QUESTION: str,
        ):
            serviceName = "MONGO_DB_SERVICE"
            serviceURL = await self.getServiceURL(serviceName)

            async with httpx.AsyncClient() as client:
                response = await client.post(f"http://{serviceURL}/Events/Discussion/AddNewQuestion?EVENT_ID={EVENT_ID}&QUESTION={QUESTION}")
                responseInJson = response.json()

            if responseInJson["EVENT_ID"] == None:
                raise HTTPException(status_code=404, detail="Event not found")

            return responseInJson

        @self.httpServer.app.get("/Events/Organizer/GetEventInfo")
        async def get_organizer_specific_event_info(
            EVENT_ID: str,
        ):

            serviceName = "MONGO_DB_SERVICE"
            serviceURL = await self.getServiceURL(serviceName)

            async with httpx.AsyncClient() as client:
                response = await client.get(f"http://{serviceURL}/Events/Organizer/GetEventInfo?EVENT_ID={EVENT_ID}")
                responseInJson = response.json()

            if responseInJson.get("EVENT_ID") is None:
                raise HTTPException(status_code=404, detail="Event not found")

            return responseInJson

    async def startService(self):
        # await self.messageQueue.InitializeConnection()
        # await self.messageQueue.AddQueueAndMapToCallback("queue1", self.fun1)
        # await self.messageQueue.AddQueueAndMapToCallback("queue2", self.fun2)
        # await self.messageQueue.StartListeningToQueue()

        await self.ConfigureAPIRoutes()
        await self.httpServer.run_app()

        
async def start_service():
    service = Service('0.0.0.0', 13000)
    await service.startService()

if __name__ == "__main__":
    asyncio.run(start_service())
