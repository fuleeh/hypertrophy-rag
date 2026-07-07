import { cn } from "@/lib/utils";
import { InputHTMLAttributes, forwardRef } from "react";

const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => {
    return (
      <input
        ref={ref}
        className={cn(
          "w-full rounded-lg border border-border bg-surface px-4 py-3 text-foreground",
          "placeholder:text-muted transition-all duration-300",
          "hover:border-border-hover focus:border-accent focus:ring-0",
          className
        )}
        {...props}
      />
    );
  }
);
Input.displayName = "Input";

export { Input };
