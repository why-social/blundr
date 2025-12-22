"use client";

import { useEffect, useState, useRef } from "react";
import Image from "next/image";

type AmbientCueProps = {
  images: string[];
  durationMs?: number;
  minIntervalMs?: number;
  maxIntervalMs?: number;
  minSize?: number;
  maxSize?: number;
};

type Cue = {
  id: number;
  image: string;
  size: number;
  style: React.CSSProperties;
};

export default function AmbientCue({
  images,
  durationMs = 1500,
  minIntervalMs = 400,
  maxIntervalMs = 1200,
  minSize = 40,
  maxSize = 110,
}: AmbientCueProps) {
  const [cues, setCues] = useState<Cue[]>([]);
  const idCounter = useRef(0);

  useEffect(() => {
    if (!images.length) {
      return;
    }

    let mounted = true;

    const spawnCue = () => {
      if (!mounted) {
        return;
      }

      const id = idCounter.current++;
      const size = minSize + Math.random() * (maxSize - minSize);
      const left = 10 + Math.random() * 80;
      const top = 10 + Math.random() * 80;
      const rotation = Math.random() * 24 - 12;

      const newCue: Cue = {
        id,
        image: images[Math.floor(Math.random() * images.length)],
        size,
        style: {
          position: "absolute",
          left: `${left}%`,
          top: `${top}%`,
          width: `${size}px`,
          height: `${size}px`,
          transform: `translate(-50%, -40%) rotate(${rotation}deg)`,
          pointerEvents: "none",
          opacity: 0,
          transition: "transform 0.3s ease, opacity 0.3s ease",
        },
      };

      setCues((prev) => [...prev, newCue]);

      requestAnimationFrame(() => {
        setCues((prev) =>
          prev.map((cue) =>
            cue.id === id
              ? {
                  ...cue,
                  style: {
                    ...cue.style,
                    transform: `translate(-50%, -50%) rotate(${rotation}deg)`,
                    opacity: 1,
                  },
                }
              : cue,
          ),
        );
      });

      setTimeout(() => {
        setCues((prev) =>
          prev.map((cue) =>
            cue.id === id
              ? { ...cue, style: { ...cue.style, opacity: 0 } }
              : cue,
          ),
        );

        setTimeout(() => {
          setCues((prev) => prev.filter((cue) => cue.id !== id));
        }, 500);
      }, durationMs);

      const nextInterval =
        minIntervalMs + Math.random() * (maxIntervalMs - minIntervalMs);
      setTimeout(spawnCue, nextInterval);
    };

    spawnCue();

    return () => {
      mounted = false;
    };
  }, [images, durationMs, minIntervalMs, maxIntervalMs, minSize, maxSize]);

  return (
    <>
      {cues.map((cue) => (
        <div
          key={cue.id}
          style={cue.style}
        >
          <Image
            src={cue.image}
            alt="Ambient cue"
            fill
            className="object-contain"
            sizes={`${cue.size}px`}
          />
        </div>
      ))}
    </>
  );
}
