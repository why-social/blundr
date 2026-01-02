// Original Author: Razvan Albu
// Source: https://git.chalmers.se/courses/dit826/2025/team2
// License: MIT

import { twMerge } from "tailwind-merge";

export const EmphasisText = ({
  text,
  emphasis,
  className = "",
}: {
  text: string;
  emphasis?: "strong" | "weak";
  className?: string;
}) => {
  return (
    <div className={`relative inline-block ${className}`}>
      <h1 className="invisible">{text}</h1>

      {emphasis === "strong" && (
        <>
          <h1 className="absolute -top-3 -left-3 text-red-600 select-none">
            {text}
          </h1>

          <h1 className="absolute -top-2 -left-2 text-red-400 select-none">
            {text}
          </h1>
        </>
      )}

      <h1
        className={twMerge(
          "absolute select-none",
          emphasis === "strong"
            ? "-top-1 -left-1 text-pink-300"
            : "-top-0.5 -left-0.5 text-red-600",
        )}
      >
        {text}
      </h1>

      <h1 className="text-white-500 absolute top-0">{text}</h1>
    </div>
  );
};
