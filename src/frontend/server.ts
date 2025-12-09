import express from "express";
import type { Request, Response } from "express";
import { createProxyMiddleware } from "http-proxy-middleware";
import { createServer, IncomingMessage } from "http";
import next from "next";
import { Socket } from "net";

const dev = process.env.NODE_ENV !== "production";
const app = next({ dev });
const handle = app.getRequestHandler();

app.prepare().then(() => {
  const server = express();

  const wsProxy = createProxyMiddleware({
    target: process.env.CHATROOM_WS_URL,
    changeOrigin: true,
    ws: true,
    pathRewrite: { "^/ws": "" },
    secure: false,
  });

  server.use("/ws", wsProxy);

  server.all(/.*/, (req: Request, res: Response) => {
    return handle(req, res);
  });

  const httpServer = createServer(server);

  httpServer.on(
    "upgrade",
    (req: IncomingMessage, socket: Socket, head: Buffer) => {
      if (req.url?.startsWith("/ws")) {
        wsProxy.upgrade(req, socket, head);
      }
    },
  );

  const PORT = process.env.PORT || 3000;
  httpServer.listen(PORT, () => {
    console.log(`Next.js server running on port ${PORT}.`);
  });
});
