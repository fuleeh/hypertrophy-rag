"use client";

import { cn } from "@/lib/utils";
import { ButtonHTMLAttributes, forwardRef } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "ghost" | "outline";
  size?: "sm" | "md" | "lg";
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", size = "md", children, ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(
          "inline-flex items-center justify-center rounded-full font-medium transition-all duration-200",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/30",
          "disabled:pointer-events-none disabled:opacity-50",
          variant === "default" && "bg-accent text-white hover:bg-accent-hover",
          variant === "ghost" && "text-text-muted hover:text-text hover:bg-white/5",
          variant === "outline" && "border border-border text-text-secondary hover:border-border-hover hover:text-text",
          size === "sm" && "h-8 px-3 text-xs",
          size === "md" && "h-10 px-5 text-sm",
          size === "lg" && "h-11 px-6 text-sm",
          className
        )}
        {...props}
      >
        {children}
      </button>
    );
  }
);
Button.displayName = "Button";

export { Button };
export type { ButtonProps };
