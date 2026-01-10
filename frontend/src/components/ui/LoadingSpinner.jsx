import { motion } from "framer-motion";
import { Loader2 } from "lucide-react";
import { cn } from "../../lib/utils";

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

export function LoadingCard({ message = "加载中...", className }) {
  return (
    <div className={cn("flex items-center justify-center p-12", className)}>
      <div className="text-center space-y-4">
        <LoadingSpinner size="lg" className="mx-auto" />
        <p className="text-slate-400">{message}</p>
      </div>
    </div>
  );
}

export function LoadingPage({ message = "加载中..." }) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 flex items-center justify-center">
      <div className="text-center space-y-4">
        <LoadingSpinner size="xl" className="mx-auto" />
        <p className="text-slate-400">{message}</p>
      </div>
    </div>
  );
}
