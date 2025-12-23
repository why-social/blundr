import * as React from "react";
import { twMerge } from "tailwind-merge";

type ButtonVariant = "primary" | "secondary" | "outline" | "ghost" | "danger";
type ButtonSize = "sm" | "md" | "lg";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  leftIcon?: React.ReactNode;
  blurryBorder?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = "primary",
      size = "md",
      blurryBorder = false,
      leftIcon,
      children,
      ...props
    },
    ref,
  ) => {
    const variants: Record<ButtonVariant, string> = {
      primary:
        "bg-zinc-900 text-zinc-50 hover:bg-zinc-900/90 dark:bg-zinc-50 dark:text-zinc-900 dark:hover:bg-zinc-50/90",
      secondary:
        "bg-zinc-100 text-zinc-900 hover:bg-zinc-100/80 dark:bg-zinc-800 dark:text-zinc-50 dark:hover:bg-zinc-800/80",
      outline:
        "border border-zinc-200 bg-transparent hover:bg-zinc-100 text-zinc-900 dark:border-zinc-800 dark:hover:bg-zinc-800 dark:text-zinc-50",
      ghost:
        "hover:bg-zinc-100 hover:text-zinc-900 dark:hover:bg-zinc-800 dark:hover:text-zinc-50",
      danger: "bg-red-500 text-white hover:bg-red-600 dark:hover:bg-red-600",
    };

    const sizes: Record<ButtonSize, string> = {
      sm: "h-8 px-4 text-sm",
      md: "h-12 px-5 text-md",
      lg: "h-14 px-8 text-lg",
    };

    return (
      <>
        {blurryBorder && (
          <div className="pointer-events-none absolute -inset-0.5 rounded-md bg-linear-to-r from-pink-600 via-fuchsia-400 to-red-400 blur-md" />
        )}
        <button
          ref={ref}
          className={twMerge(
            "inline-flex items-center justify-center rounded-md font-medium ring-offset-white transition-all",
            "duration-200 focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:outline-none active:scale-[0.98]",
            "relative hover:cursor-pointer disabled:pointer-events-none disabled:opacity-50 dark:ring-offset-zinc-950",
            variants[variant],
            sizes[size],
            className,
          )}
          {...props}
        >
          {leftIcon && (
            <span className="mr-2 inline-flex shrink-0">{leftIcon}</span>
          )}
          {children}
        </button>
      </>
    );
  },
);

Button.displayName = "Button";

export { Button };
