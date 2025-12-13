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
