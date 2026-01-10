import { motion } from "framer-motion";
import { Loader2 } from "lucide-react";
import { cn } from "../../lib/utils";

export function LoadingSpinner({
  size = "md",
  className,
  text,
  fullScreen = false,
}) {
  const sizeClasses = {
    sm: "w-4 h-4",
    md: "w-8 h-8",
    lg: "w-12 h-12",
    xl: "w-16 h-16",
  };

  const spinner = (
    <div
      className={cn(
        "flex flex-col items-center justify-center gap-3",
        className,
      )}
    >
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
      >
        <Loader2 className={cn("text-primary", sizeClasses[size])} />
      </motion.div>
      {text && <p className="text-sm text-slate-400">{text}</p>}
    </div>
  );

  if (fullScreen) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 flex items-center justify-center">
        {spinner}
      </div>
    );
  }

  return spinner;
}

export function LoadingCard({ className, rows = 3 }) {
  return (
    <div className={cn("space-y-3", className)}>
      {Array.from({ length: rows }).map((_, i) => (
        <div
          key={i}
          className="animate-pulse bg-slate-800/50 rounded-lg h-20"
        />
      ))}
    </div>
  );
}

export function LoadingSkeleton({
  className,
  width = "w-full",
  height = "h-4",
}) {
  return (
    <div
      className={cn(
        "animate-pulse bg-slate-800/50 rounded",
        width,
        height,
        className,
      )}
    />
  );
}
