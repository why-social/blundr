// Original Author: Razvan Albu
// Source: https://git.chalmers.se/courses/dit826/2025/team2
// License: MIT

"use client";

import { CSSProperties, useEffect, useRef } from "react";
import { Gradient } from "@/app/scripts/meshGradient";

export function GradientCanvas() {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    new Gradient(40, (instance: Gradient) => {
      if (instance.last != 0) {
        ref.current?.style.setProperty("opacity", "0.75");
      }

      // @ts-expect-error initGradient is attached to the object after initialization
    }).initGradient("#gradient-canvas");
  }, []);

  return (
    <>
      <div
        ref={ref}
        className="pointer-events-none fixed top-0 right-0 -z-10 size-full opacity-0 transition-opacity duration-5000"
      >
        <canvas
          id="gradient-canvas"
          className="absolute size-full"
          style={
            {
              "--gradient-color-1": "#eb3131",
              "--gradient-color-2": "#f09cff",
              "--gradient-color-3": "#ff1778",
              maskImage: `radial-gradient(circle farthest-side at top center, rgba(0,0,0,1) 0%, rgba(0,0,0,0) 100%)`,
              WebkitMaskImage: `radial-gradient(circle farthest-side at top center, rgba(0,0,0,1) 0%, rgba(0,0,0,0) 100%)`,
              maskRepeat: "no-repeat",
              WebkitMaskRepeat: "no-repeat",
              maskSize: "cover",
              WebkitMaskSize: "cover",
            } as CSSProperties
          }
        />
      </div>
    </>
  );
}
