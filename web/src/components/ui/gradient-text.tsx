import { cn } from "@/lib/utils";

interface GradientTextProps {
  children: React.ReactNode;
  className?: string;
}

function GradientText({ children, className }: GradientTextProps) {
  return (
    <span className={cn("gradient-text", className)}>
      {children}
    </span>
  );
}

export { GradientText };
