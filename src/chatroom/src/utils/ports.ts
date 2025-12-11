import dgram from "dgram";

export function getFreeUdpPort(
  options: {
    evenOnly?: boolean;
  } = {}
): Promise<number> {
  const { evenOnly = false } = options;

  return new Promise((resolve, reject) => {
    const tryBind = () => {
      const socket = dgram.createSocket("udp4");

      socket.on("error", (err) => {
        socket.close();

        reject(err);
      });

      socket.bind(0, () => {
        const port = socket.address().port;

        if (evenOnly && port % 2 !== 0) {
          socket.close(() => {
            tryBind();
          });

          return;
        }

        socket.close(() => resolve(port));
      });
    };

    tryBind();
  });
}
