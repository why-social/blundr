// Original Author: Razvan Albu
// Source: https://git.chalmers.se/courses/dit826/2025/team2
// License: MIT

import { forwardRef, JSX } from "react";

const Video = forwardRef<HTMLVideoElement, JSX.IntrinsicElements["video"]>(
  (props, ref) => {
    return (
      <video
        ref={ref}
        autoPlay
        playsInline
        muted={false}
        {...props}
      />
    );
  },
);

Video.displayName = "Video";

export default Video;
