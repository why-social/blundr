import { RefObject, useCallback, useEffect, useRef, useState } from "react";
import { Device } from "mediasoup-client";
import { AppData, Transport } from "mediasoup-client/types";
import {
  getRouterRtpCapabilities,
  createTransport,
  connectTransport,
  resumeConsumer,
  createProducer,
  createConsumer,
} from "@/api/mediasoup";
import { init as initRoomHandler } from "@/api/room";

export function useMediaSoup(
  localVideoRef: RefObject<HTMLVideoElement | null>,
  remoteVideoRef: RefObject<HTMLVideoElement | null>,
  onCallEnd: () => void,
) {
  const clientId = useRef<string | null>(null);
  const sessionId = useRef<string | null>(null);
  const [isQueuing, setQueuing] = useState(true);

  const onCallEndRef = useRef(onCallEnd);
  useEffect(() => {
    onCallEndRef.current = onCallEnd;
  }, [onCallEnd]);

  const setup = useCallback(async () => {
    const stream = await navigator.mediaDevices
      .getUserMedia({ audio: true, video: true })
      .catch((err) => {
        console.error("Failed to get media:", err);
        return null;
      });

    if (!stream) {
      return () => {};
    }

    const device = new Device();
    await device.load({
      routerRtpCapabilities: await getRouterRtpCapabilities(),
    });

    let sendTransport: Transport<AppData> | null = null;
    let receiveTransport: Transport<AppData> | null = null;

    const cleanupRoom = initRoomHandler({
      onConnected: async (id) => {
        clientId.current = id;

        if (localVideoRef.current) {
          localVideoRef.current.srcObject = stream;
        }

        const transport = device.createSendTransport(
          await createTransport(clientId.current, "send"),
        );

        transport.on(
          "connect",
          async ({ dtlsParameters }, callback, errback) => {
            try {
              await connectTransport(transport.id, dtlsParameters);
              callback();
            } catch (error) {
              errback(error as Error);
            }
          },
        );

        transport.on(
          "produce",
          async ({ kind, rtpParameters }, callback, errback) => {
            try {
              const { producerId } = await createProducer(
                transport.id,
                kind,
                rtpParameters,
              );
              callback({ id: producerId });
            } catch (error) {
              errback(error as Error);
            }
          },
        );

        await transport.produce({ track: stream.getVideoTracks()[0] });
        await transport.produce({ track: stream.getAudioTracks()[0] });

        sendTransport = transport;
      },

      onMatch: async (connectedClient, session) => {
        if (!clientId.current) {
          return;
        }

        sessionId.current = session;

        const transport = device.createRecvTransport(
          await createTransport(clientId.current, "receive"),
        );

        transport.on(
          "connect",
          async ({ dtlsParameters }, callback, errback) => {
            try {
              await connectTransport(transport.id, dtlsParameters);
              callback();
            } catch (error) {
              errback(error as Error);
            }
          },
        );

        const audioConsumer = await transport.consume(
          await createConsumer(
            clientId.current,
            connectedClient,
            "audio",
            device.rtpCapabilities,
          ),
        );
        const videoConsumer = await transport.consume(
          await createConsumer(
            clientId.current,
            connectedClient,
            "video",
            device.rtpCapabilities,
          ),
        );

        await resumeConsumer(audioConsumer.id);
        await resumeConsumer(videoConsumer.id);

        if (remoteVideoRef.current) {
          const remoteStream = new MediaStream();

          remoteStream.addTrack(videoConsumer.track);
          remoteStream.addTrack(audioConsumer.track);

          remoteVideoRef.current.srcObject = remoteStream;
        }

        receiveTransport = transport;
        setQueuing(false);
      },

      onPeerLeft: () => {
        onCallEndRef.current();
      },
    });

    return () => {
      stream.getTracks().forEach((track) => track.stop());

      sendTransport?.close();
      receiveTransport?.close();

      cleanupRoom();
    };
  }, [localVideoRef, remoteVideoRef]);

  return { setup, isQueuing, sessionId };
}
