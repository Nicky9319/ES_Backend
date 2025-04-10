const express = require('express');

class HTTPServer {
  constructor(host = "127.0.0.1", port = 54545) {
    this.app = express();
    this.host = host;
    this.port = port;
  }

  async run_app() {
    // Wrap the listen method in a promise so it behaves asynchronously.
    return new Promise((resolve, reject) => {
      this.server = this.app.listen(this.port, this.host, () => {
        console.log(`Server running on http://${this.host}:${this.port}`);
        resolve();
      });
      // Optional: handle server errors
      this.server.on('error', (err) => {
        console.error("Server error:", err);
        reject(err);
      });
    });
  }
}

class MainServer {
  constructor(httpServerHost, httpServerPort) {
    this.fast = new HTTPServer(httpServerHost, httpServerPort);
  }

  // Define the routes similar to FastAPI route decorators.
  ConfigureServerRoutes() {
    this.fast.app.get("/", async (req, res) => {
      console.log("Running Through Someone Else");
      res.json({ message: "Hello World" });
    });
  }

  async RunServer() {
    this.ConfigureServerRoutes();
    await this.fast.run_app();
  }
}

// Async function to start the server.
async function start_server() {
  const server = new MainServer('127.0.0.1', 8000);
  await server.RunServer();
}

// Start the server.
start_server().catch(err => {
  console.error("Failed to start server:", err);
});
