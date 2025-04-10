import asyncio
from fastapi import FastAPI
import uvicorn




# This is Template for a Class that has the Base HTTP class as an object and All the Routes and end points for the HTTP Server Are Defined Here
class MainServer:
    def __init__(self, httpServerHost, httpServerPort):
        self.fast = HTTPServer(httpServerHost, httpServerPort)

    # Define the Routes for the Particular Case
    def ConfigureServerRoutes(self):

        @self.fast.app.get("/")
        async def read_root():
            print("Running Through Someone Else")
            return {"message": "Hello World"}
    
    async def RunServer(self):
        self.ConfigureServerRoutes()
        await self.fast.run_app()


# This is the Base Class Which can be Called to Setup a HTTP Server
class HTTPServer:
    def __init__(self, host="127.0.0.1", port=54545):
        self.app = FastAPI()
        self.host = host
        self.port = port

    async def run_app(self):
        config = uvicorn.Config(self.app, host=self.host, port=self.port)
        server = uvicorn.Server(config)
        await server.serve()


async def start_server():
    server = MainServer('127.0.0.1', 8000)
    await server.RunServer()
    pass

# if __name__ == "__main__":
#     import asyncio
#     asyncio.run(start_server())