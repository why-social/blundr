import { forwardRef, JSX } from "react";

const Video = forwardRef<HTMLVideoElement, JSX.IntrinsicElements["video"]>(
  (props, ref) => {
    return (
      <video
        ref={ref}
        autoPlay
        playsInline
        muted={false}
        className="-scale-x-100"
        {...props}
      />
    );
  },
);

Video.displayName = "Video";

export default Video;
