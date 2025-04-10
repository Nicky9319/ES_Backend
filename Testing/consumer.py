import aio_pika
import asyncio

async def callback(message: aio_pika.IncomingMessage):
    async with message.process():
        print(f"Headers: {message.headers}")
        print(f"Message Received")

async def start_consuming(exchange_name, queue_name, **queue_args):
    # Establish a connection to RabbitMQ server
    connection = await aio_pika.connect_robust("amqp://guest:guest@localhost/")
    async with connection:
        channel = await connection.channel()

        # Declare the exchange
        await channel.declare_exchange(exchange_name, aio_pika.ExchangeType.DIRECT)

        # Declare the queue
        queue = await channel.declare_queue(queue_name, **queue_args)

        # Bind the queue to the exchange
        await queue.bind(exchange_name, routing_key=queue_name)

        # Start consuming messages
        await queue.consume(callback, no_ack=False)

        print(f"Waiting for messages in {queue_name}. To exit press CTRL+C")
        await asyncio.Future()  # Run forever

# Example usage
async def main():
    # Mention the Exchange Name
    exchange_name = "LOGGING_EXCHANGE"

    # Mention the Queue Name
    queue_name = "LE_MAIN_SERVER"
    
    await start_consuming(exchange_name, queue_name, auto_delete=True)

if __name__ == "__main__":
    asyncio.run(main())