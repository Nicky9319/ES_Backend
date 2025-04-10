import socketio
from aiohttp import web
import asyncio

import asyncio
from fastapi import FastAPI, Response, Request
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
from WS_SERVER import WebSocketServer


class Service:
    def __init__(self, wsServerHost, wsServerPort, httpServerHost, httpServerPort):
        self.messageQueue = MessageQueue("amqp://guest:guest@localhost/","/")
        self.httpServer = HTTPServer(httpServerHost, httpServerPort)
        self.wsServer = WebSocketServer(wsServerHost, wsServerPort)

    async def fun1(self, message: aio_pika.IncomingMessage):
        msg = message.body.decode()
        print("Fun1 " , msg)
    
    async def fun2(self, message: aio_pika.IncomingMessage):
        msg = message.body.decode()
        print("Fun2 " , msg)


    async def ConfigureHTTPserverRoutes(self):
        # @self.httpServer.app.get("/")
        # async def read_root():
        #     print("Running Through Someone Else")
        #     return {"message": "Hello World"}

        pass
    
    async def ConfigureWSserverMethods(self):
        @self.wsServer.sio.event
        async def connect(sid, environ , auth=None):
            print(f"A New User with ID {sid} Connected")

    
        @self.wsServer.sio.event
        async def disconnect(sid):
            print(f'Client {sid} disconnected')
        
        
        @self.wsServer.sio.on("GET_SID")
        async def get_sid(sid):
            return sid
    
    async def startService(self):
        await self.messageQueue.InitializeConnection()
        await self.messageQueue.AddQueueAndMapToCallback("queue1", self.fun1)
        await self.messageQueue.AddQueueAndMapToCallback("queue2", self.fun2)
        await self.messageQueue.BoundQueueToExchange()
        await self.messageQueue.StartListeningToQueue()

        await self.ConfigureWSserverMethods()
        await self.wsServer.start()

        await self.ConfigureHTTPserverRoutes()
        await self.httpServer.run_app()

async def start_service():
    service = Service('127.0.0.1',6000, '127.0.0.1', 8000)
    await service.startService()

if __name__ == "__main__":
    asyncio.run(start_service())