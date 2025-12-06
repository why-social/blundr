import express from "express";
import http from "http";

import config from "./config.js";
import routes from "./routes.js";

import { init } from "./wrtc/mediasoup.js";
import errorHandler from "./middleware/errorHandler.js";
import cors from "./middleware/cors.js";

const app = express();

app.use(cors);
app.use(express.json());
app.use("/", routes);
app.use(errorHandler);

const server = http.createServer(app);
init(server);

server.listen(config.port, () => {
  console.log(`Server running on port ${config.port}`);
});
