import { WebSocketServer } from "ws";
import { Server } from "http";

type Client = {
  ws: WebSocket;
  clientId: string;
};

let wss: WebSocketServer;

let waiting: Client[] = [];
let ready: Client[] = [];

const activeSessions = new Map<string, { a: Client; b: Client }>();

let sessionId = crypto.randomUUID();

export function init(
  server: Server,
  onMatch: (sessionId: string, clients: string[]) => void,
  onClose: (clientId: string) => void
) {
  wss = new WebSocketServer({ server });

  wss.on("connection", (ws: WebSocket) => {
    const clientId = crypto.randomUUID();
    const client: Client = { ws, clientId };

    ws.send(JSON.stringify({ type: "id", clientId }));
    waiting.push(client);

    ws.onclose = () => {
      waiting = waiting.filter((client) => client.clientId !== clientId);
      ready = ready.filter((client) => client.clientId !== clientId);

      onClose(clientId);

      for (const [sessionId, { a, b }] of activeSessions.entries()) {
        if (a.clientId === clientId || b.clientId === clientId) {
          const otherClient = a.clientId === clientId ? b : a;

          if (otherClient.ws.readyState === WebSocket.OPEN) {
            otherClient.ws.send(JSON.stringify({ type: "peer-left" }));
          }

          activeSessions.delete(sessionId);

          break;
        }
      }
    };

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

          activeSessions.set(targetSessionId, { a, b });

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
