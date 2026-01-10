import * as React from "react";
import { cn } from "../../lib/utils";

const Input = React.forwardRef(
  ({ className, type, icon: Icon, error, ...props }, ref) => {
    return (
      <div className="relative">
        {Icon && (
          <div className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500 pointer-events-none">
            <Icon className="h-4 w-4" />
          </div>
        )}
        <input
          type={type}
          className={cn(
            // Base styles
            "flex w-full h-11 rounded-xl text-sm",
            "bg-white/[0.03] border border-white/10",
            "text-white placeholder:text-slate-500",
            "transition-all duration-200",
            // Padding
            Icon ? "pl-10 pr-4" : "px-4",
            // Focus state
            "focus:outline-none focus:border-primary/50",
            "focus:ring-2 focus:ring-primary/20",
            "focus:bg-white/[0.05]",
            // Hover state
            "hover:border-white/20 hover:bg-white/[0.04]",
            // Error state
            error &&
              "border-red-500/50 focus:border-red-500 focus:ring-red-500/20",
            // Disabled state
            "disabled:opacity-50 disabled:cursor-not-allowed",
            className,
          )}
          ref={ref}
          {...props}
        />
      </div>
    );
  },
);
Input.displayName = "Input";

const InputWithLabel = React.forwardRef(
  ({ label, error, hint, className, ...props }, ref) => {
    return (
      <div className={cn("space-y-2", className)}>
        {label && (
          <label className="text-sm font-medium text-slate-300">{label}</label>
        )}
        <Input ref={ref} error={error} {...props} />
        {(error || hint) && (
          <p
            className={cn("text-xs", error ? "text-red-400" : "text-slate-500")}
          >
            {error || hint}
          </p>
        )}
      </div>
    );
  },
);
InputWithLabel.displayName = "InputWithLabel";

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

export { Input, InputWithLabel, Textarea };
