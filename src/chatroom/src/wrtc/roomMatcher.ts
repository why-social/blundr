import { WebSocketServer } from "ws";
import { Server } from "http";

type Client = {
  ws: WebSocket;
  clientId: string;
};

let wss: WebSocketServer;

let waiting: Client[] = [];
let ready: Client[] = [];

let sessionId = crypto.randomUUID();

export function init(
  server: Server,
  onMatch: (sessionId: string, clients: string[]) => void
) {
  wss = new WebSocketServer({ server });

  wss.on("connection", (ws: WebSocket) => {
    const clientId = crypto.randomUUID();
    const client: Client = { ws, clientId };

    ws.send(JSON.stringify({ type: "id", clientId }));

    waiting.push(client);

    // when client finishes the setup, it sends a "ready" message back
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);

      if (message.type === "ready") {
        waiting = waiting.filter(
          (waitingClient) => waitingClient.clientId !== client.clientId
        );

        ready.push(client);

        while (ready.length >= 2) {
          const a = ready.shift() as Client;
          const b = ready.shift() as Client;

          const targetSessionId = sessionId;
          sessionId = crypto.randomUUID();

          a.ws.send(
            JSON.stringify({
              type: "match",
              data: { clientId: b.clientId, sessionId: targetSessionId },
            })
          );

          b.ws.send(
            JSON.stringify({
              type: "match",
              data: { clientId: a.clientId, sessionId: targetSessionId },
            })
          );

          onMatch(targetSessionId, [a.clientId, b.clientId]);
        }
      }
    };
  });
}
