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
} from "@/app/api/mediasoup";
import { init as initRoomHandler } from "@/app/api/room";

export function useMediaSoup(
  localVideoRef: RefObject<HTMLVideoElement | null>,
  remoteVideoRef: RefObject<HTMLVideoElement | null>,
  onCallEnd: () => void,
) {
  const clientId = useRef<string | null>(null);
  const sessionId = useRef<string | null>(null);
  const [isQueuing, setQueuing] = useState(true);
  const [error, setError] = useState<string | null>(null);

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

    const routerCapabilitiesRes = await getRouterRtpCapabilities();
    if (routerCapabilitiesRes.status === "error") {
      setError(routerCapabilitiesRes.data.message);

      return () => {};
    }

    const device = new Device();
    await device.load({
      routerRtpCapabilities: routerCapabilitiesRes.data,
    });

    let sendTransport: Transport<AppData> | null = null;
    let receiveTransport: Transport<AppData> | null = null;

    const cleanupRoom = initRoomHandler({
      onConnected: async (id) => {
        clientId.current = id;

        if (localVideoRef.current) {
          localVideoRef.current.srcObject = stream;
        }

        const transportRes = await createTransport(clientId.current, "send");
        if (transportRes.status === "error") {
          setError(transportRes.data.message);
          throw Error(transportRes.data.message);
        }

        const transport = device.createSendTransport(transportRes.data);

        transport.on(
          "connect",
          async ({ dtlsParameters }, callback, errback) => {
            try {
              const connectRes = await connectTransport(
                transport.id,
                dtlsParameters,
              );
              if (connectRes.status === "error") {
                setError(connectRes.data.message);
                throw Error(connectRes.data.message);
              }

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
              const producerRes = await createProducer(
                transport.id,
                kind,
                rtpParameters,
              );

              if (producerRes.status === "error") {
                setError(producerRes.data.message);
                throw Error(producerRes.data.message);
              }

              callback({ id: producerRes.data.producerId });
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

        const transportRes = await createTransport(clientId.current, "receive");
        if (transportRes.status === "error") {
          setError(transportRes.data.message);
          throw Error(transportRes.data.message);
        }

        const transport = device.createRecvTransport(transportRes.data);

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

        const audioConsumerRes = await createConsumer(
          clientId.current,
          connectedClient,
          "audio",
          device.rtpCapabilities,
        );
        if (audioConsumerRes.status === "error") {
          setError(audioConsumerRes.data.message);
          throw Error(audioConsumerRes.data.message);
        }

        const audioConsumer = await transport.consume(audioConsumerRes.data);

        const videoConsumerRes = await createConsumer(
          clientId.current,
          connectedClient,
          "video",
          device.rtpCapabilities,
        );
        if (videoConsumerRes.status === "error") {
          setError(videoConsumerRes.data.message);
          throw Error(videoConsumerRes.data.message);
        }

        const videoConsumer = await transport.consume(videoConsumerRes.data);

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

  return { setup, isQueuing, sessionId, clientId, error };
}
