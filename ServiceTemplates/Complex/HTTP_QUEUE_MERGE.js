// Adjust the import paths according to your file structure. Here we assume:
// - `HTTPServer.js` and `MessageQueue.js` are in a folder called `ServiceTemplates/Basic`.
const HTTPServer = require('./ServiceTemplates/Basic/HTTPServer');
const MessageQueue = require('./ServiceTemplates/Basic/MessageQueue');

class Service {
  constructor(httpServerHost, httpServerPort) {
    // Create a new MessageQueue instance. The exchange name here is "/"
    // to mimic the Python code.
    this.messageQueue = new MessageQueue("amqp://guest:guest@localhost/", "/");
    // Create an HTTPServer instance that wraps an Express app.
    this.httpServer = new HTTPServer(httpServerHost, httpServerPort);
  }

  // Callback function for messages on queue1.
  async fun1(message) {
    const msg = message.content.toString();
    console.log("Fun1", msg);
  }

  // Callback function for messages on queue2.
  async fun2(message) {
    const msg = message.content.toString();
    console.log("Fun2", msg);
  }

  // Configure the API route for the HTTP server.
  async ConfigureAPIRoutes() {
    this.httpServer.app.get("/", async (req, res) => {
      console.log("Running Through Someone Else");
      res.json({ message: "Hello World" });
    });
  }

  // Start the service by initializing the message queue, mapping callbacks,
  // starting to consume messages, setting up API routes, and running the HTTP server.
  async startService() {
    await this.messageQueue.InitializeConnection();
    // Bind the methods to the current instance to preserve context.
    await this.messageQueue.AddQueueAndMapToCallback("queue1", this.fun1.bind(this));
    await this.messageQueue.AddQueueAndMapToCallback("queue2", this.fun2.bind(this));
    await this.messageQueue.StartListeningToQueue();

    await this.ConfigureAPIRoutes();
    await this.httpServer.run_app();
  }
}

// An async function to instantiate and start the service.
async function start_service() {
  const service = new Service('127.0.0.1', 8000);
  await service.startService();
}

// Start the service and catch any errors.
start_service().catch(error => {
  console.error("Error starting service:", error);
});
