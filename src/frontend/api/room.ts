export type WSHandler = {
  onConnected: (clientId: string) => Promise<void>;
  onMatch: (clientId: string, sessionId: string) => Promise<void>;
  onPeerLeft: () => void;
};

export function init(handler: WSHandler) {
  const WS_URL = process.env.NEXT_PUBLIC_CHATROOM_WS_URL;

  if (!WS_URL) {
    throw Error("NEXT_PUBLIC_CHATROOM_WS_URL is not provided.");
  }

  const ws = new WebSocket(WS_URL);

  const cleanup = () => {
    ws.onmessage = null;

    if (
      ws.readyState === WebSocket.OPEN ||
      ws.readyState === WebSocket.CONNECTING
    ) {
      ws.close();
    }
  };

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

        break;
      }

      case "peer-left": {
        handler.onPeerLeft();
        cleanup();

        break;
      }
    }
  };

  return cleanup;
}
