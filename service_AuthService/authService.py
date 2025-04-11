import asyncio
from fastapi import FastAPI, Response, Request
import uvicorn

import asyncio
import aio_pika
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

    async def fun1(self, message: aio_pika.IncomingMessage):
        msg = message.body.decode()
        print("Fun1 " , msg)
    
    async def fun2(self, message: aio_pika.IncomingMessage):
        msg = message.body.decode()
        print("Fun2 " , msg)


    async def ConfigureAPIRoutes(self):
        @self.httpServer.app.get("/Auth/Google")
        async def google_auth(request: Request):
            # Redirect the user to Google's OAuth 2.0 server
            redirect_uri = "http://localhost:5000/Auth/Google/Callback"  # Replace with your actual redirect URI
            client_id = "YOUR_GOOGLE_CLIENT_ID"  # Replace with your Google Client ID
            scope = "openid profile email"  # Add scopes as needed

            google_auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?client_id={client_id}&response_type=code&scope={scope}&redirect_uri={redirect_uri}&state=state"  # Add a state parameter for security

            return Response(status_code=302, headers={"location": google_auth_url})

        @self.httpServer.app.get("/Auth/Google/Callback")
        async def google_auth_callback(request: Request, code: str = None, state: str = None, error: str = None):
            # Handle the callback from Google
            if error:
                return {"error": error}

            if not code:
                return {"error": "Code is missing"}

            # Exchange the code for an access token
            token_url = "https://oauth2.googleapis.com/token"
            client_id = "YOUR_GOOGLE_CLIENT_ID"  # Replace with your Google Client ID
            client_secret = "YOUR_GOOGLE_CLIENT_SECRET"  # Replace with your Google Client Secret
            redirect_uri = "http://localhost:5000/Auth/Google/Callback"  # Replace with your actual redirect URI

            token_data = {
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code"
            }

            async with httpx.AsyncClient() as client:
                token_response = await client.post(token_url, data=token_data)

            token_response.raise_for_status()  # Raise an exception for bad status codes

            token_info = token_response.json()
            access_token = token_info.get("access_token")

            if not access_token:
                return {"error": "Failed to retrieve access token"}

            # Use the access token to get user information
            user_info_url = "https://www.googleapis.com/oauth2/v3/userinfo"
            headers = {"Authorization": f"Bearer {access_token}"}

            async with httpx.AsyncClient() as client:
                user_info_response = await client.get(user_info_url, headers=headers)

            user_info_response.raise_for_status()

            user_info = user_info_response.json()

            # Process the user information (e.g., store it in your database)
            print("User Info:", user_info)

            return {"message": "Authentication successful", "user_info": user_info}
    
        @self.httpServer.app.get("/Auth/Account")
        async def checkAuth(request: Request):
            data = request.json()

            email = data["EMAIL"]
            password = data["PASSWORD"]

            print(data)


    async def startService(self):
        await self.messageQueue.InitializeConnection()
        await self.messageQueue.AddQueueAndMapToCallback("queue1", self.fun1)
        await self.messageQueue.AddQueueAndMapToCallback("queue2", self.fun2)
        await self.messageQueue.StartListeningToQueue()

        await self.ConfigureAPIRoutes()
        await self.httpServer.run_app()

        
async def start_service():
    service = Service('0.0.0.0', 5000)
    await service.startService()

if __name__ == "__main__":
    asyncio.run(start_service())

