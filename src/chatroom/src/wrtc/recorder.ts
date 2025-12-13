import { spawn } from "child_process";
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
import { logError, logFFmpeg, logInfo, logWarn } from "../utils/logs.js";

export type RecorderEntry = {
  consumer: Consumer;
  transport: PlainTransport;
  sdpPath: string;
  completionPromise: Promise<void>;
};

const activeRecordings = new Map<string, RecorderEntry[]>();

export async function startSessionRecording(
  router: Router,
  sessionId: string,
  clients: string[]
) {
  logInfo(`Starting session ${sessionId} with clients:`, clients);

  const setupPromises: Promise<RecorderEntry>[] = [];
  const list: RecorderEntry[] = [];

  for (const clientId of clients) {
    const entry = transports.get(clientId);

    if (entry?.send) {
      const producers = entry.send.producers;

      if (producers) {
        for (const kind of ["audio", "video"] as const) {
          const producer = producers[kind];

          if (producer) {
            if (kind === "video") {
              (producer as any).requestKeyFrame?.();
            }

            setupPromises.push(
              createProducerRecorder(
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

  logInfo(`Waiting for all ${setupPromises.length} recorders to initialize...`);
  const recorders = await Promise.all(setupPromises);
  list.push(...recorders);

  logInfo(
    "All recorders initialized. Resuming all consumers for synchronized start."
  );

  for (const recorder of list) {
    await recorder.consumer.resume();
  }

  activeRecordings.set(sessionId, list);
  logInfo(`Recording for session ${sessionId} is now active.`);
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

  const rtpPort = await getFreeUdpPort();

  const plainTransport = await router.createPlainTransport({
    listenIp: "127.0.0.1",
    rtcpMux: true,
    comedia: false,
  });

  const consumer = await plainTransport.consume({
    producerId: producer.id,
    rtpCapabilities: router.rtpCapabilities,
    paused: true,
  });

  await plainTransport.connect({
    ip: "127.0.0.1",
    port: rtpPort,
  });

  // an SDP file is needed for ffmpeg to be able to
  // create the file
  const sdp = generateSDP(consumer, rtpPort);
  const sdpPath = path.join(baseDir, `${kind}.sdp`);

  fs.writeFileSync(sdpPath, sdp);

  let file: string;
  let ffmpegArgs: string[];

  if (kind === "audio") {
    file = path.join(baseDir, `${kind}.mp3`);
    ffmpegArgs = [
      "-protocol_whitelist",
      "file,udp,rtp",
      "-rtbufsize",
      "20M",
      "-max_delay",
      "60000000",
      "-fflags",
      "+genpts",
      "-i",
      sdpPath,
      "-c:a",
      "libmp3lame",
      "-b:a",
      "64k",
      "-ac",
      "1",
      "-ar",
      "48000",
      file,
    ];
  } else {
    file = path.join(baseDir, `${kind}.webm`);
    ffmpegArgs = [
      "-protocol_whitelist",
      "file,udp,rtp",
      "-f",
      "sdp",
      "-rtbufsize",
      "20M",
      "-max_delay",
      "60000000",
      "-analyzeduration",
      "1M",
      "-probesize",
      "1M",
      "-fflags",
      "+genpts",
      "-i",
      sdpPath,
      "-c:v",
      "copy",
      "-vsync",
      "cfr",
      "-flags",
      "+global_header",
      "-an",
      file,
    ];
  }

  logInfo(`Starting ffmpeg: ${file} (Awaiting consumer resume)`);
  const ffmpeg = spawn("ffmpeg", ffmpegArgs);

  if (process.env.DEBUG === "true") {
    ffmpeg.stderr.on("data", (data) =>
      logFFmpeg(kind, sessionId, clientId, data.toString())
    );
  }

  let resolveCompletion: () => void;
  const completionPromise = new Promise<void>((resolve) => {
    resolveCompletion = resolve;
  });

  ffmpeg.on("close", async (code) => {
    logInfo(`ffmpeg finished with code ${code} for file ${file}`);
    if (!consumer.closed) {
      consumer.close();
    }

    if (!plainTransport.closed) {
      plainTransport.close();
    }

    try {
      fs.unlinkSync(sdpPath);
    } catch {
      logWarn(`Failed to delete SDP: ${sdpPath}`);
    }

    if (!fs.existsSync(file)) {
      logError(`File missing: ${file}`);
      resolveCompletion();

      return;
    }

    if (kind === "video") {
      logInfo(`Starting post-processing resize for ${file}...`);

      const originalFile = file;
      const fixedFile = path.join(path.dirname(file), "video_fixed.webm");

      const resizeArgs = [
        "-nostdin",
        "-y",
        "-i",
        originalFile,
        "-vf",
        "scale=iw:ih:eval=init",
        "-c:v",
        "libvpx-vp9",
        "-deadline",
        "realtime",
        "-cpu-used",
        "8",
        "-row-mt",
        "1",
        "-threads",
        "8",
        "-crf",
        "45",
        "-b:v",
        "0",
        "-an",
        fixedFile,
      ];

      await new Promise<void>((resolve, reject) => {
        const resizeFFmpeg = spawn("ffmpeg", resizeArgs);
        resizeFFmpeg.on("error", (err) => {
          logError("Resize FFmpeg failed to start:", err);
          reject(err);
        });

        resizeFFmpeg.on("close", (resizeCode) => {
          if (resizeCode === 0) {
            logInfo(
              `Resize successful, replacing ${originalFile} with ${fixedFile}.`
            );

            try {
              fs.renameSync(fixedFile, originalFile);
              resolve();
            } catch (e) {
              logError("Failed to rename fixed file:", e);
              reject(e);
            }
          } else {
            logError(
              `Resize failed with code ${resizeCode}. Keeping original file.`
            );
            reject(new Error(`Resize failed with code ${resizeCode}`));
          }
        });
      }).catch((err) => {
        logError("Post-processing failed, continuing with original file.", err);
      });
    }

    uploadForAnalysis({ sessionId, clientId, file, kind })
      .then(() => {
        fs.unlink(file, (error) => {
          if (error) {
            logError(`Failed to delete ${file}`, error);
          } else {
            logInfo(`Successfully deleted ${file} after upload`);
          }

          resolveCompletion();
        });
      })
      .catch((err) => {
        logError(`Upload failed for ${file}, file preserved`, err);
        resolveCompletion();
      });
  });

  return {
    consumer,
    transport: plainTransport,
    sdpPath,
    completionPromise,
  };
}

export async function stopSessionRecording(sessionId: string) {
  const list = activeRecordings.get(sessionId);

  if (!list) {
    return;
  }

  logInfo(`Stopping recording for session ${sessionId}`);

  const terminationPromises: Promise<void>[] = [];

  for (const { consumer, completionPromise, transport } of list) {
    terminationPromises.push(completionPromise);

    if (!consumer.closed) {
      consumer.close();
    }

    if (!transport.closed) {
      transport.close();
    }
  }

  logInfo(
    `Waiting for ${terminationPromises.length} recording processes to finish cleanup...`
  );
  await Promise.all(terminationPromises);

  const sessionDir = path.join("recordings", sessionId);
  try {
    fs.rmdirSync(sessionDir);
    logInfo(`Successfully deleted empty session directory: ${sessionDir}`);
  } catch {
    logWarn(`Session directory not empty or failed to delete: ${sessionDir}`);
  }

  activeRecordings.delete(sessionId);
  logInfo(`Recording cleanup complete for session ${sessionId}.`);
}
