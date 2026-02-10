import * as React from "react";
import { cn } from "../../lib/utils";

const Card = React.forwardRef(({ className, hover = true, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      "rounded-2xl",
      "bg-gradient-to-br from-white/[0.05] to-white/[0.02]",
      "border border-white/10",
      hover && [
        "transition-all duration-300",
        "hover:border-white/20",
        "hover:shadow-lg hover:shadow-violet-500/10",
      ],
      className,
    )}
    {...props}
  />
));
Card.displayName = "Card";

const CardHeader = React.forwardRef(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex flex-col space-y-1.5 p-5 pb-0", className)}
    {...props}
  />
));
CardHeader.displayName = "CardHeader";

const CardTitle = React.forwardRef(({ className, ...props }, ref) => (
  <h3
    ref={ref}
    className={cn(
      "text-lg font-semibold leading-none tracking-tight",
      className,
    )}
    {...props}
  />
));
CardTitle.displayName = "CardTitle";

const CardDescription = React.forwardRef(({ className, ...props }, ref) => (
  <p ref={ref} className={cn("text-sm text-slate-400", className)} {...props} />
));
CardDescription.displayName = "CardDescription";

const CardContent = React.forwardRef(({ className, ...props }, ref) => (
  <div ref={ref} className={cn("p-5", className)} {...props} />
));
CardContent.displayName = "CardContent";

const CardFooter = React.forwardRef(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex items-center p-5 pt-0", className)}
    {...props}
  />
));
CardFooter.displayName = "CardFooter";

// Dashboard Stat Card
const DashboardStatCard = React.forwardRef(
  (
    {
      icon: Icon,
      label,
      value,
      change,
      trend,
      description,
      loading = false,
      iconColor = "text-primary",
      iconBg = "bg-gradient-to-br from-primary/20 to-indigo-500/10",
      className,
      onClick,
      ...props
    },
    ref,
  ) => {
    if (loading) {
      return (
        <Card ref={ref} className={cn("p-5", className)} {...props}>
          <div className="animate-pulse">
            <div className="h-10 w-10 rounded-xl bg-white/10 mb-4" />
            <div className="h-3 w-20 rounded bg-white/10 mb-3" />
            <div className="h-6 w-16 rounded bg-white/10" />
          </div>
        </Card>
      );
    }

    const resolvedTrend = trend || "neutral";

    return (
      <Card
        ref={ref}
        className={cn("p-5 group", onClick && "cursor-pointer", className)}
        onClick={onClick}
        {...props}
      >
        <div className="flex items-center justify-between mb-4">
          <div
            className={cn(
              "p-2.5 rounded-xl",
              iconBg,
              "ring-1 ring-primary/20",
            )}
          >
            {Icon && <Icon className={cn("h-5 w-5", iconColor)} />}
          </div>

          {change && (
            <div
              className={cn(
                "flex items-center gap-1 text-xs font-medium px-2 py-1 rounded-full",
                resolvedTrend === "up"
                  ? "text-emerald-400 bg-emerald-500/10"
                  : resolvedTrend === "down"
                    ? "text-red-400 bg-red-500/10"
                    : "text-slate-400 bg-slate-500/10",
              )}
            >
              {resolvedTrend === "up" ? "↑" : resolvedTrend === "down" ? "↓" : ""}
              {change}
            </div>
          )}
        </div>

        <p className="text-sm text-slate-400 mb-1">{label}</p>
        <p className="text-2xl font-semibold text-white tracking-tight">
          {value}
        </p>
        {description && (
          <p className="text-xs text-slate-500 mt-1">{description}</p>
        )}
      </Card>
    );
  },
);
DashboardStatCard.displayName = "DashboardStatCard";


export {
  Card,
  CardHeader,
  CardFooter,
  CardTitle,
  CardDescription,
  CardContent,
  DashboardStatCard,
};
