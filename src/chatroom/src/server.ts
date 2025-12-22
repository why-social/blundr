import express from "express";
import https from "https";
import http from "http";

import config from "./config.js";
import routes from "./routes.js";

import { init } from "./wrtc/mediasoup.js";
import errorHandler from "./middleware/errorHandler.js";
import cors from "./middleware/cors.js";
import { readFileSync } from "fs";
import { logInfo, logWarn } from "./utils/logs.js";

const app = express();

app.use(cors);
app.use(express.json());
app.use("/", routes);
app.use(errorHandler);

let server;

try {
  const options = {
    key: readFileSync("/etc/tls/privkey.pem"),
    cert: readFileSync("/etc/tls/fullchain.pem"),
  };
  server = https.createServer(options, app);

  logInfo("HTTPS server created");
} catch (error) {
  logWarn("Certificates not found, falling back to HTTP");

  server = http.createServer(app);
}

init(server);

server.listen(config.port, () => {
  logInfo(`Server running on port ${config.port}`);
});
