import { spawn, execSync } from "child_process";
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
  startFFmpeg: () => void;
  clientId: string;
  file: string;
  kind: MediaKind;
  success: boolean;
};

const activeRecordings = new Map<string, RecorderEntry[]>();

export async function startSessionRecording(
  router: Router,
  sessionId: string,
  clients: string[]
) {
  logInfo(`Starting session ${sessionId} with clients:`, clients);

  const setupPromises: Promise<RecorderEntry>[] = [];

  for (const clientId of clients) {
    const entry = transports.get(clientId);

    if (entry?.send) {
      const producers = entry.send.producers;

      if (producers) {
        for (const kind of ["audio", "video"] as const) {
          const producer = producers[kind];

          if (producer) {
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

  logInfo(
    "All recorders initialized. Resuming all consumers for synchronized start."
  );

  for (const recorder of recorders) {
    recorder.startFFmpeg();
  }

  // wait for FFmpeg to spin up and bind the UDP ports
  // this is supposed to help a little when running in a VM
  await new Promise((resolve) => setTimeout(resolve, 500));

  for (const recorder of recorders) {
    await recorder.consumer.resume();

    if (recorder.kind === "video") {
      await recorder.consumer.requestKeyFrame();
    }
  }

  activeRecordings.set(sessionId, recorders);
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
      "-i",
      sdpPath,
      "-c:v",
      "copy",
      "-an",
      "-vsync",
      "vfr",
      file,
    ];
  }

  let ffmpegProcess: ReturnType<typeof spawn> | null = null;
  let resolveCompletion: () => void = () => {};
  const completionPromise = new Promise<void>((resolve) => {
    resolveCompletion = resolve;
  });

  let success = true;

  const startFFmpeg = () => {
    logInfo(`Starting ffmpeg: ${file} (Awaiting consumer resume)`);

    ffmpegProcess = spawn("ffmpeg", ffmpegArgs);

    if (process.env.DEBUG === "true") {
      ffmpegProcess.stderr?.on("data", (data) =>
        logFFmpeg(kind, sessionId, clientId, data.toString())
      );
    }

    ffmpegProcess.on("close", (code) => {
      try {
        if (code !== 0) {
          logError(`FFmpeg exited with code ${code} for file ${file}`);
          success = false;
        }

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
          success = false;
        }
      } catch (err) {
        logError("Unexpected error in FFmpeg close handler", err);
        success = false;
      } finally {
        resolveCompletion();
      }
    });
  };

  return {
    consumer,
    transport: plainTransport,
    sdpPath,
    completionPromise,
    startFFmpeg,
    clientId,
    file,
    kind,
    success,
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

  const videoRecordings = list.filter((r) => r.kind === "video");

  let longestDuration = 0;
  const durations: Record<string, number> = {};

  for (const recording of list) {
    if (!fs.existsSync(recording.file)) {
      recording.success = false;
    } else {
      try {
        const duration = parseFloat(
          execSync(
            `ffprobe -v error -show_entries format=duration -of csv=p=0 "${recording.file}"`
          ).toString()
        );
        durations[recording.file] = duration;

        if (duration > longestDuration) {
          longestDuration = duration;
        }
      } catch (error) {
        logError(`Failed to get duration for ${recording.file}`, error);
        recording.success = false;
      }
    }
  }

  for (const video of videoRecordings) {
    const originalFile = video.file;
    const duration = durations[originalFile] || longestDuration;

    if (!video.success) {
      const tempFile = path.join(
        path.dirname(originalFile),
        "video_black.webm"
      );

      const ffmpegArgs = [
        "-y",
        "-f",
        "lavfi",
        "-i",
        `color=size=640x360:rate=30:color=black`,
        "-t",
        `${duration}`,
        "-c:v",
        "libvpx-vp9",
        "-b:v",
        "0",
        "-an",
        tempFile,
      ];

      try {
        await new Promise<void>((resolve, reject) => {
          const blackFFmpeg = spawn("ffmpeg", ffmpegArgs);

          blackFFmpeg.on("error", (error) => reject(error));

          blackFFmpeg.on("close", (code) => {
            if (code === 0) {
              fs.renameSync(tempFile, originalFile);
              video.success = true;

              resolve();
            } else {
              reject(new Error(`Failed to generate black video: ${code}`));
            }
          });
        });
        logInfo(`Replaced failed video ${originalFile} with black placeholder`);
      } catch (err) {
        logError(`Could not create black video for ${originalFile}`, err);
        video.success = false;
      }
    } else {
      const padDuration = longestDuration - (durations[originalFile] || 0);
      const vfArgs =
        padDuration > 0.05
          ? `tpad=start_duration=${padDuration}:start_mode=add`
          : "null";

      const tempFile = path.join(
        path.dirname(originalFile),
        "video_fixed.webm"
      );

      const resizeArgs = [
        "-nostdin",
        "-y",
        "-i",
        originalFile,
        "-vf",
        vfArgs,
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
        tempFile,
      ];

      try {
        await new Promise<void>((resolve, reject) => {
          const resizeFFmpeg = spawn("ffmpeg", resizeArgs);

          resizeFFmpeg.on("error", (error) => reject(error));

          resizeFFmpeg.on("close", (code) => {
            if (code === 0) {
              fs.renameSync(tempFile, originalFile);

              resolve();
            } else {
              reject(new Error(`Resize/pad failed with code ${code}`));
            }
          });
        });

        logInfo(`Post-processed video ${originalFile} successfully`);
        video.success = true;
      } catch (err) {
        logError(`Post-processing failed for video ${originalFile}`, err);
        video.success = false;
      }
    }
  }

  const finalSucceeded = list.every((recording) => recording.success);

  if (finalSucceeded) {
    logInfo(`All recordings succeeded for session ${sessionId}. Uploading...`);

    const uploadPromises = list.map((recording) =>
      uploadForAnalysis({
        sessionId,
        clientId: recording.clientId,
        file: recording.file,
        kind: recording.kind,
      }).catch((err) => {
        logError(
          `Upload failed for ${recording.kind} of ${recording.clientId}:`,
          err
        );
      })
    );

    await Promise.all(uploadPromises);
  } else {
    logWarn(
      `One or more recordings failed after post-processing for session ${sessionId}. Skipping upload.`
    );
  }

  const sessionDir = path.join("recordings", sessionId);
  fs.rmSync(sessionDir, { recursive: true, force: true });
  logInfo(`Deleted session directory: ${sessionDir}`);

  activeRecordings.delete(sessionId);
  logInfo(`Recording cleanup complete for session ${sessionId}.`);
}
