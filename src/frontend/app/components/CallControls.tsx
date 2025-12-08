import { forwardRef, useEffect, useRef, useState } from "react";
import Video from "./Video";
import Image from "next/image";
import clsx from "clsx";

type CallControlsProps = {
  pending?: boolean;
  onEndCall: () => void;
};

const CallControls = forwardRef<HTMLVideoElement, CallControlsProps>(
  ({ pending, onEndCall: onClose }, ref) => {
    const startTimeRef = useRef<number | null>(null);
    const [elapsedTime, setElapsedTime] = useState("00:00");

    useEffect(() => {
      if (!pending && startTimeRef.current === null) {
        startTimeRef.current = Date.now();
      }
    }, [pending]);

    useEffect(() => {
      if (pending || startTimeRef.current === null) {
        return;
      }

      const updateTimer = () => {
        const now = Date.now();
        const differenceInSeconds = Math.floor(
          (now - startTimeRef.current!) / 1000,
        );

        const minutes = Math.floor(differenceInSeconds / 60)
          .toString()
          .padStart(2, "0");
        const seconds = (differenceInSeconds % 60).toString().padStart(2, "0");

        setElapsedTime(`${minutes}:${seconds}`);
      };

      updateTimer();
      const intervalId = setInterval(updateTimer, 1000);

      return () => clearInterval(intervalId);
    }, [pending]);

    return (
      <div className="relative inline-block select-none [clip-path:inset(0_round_1.5rem)]">
        <Video
          ref={ref}
          muted={true}
        />
        <div
          className={clsx(
            "absolute right-2 bottom-2 left-2 flex items-center",
            pending ? "justify-end" : "justify-between",
          )}
        >
          {!pending && (
            <h3 className="mx-2.5 font-semibold text-shadow-[#00000035] text-shadow-lg">
              {elapsedTime}
            </h3>
          )}
          <button
            onClick={onClose}
            className={clsx(
              "flex h-10 items-center gap-2 rounded-full bg-red-700 px-4 font-semibold",
              "transition-colors hover:cursor-pointer hover:bg-red-800",
            )}
          >
            End Call
            <Image
              src={"/call_end.svg"}
              alt="End Call"
              width={100}
              height={100}
              className="size-7"
            />
          </button>
        </div>
      </div>
    );
  },
);

CallControls.displayName = "CallControls";

export default CallControls;
