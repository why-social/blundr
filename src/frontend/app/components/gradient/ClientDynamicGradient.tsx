// Original Author: Razvan Albu
// Source: https://git.chalmers.se/courses/dit826/2025/team2
// License: MIT

"use client";

import dynamic from "next/dynamic";

const DynamicGradientCanvas = dynamic(
  () => import("./Gradient").then((mod) => mod.GradientCanvas),
  {
    ssr: false,
  },
);

export function ClientDynamicGradient() {
  return <DynamicGradientCanvas />;
}
