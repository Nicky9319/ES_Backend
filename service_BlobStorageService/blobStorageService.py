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
        @self.httpServer.app.post("/UserProfilePic/StoreImage")
        async def user_profile_pic_storeImage(
            PROFILE_PIC: UploadFile = Form(...),
            USER_ID: str = Form(...),
        ):
            print(PROFILE_PIC)
            print(USER_ID)
            await self.uploadImageToBlobStorage(PROFILE_PIC, "user-profile-pic", USER_ID + ".jpg")
            print("Received the User ID and the Profile Pic")
            return {"message": "Image uploaded successfully"}
    
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
