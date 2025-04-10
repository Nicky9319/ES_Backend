const amqp = require('amqplib');

class MessageQueue {
  constructor(ConnectionURL = "amqp://guest:guest@localhost/", ExchangeName = "/") {
    this.ExchangeName = ExchangeName;
    this.ConnectionURL = ConnectionURL;
    this.Connection = null;
    this.Channel = null;
    this.QueueList = []; // We'll store the queue names here.
    this.QueueToCallbackMapping = {};  
    this.DeclaredExchanges = {};
  }

  async InitializeConnection() {
    // Connect to the RabbitMQ server
    this.Connection = await amqp.connect(this.ConnectionURL);
    this.Channel = await this.Connection.createChannel();

    // Declare the exchange if provided.
    // (If ExchangeName is empty, you might be using the default exchange.)
    if (this.ExchangeName) {
      await this.Channel.assertExchange(this.ExchangeName, 'direct', { durable: true });
    }
  }

  async BoundQueueToExchange() {
    // Bind each queue to the exchange using the queue name as the routing key.
    for (const queueName of this.QueueList) {
      await this.Channel.bindQueue(queueName, this.ExchangeName, queueName);
    }
  }

  async AddNewQueue(QueueName, queueParams = {}) {
    // Declare a new queue and store its name.
    const q = await this.Channel.assertQueue(QueueName, queueParams);
    // The actual queue name is available in q.queue.
    this.QueueList.push(q.queue);
  }

  async MapQueueToCallback(QueueName, Callback) {
    this.QueueToCallbackMapping[QueueName] = Callback;
  }

  async AddQueueAndMapToCallback(QueueName, Callback, queueParams = {}) {
    await this.AddNewQueue(QueueName, queueParams);
    await this.MapQueueToCallback(QueueName, Callback);
  }

  async StartListeningToQueue() {
    // For each queue, start consuming messages with the associated callback.
    for (const queueName of this.QueueList) {
      await this.Channel.consume(queueName, async (msg) => {
        if (msg !== null) {
          try {
            // Invoke the callback for this queue.
            await this.QueueToCallbackMapping[queueName](msg);
            // Acknowledge the message after processing.
            this.Channel.ack(msg);
          } catch (error) {
            console.error("Error processing message:", error);
            // Optionally, use nack() to reject the message.
            this.Channel.nack(msg, false, false);
          }
        }
      });
    }
  }

  async PublishMessage(exchangeName, routingKey, message, headers = {}) {
    let exchange;
    if (!this.DeclaredExchanges.hasOwnProperty(exchangeName)) {
      // Declare the exchange with 'direct' type by default.
      exchange = await this.Channel.assertExchange(exchangeName, 'direct', { durable: true });
      this.DeclaredExchanges[exchangeName] = exchange;
    } else {
      exchange = this.DeclaredExchanges[exchangeName];
    }

    // Prepare the message body.
    let messageToSend;
    if (headers && headers.DATA_FORMAT) {
      if (headers.DATA_FORMAT === "BYTES") {
        console.log("Bytes");
        // Assume message is already a Buffer.
        messageToSend = message;
      } else {
        messageToSend = Buffer.from(message);
      }
    } else {
      messageToSend = Buffer.from(message);
    }

    // Publish the message to the specified exchange and routing key.
    this.Channel.publish(exchangeName, routingKey, messageToSend, { headers });
  }

  async CloseConnection() {
    await this.Connection.close();
  }
}

// --- Example usage (analogous to your Python main() function) ---

async function main() {
  // Callback function that parses the message as JSON.
  async function fun1(msg) {
    const content = msg.content.toString();
    try {
      console.log(JSON.parse(content));
    } catch (error) {
      console.error("Failed to parse JSON:", error);
    }
  }

  // Callback function that prints the message as a string.
  async function fun2(msg) {
    const content = msg.content.toString();
    console.log(content);
  }

  // Create a MessageQueue instance.
  const messageQueue = new MessageQueue("amqp://guest:guest@localhost/", "");
  await messageQueue.InitializeConnection();

  // Add queues and map them to callbacks.
  await messageQueue.AddQueueAndMapToCallback("queue1", fun1);
  await messageQueue.AddQueueAndMapToCallback("queue2", fun2);

  // Start consuming messages.
  await messageQueue.StartListeningToQueue();

  // Optionally, bind queues to an exchange if needed.
  // await messageQueue.BoundQueueToExchange();
}

// Execute the main function.
main().catch(error => {
  console.error("Error in main:", error);
});
