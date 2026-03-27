import { motion } from "framer-motion";
import { Loader2 } from "lucide-react";
import { cn } from "../../lib/utils";
import { SkeletonDashboard } from "./skeleton";

export function LoadingSpinner({ size = "md", className }) {
  const sizeClasses = {
    sm: "w-4 h-4",
    md: "w-6 h-6",
    lg: "w-8 h-8",
    xl: "w-12 h-12",
  };

  return (
    <motion.div
      animate={{ rotate: 360 }}
      transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
      className={cn(sizeClasses[size], className)}
    >
      <Loader2 className="w-full h-full text-primary" />
    </motion.div>
  );
}

export function LoadingCard({ message, className }) {
  return (
    <div className={cn("p-6", className)}>
      <div className="space-y-4">
        <div className="animate-pulse space-y-3">
          <div className="h-5 bg-white/[0.06] rounded w-1/3" />
          <div className="h-4 bg-white/[0.06] rounded w-full" />
          <div className="h-4 bg-white/[0.06] rounded w-2/3" />
        </div>
        {message && (
          <p className="text-sm text-slate-500">{message}</p>
        )}
      </div>
    </div>
  );
}

export function LoadingPage({ message }) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-6">
      <SkeletonDashboard />
      {message && (
        <p className="text-center text-slate-500 mt-4">{message}</p>
      )}
    </div>
  );
}
