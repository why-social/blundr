import dgram from "dgram";

export function getFreeUdpPort(): Promise<number> {
  return new Promise((resolve, reject) => {
    const socket = dgram.createSocket("udp4");

    socket.bind(0, () => {
      const port = socket.address().port;
      socket.close(() => resolve(port));
    });

    socket.on("error", reject);
  });
}
