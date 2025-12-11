import { ChildProcess, spawn } from "child_process";
import {
  Router,
  Producer,
  Consumer,
  PlainTransport,
  MediaKind,
} from "mediasoup/types";
import fs from "fs";
import path from "path";
import { transports } from "./mediasoup.js";
import { getFreeUdpPort } from "../utils/ports.js";
import { generateSDP } from "../utils/sdp.js";
import { uploadForAnalysis } from "../analysis/upload.js";

export type RecorderEntry = {
  ffmpeg: ReturnType<typeof spawn>;
  consumer: Consumer;
  transport: PlainTransport;
  sdpPath: string;
};

const activeRecordings = new Map<string, RecorderEntry[]>();

export async function startSessionRecording(
  router: Router,
  sessionId: string,
  clients: string[]
) {
  console.log(`Starting session ${sessionId} with clients:`, clients);

  const list: RecorderEntry[] = [];

  for (const clientId of clients) {
    const entry = transports.get(clientId);

    if (entry?.send) {
      const producers = entry.send.producers;

      if (producers) {
        for (const kind of ["audio", "video"] as const) {
          const producer = producers[kind];

          if (producer) {
            list.push(
              await createProducerRecorder(
                router,
                sessionId,
                clientId,
                producer,
                kind
              )
            );
          }
        }
      }
    }
  }

  activeRecordings.set(sessionId, list);
}

async function createProducerRecorder(
  router: Router,
  sessionId: string,
  clientId: string,
  producer: Producer,
  kind: MediaKind
): Promise<RecorderEntry> {
  const baseDir = path.join("recordings", sessionId, clientId);
  fs.mkdirSync(baseDir, { recursive: true });

  const rtpPort = await getFreeUdpPort({ evenOnly: true });
  const rtcpPort = rtpPort + 1;

  const plainTransport = await router.createPlainTransport({
    listenIp: "127.0.0.1",
    rtcpMux: false,
    comedia: false,
  });

  const consumer = await plainTransport.consume({
    producerId: producer.id,
    rtpCapabilities: router.rtpCapabilities,
    paused: false,
  });
  await consumer.resume();

  await plainTransport.connect({
    ip: "127.0.0.1",
    port: rtpPort,
    rtcpPort,
  });

  // an SDP file is needed for ffmpeg to be able to
  // create the file
  const sdp = generateSDP(consumer, rtpPort, rtcpPort);
  const sdpPath = path.join(baseDir, `${kind}.sdp`);

  fs.writeFileSync(sdpPath, sdp);

  let file: string;
  let ffmpegArgs: string[];

  if (kind === "audio") {
    file = path.join(baseDir, `${kind}.wav`);
    ffmpegArgs = [
      "-protocol_whitelist",
      "file,udp,rtp",
      "-i",
      sdpPath,
      "-c:a",
      "pcm_s16le",
      "-vn",
      file,
    ];
  } else {
    file = path.join(baseDir, `${kind}.webm`);
    ffmpegArgs = [
      "-protocol_whitelist",
      "file,udp,rtp",
      "-err_detect",
      "ignore_err",
      "-i",
      sdpPath,
      "-c",
      "copy",
      file,
    ];
  }

  console.log(`Starting ffmpeg: ${file}`);
  const ffmpeg = spawn("ffmpeg", ffmpegArgs);

  if (process.env.DEBUG === "true") {
    ffmpeg.stderr.on("data", (data) =>
      console.log(`[FFmpeg ${kind}]`, data.toString())
    );
  }

  ffmpeg.on("close", (code) => {
    console.log(`ffmpeg finished with code ${code} for file ${file}`);

    try {
      if (!consumer.closed) {
        consumer.close();
      }
    } catch {
      console.log(`Could not close consumer ${consumer.id}`);
    }

    try {
      if (!plainTransport.closed) {
        plainTransport.close();
      }
    } catch {
      console.log(`Could not close transport ${plainTransport.id}`);
    }

    try {
      fs.unlinkSync(sdpPath);

      console.log(`Cleaned up SDP: ${sdpPath}`);
    } catch (error) {
      console.warn(`Could not delete SDP: ${sdpPath}`, error);
    }

    if (!fs.existsSync(file)) {
      console.error(`Skipping analysis — file does not exist: ${file}`);
      return;
    }

    uploadForAnalysis({
      sessionId,
      clientId,
      file,
      kind,
    }).finally(() => {
      fs.unlink(file, (error) => {
        if (error) {
          console.error(`Failed to delete file ${file}`, error);
        }
      });
    });
  });

  return {
    ffmpeg,
    consumer,
    transport: plainTransport,
    sdpPath,
  };
}

export function stopSessionRecording(sessionId: string) {
  const list = activeRecordings.get(sessionId);

  if (!list) {
    console.warn(`No recordings to stop for session ${sessionId}`);

    return;
  }

  console.log(`Stopping recording for session ${sessionId}`);

  for (const { ffmpeg, consumer, transport } of list) {
    try {
      gracefulStop(ffmpeg);
    } catch (error) {
      console.error("Error killing ffmpeg:", error);
    }

    try {
      if (!consumer.closed) {
        consumer.close();
      }
    } catch {
      console.log(`Could not close consumer ${consumer.id}`);
    }

    try {
      if (!transport.closed) {
        transport.close();
      }
    } catch {
      console.log(`Could not close transport ${transport.id}`);
    }
  }

  activeRecordings.delete(sessionId);
}

async function gracefulStop(ffmpeg: ChildProcess) {
  return new Promise<void>((resolve) => {
    const killTimer = setTimeout(() => {
      if (!ffmpeg.killed) {
        try {
          ffmpeg.kill("SIGTERM");
        } catch (error) {
          console.warn(
            "Failed to kill FFmpeg (it might already be closed):",
            error
          );
        }
      }
    }, 500);

    ffmpeg.once("close", () => {
      clearTimeout(killTimer);
      resolve();
    });

    try {
      ffmpeg.stdin?.write("q");
    } catch (error) {
      console.warn("Failed to send 'q' to FFmpeg stdin:", error);
    }
  });
}
