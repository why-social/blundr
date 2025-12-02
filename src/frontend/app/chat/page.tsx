"use client";

import { useEffect, useRef, useState } from "react";

import CallControls from "@/app/components/CallControls";
import Video from "@/app/components/Video";
import { Button } from "../components/Button";

import { checkMediaPermissions } from "./useMediaPermissions";
import { useMediaSoup } from "./useMediasoup";
import { useNavigationBlock } from "./useNavigationBlock";

export default function Chat() {
  const localVideoRef = useRef<HTMLVideoElement>(null);
  const remoteVideoRef = useRef<HTMLVideoElement>(null);

  const [showDialog, setShowDialog] = useState(false);
  const [permissionError, setPermissionError] = useState<string | null>(null);

  const replaceUrl = useNavigationBlock(setShowDialog);

  const {
    setup,
    isQueuing,
    sessionId: sessionIdRef,
  } = useMediaSoup(localVideoRef, remoteVideoRef, () => {
    if (sessionIdRef.current && !isQueuing) {
      replaceUrl(`/analyze/${sessionIdRef.current}`);
    } else {
      replaceUrl("/");
    }
  });

  useEffect(() => {
    let mounted = true;
    const cleanupRef = { current: undefined as (() => void) | undefined };

    (async () => {
      const permissionStatus = await checkMediaPermissions();
      if (permissionStatus === "denied") {
        setPermissionError(
          "Camera/microphone blocked. Enable them and reload.",
        );
        return;
      }

      if (!mounted) return;

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
        pending={isQueuing}
        onEndCall={() => {
          if (sessionIdRef.current && !isQueuing) {
            replaceUrl(`/analyze/${sessionIdRef.current}`);
          } else {
            replaceUrl("/");
          }
        }}
      />

      <Video ref={remoteVideoRef} />

      {showDialog && (
        <LeaveDialog
          onConfirm={() => replaceUrl("/")}
          onCancel={() => setShowDialog(false)}
        />
      )}

      {permissionError && (
        <ErrorDialog
          message={permissionError}
          onReturn={() => replaceUrl("/")}
        />
      )}
    </div>
  );
}

function LeaveDialog({
  onConfirm,
  onCancel,
}: {
  onConfirm: () => void;
  onCancel: () => void;
}) {
  return (
    <div className="fixed top-0 left-0 z-50 flex h-full w-full items-center justify-center bg-black/70 backdrop-blur-sm">
      <div className="flex flex-col gap-4 text-center">
        <p>Are you sure you want to leave?</p>
        <div className="flex justify-center gap-4">
          <Button onClick={onConfirm}>Yes</Button>
          <Button
            variant="secondary"
            onClick={onCancel}
          >
            No
          </Button>
        </div>
      </div>
    </div>
  );
}

function ErrorDialog({
  message,
  onReturn,
}: {
  message: string;
  onReturn: () => void;
}) {
  return (
    <div className="fixed top-0 left-0 z-50 flex h-full w-full flex-col items-center justify-center bg-black/70 backdrop-blur-sm">
      <p className="mb-4">{message}</p>
      <Button onClick={onReturn}>Return Home</Button>
    </div>
  );
}
