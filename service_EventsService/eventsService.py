import asyncio
from fastapi import FastAPI, Response, Request, Form, UploadFile
import uvicorn

import asyncio
import aio_pika

import json
import httpx

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "../ServiceTemplates/Basic"))


from HTTP_SERVER import HTTPServer
from MESSAGE_QUEUE import MessageQueue

class Service():
    def __init__(self,httpServerHost, httpServerPort):
        self.messageQueue = MessageQueue("amqp://guest:guest@localhost/","/")
        self.httpServer = HTTPServer(httpServerHost, httpServerPort)

    # async def fun1(self, message: aio_pika.IncomingMessage):
    #     msg = message.body.decode()
    #     print("Fun1 " , msg)
    
    # async def fun2(self, message: aio_pika.IncomingMessage):
    #     msg = message.body.decode()
    #     print("Fun2 " , msg)


    async def ConfigureAPIRoutes(self):
        @self.httpServer.app.get("/Events/CreateNewEvent")
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
     
                data = {
                    "EVENT_ID" : str(eventID),
                    "EVENT_BANNER" : f"http://{self.serverIPAddress}:15000/Image/RetrieveImage?bucket=event-banner&key={eventID}.jpg"
                }

                async with httpx.AsyncClient() as client:
                    response = await client.put(f"http://{serviceURL}/Events/Update/EventBanner", json=data)
                    responseInJson = response.json()

                print("Response from MongoDB Service: ", responseInJson)


            return {"EVENT_ID" : eventID}

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
