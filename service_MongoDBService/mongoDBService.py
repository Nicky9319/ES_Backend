import asyncio
from fastapi import FastAPI, Response, Request
import uvicorn

import asyncio
import aio_pika


import sys
import os

# Import necessary MongoDB modules
from pymongo import MongoClient
from pymongo.server_api import ServerApi

sys.path.append(os.path.join(os.path.dirname(__file__), "../ServiceTemplates/Basic"))


from HTTP_SERVER import HTTPServer
from MESSAGE_QUEUE import MessageQueue


class Service():
    def __init__(self,httpServerHost, httpServerPort):
        self.messageQueue = MessageQueue("amqp://guest:guest@localhost/","/")
        self.httpServer = HTTPServer(httpServerHost, httpServerPort)
        
        # MongoDB Configuration
        self.mongo_client = MongoClient('mongodb://localhost:27017/', server_api=ServerApi('1'))
        self.db = self.mongo_client["ES"]  # Database name from MongoSchema.json
        self.event_collection = self.db["EVENTS"]  # Collection name from MongoSchema.json

    async def fun1(self, message: aio_pika.IncomingMessage):
        msg = message.body.decode()
        print("Fun1 " , msg)
    
    async def fun2(self, message: aio_pika.IncomingMessage):
        msg = message.body.decode()
        print("Fun2 " , msg)

    async def ConfigureAPIRoutes(self):

        @self.httpServer.app.get("/Events/AllEvents")
        async def get_event():
            print("Fetching All Events")
            events = list(self.event_collection.find({}, {'_id': 0}))  # Fetch all events, exclude _id
            return {"EVENTS": events}
    
        @self.httpServer.app.post("/Events/InsertEvent")
        async def insert_event(request: Request):
            try:
                event_data = await request.json()
                print("Inserting Event", event_data)
                self.event_collection.insert_one(event_data)
                return {"message": "Event inserted successfully"}
            except Exception as e:
                return {"message": f"Error inserting event: {str(e)}"}
            
        @self.httpServer.app.put("/Events/Update")
        async def update_event(request: Request):
            try:
                event_data = await request.json()
                print("Updating Event", event_data)
                self.event_collection.update_one({"event_id": event_data["event_id"]}, {"$set": event_data})
                return {"message": "Event updated successfully"}
            except Exception as e:
                return {"message": f"Error updating event: {str(e)}"}
    

    async def startService(self):
        await self.messageQueue.InitializeConnection()
        await self.messageQueue.AddQueueAndMapToCallback("queue1", self.fun1)
        await self.messageQueue.AddQueueAndMapToCallback("queue2", self.fun2)
        await self.messageQueue.StartListeningToQueue()

        await self.ConfigureAPIRoutes()
        await self.httpServer.run_app()

        
async def start_service():
    service = Service('0.0.0.0', 14000)
    await service.startService()

if __name__ == "__main__":
    asyncio.run(start_service())
