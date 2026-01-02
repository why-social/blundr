// Original Author: Razvan Albu
// Source: https://git.chalmers.se/courses/dit826/2025/team2
// License: MIT

import React from "react";

interface SpinnerProps {
  size?: "sm" | "md" | "lg";
  color?: string;
  className?: string;
}

const sizeClasses = {
  sm: "w-4 h-4",
  md: "w-8 h-8",
  lg: "w-16 h-16",
};

const Spinner: React.FC<SpinnerProps> = ({
  size = "md",
  color = "border-pink-100",
  className = "",
}) => {
  return (
    <div
      className={`animate-spin rounded-full border-4 border-t-transparent ${color} ${sizeClasses[size]} ${className}`}
    ></div>
  );
};

export default Spinner;
