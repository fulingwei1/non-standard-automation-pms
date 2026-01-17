import * as React from "react";
import { cva } from "class-variance-authority";
import { cn } from "../../lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium transition-colors",
  {
    variants: {
      variant: {
        default: "bg-primary/15 text-primary border border-primary/30",
        secondary: "bg-white/5 text-slate-400 border border-white/10",
        success:
          "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30",
        warning: "bg-amber-500/15 text-amber-400 border border-amber-500/30",
        danger: "bg-red-500/15 text-red-400 border border-red-500/30",
        info: "bg-blue-500/15 text-blue-400 border border-blue-500/30",
        outline: "bg-transparent text-slate-400 border border-white/20",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  },
);

function Badge({ className, variant, ...props }) {
  return (
    <span className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}

// Health badge with dot indicator
function HealthBadge({ health, className }) {
  const config = {
    H1: { label: "正常", color: "emerald" },
    H2: { label: "风险", color: "amber" },
    H3: { label: "阻塞", color: "red" },
    H4: { label: "完结", color: "slate" },
  };

  const { label, color } = config[health] || config.H1;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium",
        `bg-${color}-500/15 text-${color}-400 border border-${color}-500/30`,
        className,
      )}
    >
      <span className={`w-1.5 h-1.5 rounded-full bg-${color}-500`} />
      {health} {label}
    </span>
  );
}

// Stage badge
function StageBadge({ stage, className }) {
  return (
    <Badge variant="secondary" className={className}>
      {stage}
    </Badge>
  );
}

export { Badge, badgeVariants, HealthBadge, StageBadge };
