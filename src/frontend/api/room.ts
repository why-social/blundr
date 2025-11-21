let ws: WebSocket;

export type WSHandler = {
  onConnected: (clientId: string) => Promise<void>;
  onMatch: (clientId: string, sessionId: string) => Promise<void>;
};

export function init(handler: WSHandler) {
  const WS_URL = process.env.NEXT_PUBLIC_WS_URL;

  if (!WS_URL) {
    console.error("NEXT_PUBLIC_WS_URL is not provided.");
    process.exit(1);
  }

  ws = new WebSocket(WS_URL);

  ws.onmessage = async (event) => {
    const message = JSON.parse(event.data);

    switch (message.type) {
      case "id": {
        await handler.onConnected(message.clientId);

        ws.send(
          JSON.stringify({
            type: "ready",
            clientId: message.clientId,
          }),
        );

        break;
      }
      case "match": {
        await handler.onMatch(message.data.clientId, message.data.sessionId);
        ws.close();

        break;
      }
    }
  };

  return ws;
}

export const send = (message: string) => ws.send(JSON.stringify(message));
