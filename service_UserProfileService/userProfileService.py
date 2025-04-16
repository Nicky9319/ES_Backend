import asyncio
from fastapi import FastAPI, Response, Request, Form, UploadFile
import uvicorn


import asyncio
import aio_pika


import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "../ServiceTemplates/Basic"))


from HTTP_SERVER import HTTPServer
from MESSAGE_QUEUE import MessageQueue

class Service():
    def __init__(self,httpServerHost, httpServerPort):
        self.messageQueue = MessageQueue("amqp://guest:guest@localhost/","/")
        self.httpServer = HTTPServer(httpServerHost, httpServerPort)

    async def fun1(self, message: aio_pika.IncomingMessage):
        msg = message.body.decode()
        print("Fun1 " , msg)
    
    async def fun2(self, message: aio_pika.IncomingMessage):
        msg = message.body.decode()
        print("Fun2 " , msg)


    async def ConfigureAPIRoutes(self):
        @self.httpServer.app.post("/UserProfile/CreateNewUser")
        async def create_new_user(
            PROFILE_PIC: UploadFile = Form(...), 
            PROFILE_BANNER: UploadFile = Form(...),  
            USER_INFO: str = Form(...)
        ):
            print(PROFILE_PIC)
            print(USER_INFO)
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
