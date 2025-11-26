"use client";

import { useCallback, useEffect, useRef } from "react";
import {
  getRouterRtpCapabilities,
  createTransport,
  connectTransport,
  resumeConsumer,
  createProducer,
  createConsumer,
} from "@/api/mediasoup";
import { Device } from "mediasoup-client";
import CallControls from "@/app/components/CallControls";
import Video from "@/app/components/Video";
import { init as initRoomHandler } from "@/api/room";
import { AppData, Transport } from "mediasoup-client/types";

export default function Chat() {
  const localVideoRef = useRef<HTMLVideoElement>(null);
  const remoteVideoRef = useRef<HTMLVideoElement>(null);

  const clientId = useRef<string>(null);
  const sessionId = useRef<string>(null);

  const setup = useCallback(async () => {
    const device = new Device();
    await device.load({
      routerRtpCapabilities: await getRouterRtpCapabilities(),
    });

    const stream = await navigator.mediaDevices.getUserMedia({
      audio: true,
      video: true,
    });

    let sendTransport: Transport<AppData> | null = null;
    let receiveTransport: Transport<AppData> | null = null;

    // TODO: error handling
    const cleanupRoom = initRoomHandler({
      onConnected: async (id: string) => {
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
      onMatch: async (connectedClient: string, session: string) => {
        if (clientId.current == null) {
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
      },
    });

    return () => {
      stream.getTracks().forEach((track) => track.stop());

      sendTransport?.close();
      receiveTransport?.close();

      cleanupRoom();
    };
  }, []);

  // setup hook
  const hasRealMounted = useRef(false);

  useEffect(() => {
    // ignore the first development mount (StrictMode double mount)
    // this breaks the web socket logic otherwise
    if (process.env.NODE_ENV === "development" && !hasRealMounted.current) {
      hasRealMounted.current = true;
      console.debug("Ignoring first mount in development...");

      return;
    }

    let mounted = true;
    // use it as a local "ref" rather than a hook
    // to avoid the dev StrictMode mount issue
    const cleanupRef = {
      current: undefined as (() => void) | undefined,
    };

    (async () => {
      const cleanup = await setup();

      if (mounted) {
        cleanupRef.current = cleanup;
      } else {
        cleanup();
      }
    })();

    return () => {
      mounted = false;
      cleanupRef.current?.();
    };
  }, [setup]);

  return (
    <div className="p-5">
      <CallControls
        ref={localVideoRef}
        onEndCall={() => console.log("Call ended")}
      />
      <Video ref={remoteVideoRef} />
    </div>
  );
}
