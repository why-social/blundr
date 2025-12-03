import { Server } from "http";
import getPublicIp from "../utils/ip.js";
import { createWorker } from "mediasoup";
import { init as initMatcher } from "./roomMatcher.js";
import {
  Worker,
  Router,
  RtpCapabilities,
  RtpParameters,
  DtlsParameters,
  MediaKind,
  Consumer,
  AppData,
  WebRtcTransport,
  Producer,
  DtlsState,
  IceState,
} from "mediasoup/types";
import { Optional } from "../utils/types.js";
import { startSessionRecording, stopSessionRecording } from "./recorder.js";

type TransportSection = {
  transport: WebRtcTransport<AppData>;
  producers: {
    audio?: Producer<AppData>;
    video?: Producer<AppData>;
  };
  consumers: {
    audio?: Consumer<AppData>;
    video?: Consumer<AppData>;
  };
};

type Session = {
  sessionId: string;
  clients: string[];
};

let worker: Worker;
let router: Router;

let listenIp: string | undefined;
let announcedIp: string | undefined;

const sessions = new Array<Session>();

export const transports = new Map<
  string,
  {
    send?: Omit<TransportSection, "consumers">;
    receive?: Omit<TransportSection, "producers">;
  }
>();

export async function init(server: Server): Promise<void> {
  listenIp = process.env.MEDIASOUP_LISTEN_IP ?? "0.0.0.0";
  announcedIp = process.env.MEDIASOUP_ANNOUNCED_IP ?? (await getPublicIp());

  if (!announcedIp) {
    throw new Error("No public IP available for Mediasoup WebRTC transport");
  }

  worker = await createWorker({
    logLevel: "warn",
    rtcMinPort: 2000,
    rtcMaxPort: 2100,
  });

  router = await worker.createRouter({
    mediaCodecs: [
      {
        kind: "audio",
        mimeType: "audio/opus",
        clockRate: 48000,
        channels: 2,
      },
      {
        kind: "video",
        mimeType: "video/VP8",
        clockRate: 90000,
        parameters: { "x-google-start-bitrate": 1000 },
      },
    ],
  });

  console.log("Mediasoup worker and router created");

  initMatcher(
    server,
    async function onSession(sessionId: string, clients: string[]) {
      sessions.push({ sessionId, clients });

      await startSessionRecording(router, sessionId, clients);
    },
    function onClose(clientId: string) {
      const session = sessions.find((session) =>
        session.clients.includes(clientId)
      );

      if (!session) {
        cleanupClient(clientId);

        return;
      }

      session.clients = session.clients.filter((client) => client !== clientId);

      cleanupClient(clientId);

      if (session.clients.length === 0) {
        stopSessionRecording(session.sessionId);
        sessions.splice(sessions.indexOf(session), 1);
      }
    }
  );
}

export function getCapabilities(): RtpCapabilities {
  if (!router) {
    throw new Error("Router not ready");
  }

  return router.rtpCapabilities;
}

export async function create(clientId: string, direction: "send" | "receive") {
  if (!listenIp) {
    throw new Error("Mediasoup IP configuration error");
  }

  const transport = await router.createWebRtcTransport({
    listenIps: [{ ip: listenIp, announcedIp }],
    enableUdp: true,
    enableTcp: true,
    preferUdp: true,
  });

  transport.on("dtlsstatechange", (dtlsState: DtlsState) => {
    if (dtlsState === "closed" || dtlsState === "failed") {
      cleanupTransport(transport.id);
    }
  });

  transport.on("icestatechange", (iceState: IceState) => {
    if (iceState === "disconnected" || iceState === "closed") {
      cleanupTransport(transport.id);
    }
  });

  let entry = transports.get(clientId);
  if (!entry) {
    entry = {};
    transports.set(clientId, entry);
  }

  if (direction === "send") {
    entry.send = {
      transport,
      producers: {},
    };
  } else {
    entry.receive = {
      transport,
      consumers: {},
    };
  }

  return {
    id: transport.id,
    iceParameters: transport.iceParameters,
    iceCandidates: transport.iceCandidates,
    dtlsParameters: transport.dtlsParameters,
  };
}

/**
 * Connects a transport with parameters from the client
 *
 * @param transportId - ID of the transport to connect
 * @param dtlsParameters - DTLS parameters from the client
 *
 * @returns Connection status
 */
