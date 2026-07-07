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
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium font-mono",
        variant === "default" && "bg-white/5 text-text-secondary border border-border/60",
        variant === "accent" && "bg-accent/10 text-accent border border-accent/20",
        variant === "success" && "bg-success/10 text-success border border-success/20",
        variant === "warning" && "bg-warning/10 text-warning border border-warning/20",
        variant === "muted" && "bg-white/5 text-text-muted border border-border/40",
        className
      )}
    >
      {children}
    </span>
  );
}

export { Badge };
