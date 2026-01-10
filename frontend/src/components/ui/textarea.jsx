import * as React from "react";
import { cn } from "../../lib/utils";

const Textarea = React.forwardRef(({ className, error, ...props }, ref) => {
  return (
    <textarea
      className={cn(
        "flex w-full min-h-[100px] rounded-xl text-sm",
        "bg-white/[0.03] border border-white/10",
        "text-white placeholder:text-slate-500",
        "transition-all duration-200",
        "px-4 py-3",
        "focus:outline-none focus:border-primary/50",
        "focus:ring-2 focus:ring-primary/20",
        "focus:bg-white/[0.05]",
        "hover:border-white/20 hover:bg-white/[0.04]",
        error && "border-red-500/50 focus:border-red-500 focus:ring-red-500/20",
        "disabled:opacity-50 disabled:cursor-not-allowed",
        "resize-none",
        className,
      )}
      ref={ref}
      {...props}
    />
  );
});
Textarea.displayName = "Textarea";

export { Textarea };
