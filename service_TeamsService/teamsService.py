import asyncio
from fastapi import FastAPI, Response, Request, Form, UploadFile
import uvicorn

import asyncio
import aio_pika

import json
import httpx

import sys
import os

from dotenv import load_dotenv
load_dotenv()

from fastapi.middleware.cors import CORSMiddleware

sys.path.append(os.path.join(os.path.dirname(__file__), "../ServiceTemplates/Basic"))


from HTTP_SERVER import HTTPServer
from MESSAGE_QUEUE import MessageQueue

class Service():
    def __init__(self,httpServerHost, httpServerPort):
        self.messageQueue = MessageQueue("amqp://guest:guest@localhost/","/")
        self.httpServer = HTTPServer(httpServerHost, httpServerPort)

        self.httpServer.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

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
        @self.httpServer.app.post("/Teams/CreateNewTeam")
        async def create_new_team(
            TEAM_LOGO : UploadFile = Form(...),
            TEAM_INFO : str = Form(...)
        ):
            serviceName = "MONGO_DB_SERVICE"
            serviceURL = await self.getServiceURL(serviceName)

            teamID = None

            TEAM_INFO = json.loads(TEAM_INFO)

            async with httpx.AsyncClient() as client:
                TEAM_INFO["TEAM_LOGO"] = "https://images.unsplash.com/photo-1542751371-adc38448a05e?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80"

                response = await client.post(f"http://{serviceURL}/Teams/CreateNewTeam", json=TEAM_INFO)
                responseInJson = response.json()

                teamID = responseInJson["TEAM_ID"]

            
            print("Team ID : ", teamID)

            if TEAM_LOGO != None:
                serviceName = "BLOB_STORAGE_SERVICE"
                serviceURL = await self.getServiceURL(serviceName)

                files = {
                    "TEAM_LOGO": (TEAM_LOGO.filename, await TEAM_LOGO.read(), TEAM_LOGO.content_type),
                }
                data = {
                    "TEAM_ID": str(teamID)
                }

                async with httpx.AsyncClient() as client:
                    response = await client.post(f"http://{serviceURL}/Team/StoreImage", files=files, data=data)
                    responseInJson = response.json()

                serviceName = "MONGO_DB_SERVICE"
                serviceURL = await self.getServiceURL(serviceName)
            
                data = {
                    "TEAM_ID" : str(teamID),
                    "TEAM_LOGO" : f"http://{self.httpServer.host}:15000/Image/RetrieveImage?bucket=team-logos&key={teamID}.jpg"
                }

                async with httpx.AsyncClient() as client:
                    response = await client.put(f"http://{serviceURL}/Teams/Update/TeamLogo", json=data)
                    responseInJson = response.json()

                print("Response from MongoDB Service: ", responseInJson)


            return {"TEAM_ID" : teamID}
    
        @self.httpServer.app.get("/Teams/User/GetAllTeams")
        async def get_all_teams_for_a_user(
            USER_ID: str,
            request: Request
        ):
            serviceName = "MONGO_DB_SERVICE"
            serviceURL = await self.getServiceURL(serviceName)

            async with httpx.AsyncClient() as client:
                response = await client.get(f"http://{serviceURL}/Teams/User/GetAllTeams?USER_ID={USER_ID}")
                responseInJson = response.json()

            print("Response from MongoDB Service: ", responseInJson)

            return responseInJson

    async def startService(self):
        # await self.messageQueue.InitializeConnection()
        # await self.messageQueue.AddQueueAndMapToCallback("queue1", self.fun1)
        # await self.messageQueue.AddQueueAndMapToCallback("queue2", self.fun2)
        # await self.messageQueue.StartListeningToQueue()

        await self.ConfigureAPIRoutes()
        await self.httpServer.run_app()

        
async def start_service():
    service = Service('0.0.0.0', 17000)
    await service.startService()

if __name__ == "__main__":
    asyncio.run(start_service())
