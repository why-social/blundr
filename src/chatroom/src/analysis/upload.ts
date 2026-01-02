// Original Author: Razvan Albu
// Source: https://git.chalmers.se/courses/dit826/2025/team2
// License: MIT

import path from "path";
import fs from "fs";
import { MediaKind } from "mediasoup/types";
import { logError, logInfo } from "../utils/logs.js";

export function uploadForAnalysis({
  sessionId,
  clientId,
  file,
  kind,
}: {
  sessionId: string;
  clientId: string;
  file: string;
  kind: MediaKind;
}): Promise<any> {
  const form = new FormData();
  form.append("user_id", clientId);
  form.append("session_id", sessionId);

  const fileBuffer = fs.readFileSync(file);
  const fileName = path.basename(file);
  form.append(
    kind === "video" ? "file" : "audio",
    new Blob([fileBuffer]),
    fileName
  );

  const url =
    kind === "video"
      ? `${process.env.FER_URL}/predict-face-emotion`
      : `${process.env.VER_URL}/predict-audio-emotion`;

  return fetch(url, { method: "POST", body: form })
    .then(async (res) => {
      logInfo(`Sent ${kind} for ${clientId}, status: ${res.status}`);
    })
    .catch((error) => {
      if (error instanceof Error) {
        logError(`Upload failed for ${kind} of ${clientId}:`, error.message);
      } else {
        logError(`Upload failed for ${kind} of ${clientId}:`, error);
      }
    });
}
