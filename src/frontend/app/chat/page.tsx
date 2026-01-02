// Original Author: Razvan Albu
// Source: https://git.chalmers.se/courses/dit826/2025/team2
// License: MIT

"use client";

import { useEffect, useRef, useState } from "react";

import CallControls from "@/app/components/chat/CallControls";
import { Button } from "../components/Button";

import { checkMediaPermissions } from "./useMediaPermissions";
import { useMediaSoup } from "./useMediasoup";
import { useNavigationBlock } from "./useNavigationBlock";
import CallVideo from "../components/chat/CallVideo";
import { twMerge } from "tailwind-merge";
import { EmphasisText } from "../components/EmphasisText";
import { ErrorDialog } from "../components/ErrorDialog";

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
    clientId: clientIdRef,
    error: mediasoupError,
  } = useMediaSoup(localVideoRef, remoteVideoRef, () => {
    if (clientIdRef.current && sessionIdRef.current && !isQueuing) {
      replaceUrl(`/analysis/${sessionIdRef.current}/${clientIdRef.current}`);
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

      if (!mounted) {
        return;
      }

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
    <div className="relative min-h-screen w-full p-5 before:absolute before:top-5 before:right-5 before:bottom-5 before:left-5 before:bg-gray-950 before:[clip-path:inset(0_round_1.5rem)] md:before:[clip-path:inset(0_round_2rem)]">
      <CallVideo
        ref={localVideoRef}
        showSpinner={true}
        muted={true}
        className={twMerge(
          "absolute top-5 right-5 bottom-5 left-5 origin-top-right bg-gray-950 transition-transform duration-1000 ease-in-out",
          !isQueuing && "z-20 -translate-x-5 translate-y-5 scale-[0.26]",
        )}
      />

      <CallControls
        ref={remoteVideoRef}
        muted={false}
        pending={isQueuing}
        className={"absolute top-5 right-5 bottom-5 left-5"}
        onEndCall={() => {
          if (clientIdRef.current && sessionIdRef.current && !isQueuing) {
            replaceUrl(
              `/analysis/${sessionIdRef.current}/${clientIdRef.current}`,
            );
          } else {
            replaceUrl("/");
          }
        }}
      />

      {isQueuing && (
        <EmphasisText
          className="absolute inset-x-9 top-8 animate-pulse text-2xl font-black text-white italic text-shadow-[#00000035] text-shadow-lg"
          text="Waiting for a match..."
        />
      )}

      {showDialog && (
        <LeaveDialog
          onConfirm={() => replaceUrl("/")}
          onCancel={() => setShowDialog(false)}
        />
      )}

      {(permissionError || mediasoupError) && (
        <ErrorDialog
          message={permissionError ?? mediasoupError}
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
