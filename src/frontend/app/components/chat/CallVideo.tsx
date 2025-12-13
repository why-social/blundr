import { forwardRef, JSX } from "react";
import Video from "./Video";
import { twMerge } from "tailwind-merge";
import Spinner from "../Spinner";

type CallVideoProps = JSX.IntrinsicElements["video"] & {
  showSpinner?: boolean;
  muted?: boolean;
};

const CallVideo = forwardRef<HTMLVideoElement, CallVideoProps>(
  ({ className, showSpinner, muted, children }, ref) => {
    return (
      <div
        className={twMerge(
          "relative inline-block select-none [clip-path:inset(0_round_1.5rem)] md:[clip-path:inset(0_round_2rem)]",
          className ?? "",
        )}
      >
        {showSpinner && (
          <Spinner
            size="lg"
            className="absolute top-1/2 left-1/2 -translate-1/2"
          />
        )}

        <Video
          ref={ref}
          className="absolute size-full -scale-x-100 object-cover"
          muted={muted}
        />
        {children}
      </div>
    );
  },
);

CallVideo.displayName = "CallVideo";

export default CallVideo;