export async function connect(
  transportId: string,
  dtlsParameters: DtlsParameters
) {
  const transport = findTransportById(transportId);

  if (!transport) {
    throw new Error("Transport not found");
  }

  await transport.connect({ dtlsParameters });

  return { connected: true };
}

/**
 * Creates a producer for a client
 *
 * @param transportId - Transport ID used to send media
 * @param kind - "audio" for audio stream, "video" for video stream
 * @param rtpParameters - RTP parameters for stream
 *
 * @returns ID of created producers
 */
export async function produce(
  transportId: string,
  kind: MediaKind,
  rtpParameters: RtpParameters
) {
  const transport = findTransportById(transportId);

  if (!transport) {
    throw new Error("Transport not found");
  }

  const producer = await transport.produce({
    kind,
    rtpParameters,
  });

  for (const entry of transports.values()) {
    if (entry.send?.transport.id === transportId) {
      entry.send.producers[kind] = producer;

      break;
    }
  }

  return {
    producerId: producer.id,
  };
}

/**
 * Creates consumers for audio and video from another producer
 *
 * @param clientId - ID of client's producers to consume
 * @param kind - what type of media to consume
 * @param rtpCapabilities - Client's RTP capabilities
 *
 * @returns Info about created consumer
 */
export async function consume(
  consumingClientId: string,
  clientId: string,
  kind: MediaKind,
  rtpCapabilities: RtpCapabilities
) {
  let transport = transports.get(clientId);

  if (!transport) {
    throw new Error("Transport not found");
  }

  const producer = transport.send?.producers[kind];
  if (!producer) {
    throw new Error(`Producer for kind ${kind} not found`);
  }

  if (!router.canConsume({ producerId: producer.id, rtpCapabilities })) {
    throw new Error(`Cannot consume producer ${producer.id}`);
  }

  transport = transports.get(consumingClientId);

  if (!transport?.receive) {
    throw new Error("Receive transport not found");
  }

  const consumer = await transport?.receive.transport.consume({
    producerId: producer.id,
    rtpCapabilities,
    paused: true,
  });

  transport.receive.consumers[kind] = consumer;

  return {
    id: consumer.id,
    producerId: producer.id,
    kind: consumer.kind,
    rtpParameters: consumer.rtpParameters,
  };
}

/**
 * Resumes a paused consumer
 *
 * @param consumerId - ID of the consumer to resume
 *
 * @returns Resume status
 */
export async function resume(consumerId: string) {
  let foundConsumer: Consumer<AppData> | null = null;

  for (const entry of transports.values()) {
    const receiveConsumers = entry.receive?.consumers;

    if (receiveConsumers) {
      for (const consumer of Object.values(receiveConsumers)) {
        if (consumer.id === consumerId) {
          foundConsumer = consumer;

          break;
        }
      }
    }

    if (foundConsumer) {
      break;
    }
  }

  if (!foundConsumer) {
    throw new Error("Consumer not found");
  }

  await foundConsumer.resume();

  return { resumed: true };
}

function cleanupClient(clientId: string) {
  const entry = transports.get(clientId);
  if (!entry) {
    return;
  }

  if (entry.send) {
    closeTransportSection(entry.send);
  }

  if (entry.receive) {
    closeTransportSection(entry.receive);
  }

  transports.delete(clientId);
  console.debug(`Resources for client ${clientId} cleaned up`);
}

function closeTransportSection(
  section: Optional<TransportSection, "producers" | "consumers">
) {
  if (section.producers) {
    for (const producer of Object.values(section.producers)) {
      producer?.close();
    }
  }

  if (section.consumers) {
    for (const consumer of Object.values(section.consumers)) {
      consumer?.close();
    }
  }

  section.transport.close();
}

function findTransportById(id: string) {
  for (const { send, receive } of transports.values()) {
    if (send && send.transport.id === id) {
      return send.transport;
    }

    if (receive && receive.transport.id === id) {
      return receive.transport;
    }
  }

  return null;
}

function cleanupTransport(transportId: string) {
  for (const [clientId, entry] of transports.entries()) {
    if (entry.send?.transport.id === transportId) {
      closeTransportSection(entry.send);

      entry.send = undefined;
    }

    if (entry.receive?.transport.id === transportId) {
      closeTransportSection(entry.receive);

      entry.receive = undefined;
    }

    if (!entry.send && !entry.receive) {
      transports.delete(clientId);
    }
  }
}
