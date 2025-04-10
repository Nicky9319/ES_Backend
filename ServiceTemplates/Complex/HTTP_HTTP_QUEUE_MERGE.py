from aiohttp import web
import asyncio

import asyncio
from fastapi import FastAPI, Request, Response
import uvicorn

import asyncio
import aio_pika
import json
import time


import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "../ServiceTemplates/Basic"))


from HTTP_SERVER import HTTPServer
from MESSAGE_QUEUE import MessageQueue

class Service:
    def __init__(self, httpServerHost, httpServerPort, apiServerHost, apiServerPort):
        self.messageQueue = MessageQueue("amqp://guest:guest@localhost/","/")
        self.apiServer = HTTPServer(apiServerHost, apiServerPort)
        self.httpServer = HTTPServer(httpServerHost, httpServerPort)

    async def fun1(self, message: aio_pika.IncomingMessage):
        msg = message.body.decode()
        print("Fun1 " , msg)
    
    async def fun2(self, message: aio_pika.IncomingMessage):
        msg = message.body.decode()
        print("Fun2 " , msg)


    async def ConfigureHTTPRoutes(self):
        @self.httpServer.app.get("/")
        async def read_root():
            print("Running Through Someone Else")
            return {"message": "Hello World"}
    
    async def ConfigureAPIRoutes(self):
        @self.apiServer.app.get("/")
        async def read_root():
            print("Running Through Someone Else")
            return {"message": "Hello World"}
    
    async def startService(self):
        await self.messageQueue.InitializeConnection()
        await self.messageQueue.AddQueueAndMapToCallback("queue1", self.fun1)
        await self.messageQueue.AddQueueAndMapToCallback("queue2", self.fun2)
        await self.messageQueue.StartListeningToQueue()

        await self.ConfigureAPIRoutes()
        asyncio.create_task(self.apiServer.run_app())

        await self.ConfigureHTTPRoutes()
        await self.httpServer.run_app()

async def start_service():
    service = Service('127.0.0.1',6000, '127.0.0.1', 8000)
    await service.startService()

if __name__ == "__main__":
    asyncio.run(start_service())