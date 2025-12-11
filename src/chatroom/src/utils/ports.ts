import dgram from "dgram";

export function getFreeUdpPort(): Promise<number> {
  return new Promise((resolve, reject) => {
    const socket = dgram.createSocket("udp4");

    socket.on("error", (err) => {
      socket.close();
      reject(err);
    });

    socket.bind(0, () => {
      const port = socket.address().port;
      socket.close(() => resolve(port));
    });
  });
}
