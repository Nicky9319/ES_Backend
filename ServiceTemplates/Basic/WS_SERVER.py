import socketio
from aiohttp import web
import asyncio

# This is Template for a Class that has the Base WS class as an object and All the Routes and end points for the WS Server Are Defined Here
class MainServer:
    def __init__(self, wsServerHost , wsServerPort):
        self.wsServer = WebSocketServer(wsServerHost, wsServerPort)

    def ConfigureServerRoutes(self):
        @self.wsServer.sio.event
        async def connect(sid, environ , auth=None):
            print(f"A New User with ID {sid} Connected")

    
        @self.wsServer.sio.event
        async def disconnect(sid):
            print(f'Client {sid} disconnected')
        
        
        @self.wsServer.sio.on("GET_SID")
        async def get_sid(sid):
            return sid

    async def RunServer(self):
        self.ConfigureServerRoutes()
        await self.wsServer.start()

# This is the Base Class Which can be Called to Setup a WebSocket Server
class WebSocketServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sio = socketio.AsyncServer()
        self.app = web.Application()
        self.sio.attach(self.app)

    async def start(self):
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, host=self.host, port=self.port)
        await site.start()
        print(f"Server started at http://{self.host}:{self.port}")

async def main():
    server = MainServer('localhost', 6000)
    await server.RunServer()

# if __name__ == '__main__':
#     asyncio.run(main())