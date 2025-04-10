import asyncio
import aio_pika

import json

import time

class MessageQueue:
    def __init__(self, ConnectionURL="amqp://guest:guest@localhost/", ExchangeName="/"):
        self.ExchangeName = ExchangeName
        self.ConnectionURL = ConnectionURL
        self.Connection = None
        self.Channel = None
        self.QueueList = []
        self.QueueToCallbackMapping = {}  
        self.DeclaredExchanges = {}


    async def InitializeConnection(self):
        self.Connection = await aio_pika.connect_robust(self.ConnectionURL)
        self.Channel = await self.Connection.channel()
        await self.Channel.declare_exchange(self.ExchangeName, aio_pika.ExchangeType.DIRECT)

    async def BoundQueueToExchange(self):
        for queues in self.QueueList:
            await queues.bind(self.ExchangeName , routing_key=queues.name)
        
    async def AddNewQueue(self, QueueName,**queueParams):
        queue = await self.Channel.declare_queue(QueueName, **queueParams)
        self.QueueList.append(queue)
    
    async def MapQueueToCallback(self, QueueName, Callback):
        self.QueueToCallbackMapping[QueueName] = Callback

    async def AddQueueAndMapToCallback(self, QueueName, Callback,**queueParams):
        await self.AddNewQueue(QueueName,**queueParams)
        await self.MapQueueToCallback(QueueName, Callback)

    async def StartListeningToQueue(self):
        for queue in self.QueueList:
            await queue.consume(self.QueueToCallbackMapping[queue.name])

    async def PublishMessage(self, exchangeName , routingKey, message, headers=None):
        exchange = None
        if exchangeName not in self.DeclaredExchanges.keys():
            exchange = await self.Channel.declare_exchange(exchangeName)
            self.DeclaredExchanges[exchangeName] = exchange
        else:
            exchange = self.DeclaredExchanges[exchangeName]


        messageToSend = None
        if headers and "DATA_FORMAT" in headers:
            if headers["DATA_FORMAT"] == "BYTES":
                print("Bytes")
                messageToSend = message
            else:
                messageToSend = message.encode()
        else:
            messageToSend = message.encode()


        await exchange.publish(
            aio_pika.Message(body=messageToSend,headers=headers),
            routing_key=routingKey
        )

    async def CloseConnection(self):
        await self.Connection.close()





async def main():

    async def fun1(message: aio_pika.IncomingMessage):
        msg = message.body.decode()
        print(json.loads(msg))

    async def fun2(message: aio_pika.IncomingMessage):
        msg = message.body.decode()
        print(msg)


    messageQueue = MessageQueue("amqp://guest:guest@localhost/", "")
    await messageQueue.InitializeConnection()
    await messageQueue.AddQueueAndMapToCallback("queue1", fun1)
    await messageQueue.AddQueueAndMapToCallback("queue2", fun2)

    await messageQueue.StartListeningToQueue()


# if __name__ == "__main__":
#     asyncio.run(main())

