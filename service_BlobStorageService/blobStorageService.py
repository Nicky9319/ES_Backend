import asyncio
from fastapi import FastAPI, Response, Request, Form, UploadFile
import uvicorn

import asyncio
import aio_pika


import sys
import os

import boto3
from botocore.client import Config

sys.path.append(os.path.join(os.path.dirname(__file__), "../ServiceTemplates/Basic"))


from HTTP_SERVER import HTTPServer
from MESSAGE_QUEUE import MessageQueue

class Service():
    def __init__(self,httpServerHost, httpServerPort):
        self.messageQueue = MessageQueue("amqp://guest:guest@localhost/","/")
        self.httpServer = HTTPServer(httpServerHost, httpServerPort)

        self.client = boto3.client(
            "s3",
            endpoint_url="http://localhost:3000",
            aws_access_key_id="admin",
            aws_secret_access_key="password",
            config=Config(signature_version="s3v4"),
            region_name="us-east-1"
        )

    async def fun1(self, message: aio_pika.IncomingMessage):
        msg = message.body.decode()
        print("Fun1 " , msg)
    
    async def fun2(self, message: aio_pika.IncomingMessage):
        msg = message.body.decode()
        print("Fun2 " , msg)


    async def uploadImageToBlobStorage(self, image: UploadFile, bucket: str, key: str):
        print(image)
        try:
            contents = await image.read()
            self.client.put_object(Bucket=bucket, Key=key , Body=contents)
            return {"filename": image.filename}
        except Exception as e:
            return {"error": str(e)}
        
    async def retrieveImageFromBlobStorage(self, bucket: str, key: str):
        try:
            response = self.client.get_object(Bucket=bucket, Key=key)
            data = response['Body'].read()
            print(type(data))
            return data
        except Exception as e:
            return {"error": str(e)}

    async def ConfigureAPIRoutes(self):
    
    # User Profile 

        @self.httpServer.app.post("/UserProfilePic/StoreImage")
        async def user_profile_pic_storeImage(
            PROFILE_PIC: UploadFile = Form(...),
            USER_ID: str = Form(...),
        ):
            # print(PROFILE_PIC)
            # print(USER_ID)
            await self.uploadImageToBlobStorage(PROFILE_PIC, "user-profile-pic", USER_ID + ".jpg")
            print("Received the User ID and the Profile Pic")
            return {"message": "Image uploaded successfully"}   
    
        @self.httpServer.app.post("/UserProfileBanner/StoreImage")
        async def user_profile_banner_storeImage(
            PROFILE_BANNER: UploadFile = Form(...),
            USER_ID: str = Form(...),
        ):
            print(PROFILE_BANNER)
            print(USER_ID)
            await self.uploadImageToBlobStorage(PROFILE_BANNER, "user-profile-banner", USER_ID + ".jpg")
            print("Received the User ID and the Profile Banner")
            return {"message": "Image uploaded successfully"}


    # Mentor Profile

        @self.httpServer.app.post("/MentorProfilePic/StoreImage")
        async def mentor_profile_pic_storeImage(
            PROFILE_PIC: UploadFile = Form(...),
            MENTOR_ID: str = Form(...),
        ):
            print(PROFILE_PIC)
            print(MENTOR_ID)
            await self.uploadImageToBlobStorage(PROFILE_PIC, "mentor-profile-pic", MENTOR_ID + ".jpg")
            print("Received the User ID and the Profile Pic")
            return {"message": "Image uploaded successfully"}
        
        @self.httpServer.app.post("/MentorProfileBanner/StoreImage")
        async def mentor_profile_banner_storeImage(
            PROFILE_BANNER: UploadFile = Form(...),
            MENTOR_ID: str = Form(...),
        ):
            print(PROFILE_BANNER)
            print(MENTOR_ID)
            await self.uploadImageToBlobStorage(PROFILE_BANNER, "mentor-profile-banner", MENTOR_ID + ".jpg")
            print("Received the User ID and the Profile Banner")
            return {"message": "Image uploaded successfully"}

    # Team

        @self.httpServer.app.post("/Team/StoreImage")
        async def team_store_logo(
            TEAM_LOGO: UploadFile = Form(...),
            TEAM_ID: str = Form(...),
        ):
            print(TEAM_LOGO)
            print(TEAM_ID)
            await self.uploadImageToBlobStorage(TEAM_LOGO, "team-logo", TEAM_ID + ".jpg")
            print("Received the Team ID and the Team Logo")
            return {"message": "Image uploaded successfully"}


    # Events

        @self.httpServer.app.post("/Event/StoreImage")
        async def event_store_image(
            EVENT_BANNER: UploadFile = Form(...),
            EVENT_ID: str = Form(...),
        ):
            print(EVENT_BANNER)
            print(EVENT_ID)
            await self.uploadImageToBlobStorage(EVENT_BANNER, "event-image", EVENT_ID + ".jpg")
            print("Received the Event ID and the Event Banner")
            return {"message": "Image uploaded successfully"}

    # Retrieve Existing Images
        @self.httpServer.app.get("/Image/RetrieveImage")
        async def retrieve_image(
            bucket: str,
            key: str
        ):
            print(bucket)
            print(key)
            data = await self.retrieveImageFromBlobStorage(bucket, key)
            if isinstance(data, bytes):
                return Response(content=data, media_type="image/jpg")
            else:
                return {"error": data["error"]}


    async def startService(self):
        # await self.messageQueue.InitializeConnection()
        # await self.messageQueue.AddQueueAndMapToCallback("queue1", self.fun1)
        # await self.messageQueue.AddQueueAndMapToCallback("queue2", self.fun2)
        # await self.messageQueue.StartListeningToQueue()

        await self.ConfigureAPIRoutes()
        await self.httpServer.run_app()

        
async def start_service():
    service = Service('0.0.0.0', 15000)
    await service.startService()

if __name__ == "__main__":
    asyncio.run(start_service())
