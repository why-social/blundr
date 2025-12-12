import { forwardRef, useEffect, useRef, useState } from "react";
import Image from "next/image";
import { twMerge } from "tailwind-merge";
import CallVideo from "./CallVideo";

type CallControlsProps = {
  pending?: boolean;
  className?: string;
  onEndCall: () => void;
};

const CallControls = forwardRef<HTMLVideoElement, CallControlsProps>(
  ({ pending, onEndCall: onClose, className }, ref) => {
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
      <CallVideo
        className={className}
        ref={ref}
      >
        <div
          className={twMerge(
            "absolute right-4 bottom-4 left-4 flex items-baseline sm:items-center xl:text-xl",
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
            className={twMerge(
              "flex h-26 w-26 items-center gap-2 rounded-full bg-red-700 px-4 font-semibold sm:h-12 sm:w-fit xl:h-14 xl:gap-5 xl:px-6",
              "transition-colors hover:cursor-pointer hover:bg-red-800",
            )}
          >
            <span className="max-sm:hidden">End Call</span>
            <Image
              src={"/call_end.svg"}
              alt="End Call"
              width={100}
              height={100}
              className="size-17.5 sm:size-7 xl:size-9"
            />
          </button>
        </div>
      </CallVideo>
    );
  },
);

CallControls.displayName = "CallControls";

export default CallControls;
