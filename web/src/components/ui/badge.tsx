import { cn } from "@/lib/utils";

interface BadgeProps {
  children: React.ReactNode;
  variant?: "default" | "accent" | "success" | "warning" | "muted";
  className?: string;
}

function Badge({ children, variant = "default", className }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
        variant === "default" && "bg-white/10 text-foreground",
        variant === "accent" && "bg-accent/20 text-accent",
        variant === "success" && "bg-success/20 text-success",
        variant === "warning" && "bg-warning/20 text-warning",
        variant === "muted" && "bg-white/5 text-muted",
        className
      )}
    >
      {children}
    </span>
  );
}

export { Badge };
