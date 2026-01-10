import { cn } from "../../lib/utils";

function Skeleton({ className, ...props }) {
  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-lg bg-white/[0.06]",
        "after:absolute after:inset-0",
        "after:bg-gradient-to-r after:from-transparent after:via-white/10 after:to-transparent",
        "after:animate-shimmer",
        className,
      )}
      {...props}
    />
  );
}

// Text skeleton with multiple lines
function SkeletonText({ lines = 1, className }) {
  return (
    <div className={cn("space-y-2", className)}>
      {Array(lines)
        .fill(null)
        .map((_, i) => (
          <Skeleton
            key={i}
            className={cn(
              "h-4",
              i === lines - 1 && lines > 1 ? "w-3/4" : "w-full",
            )}
          />
        ))}
    </div>
  );
}

// Avatar skeleton
function SkeletonAvatar({ className, size = "default" }) {
  const sizes = {
    sm: "h-8 w-8",
    default: "h-10 w-10",
    lg: "h-12 w-12",
    xl: "h-16 w-16",
  };

  return <Skeleton className={cn("rounded-full", sizes[size], className)} />;
}

// Card skeleton
function SkeletonCard({ className }) {
  return (
    <div
      className={cn(
        "rounded-2xl border border-white/10 bg-white/[0.02] p-5 space-y-4",
        className,
      )}
    >
      <div className="flex items-center gap-3">
        <SkeletonAvatar />
        <div className="flex-1 space-y-2">
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-3 w-1/2" />
        </div>
      </div>
      <div className="flex gap-2">
        <Skeleton className="h-6 w-16 rounded-full" />
        <Skeleton className="h-6 w-20 rounded-full" />
      </div>
      <div className="space-y-2">
        <Skeleton className="h-2 w-full rounded-full" />
        <div className="flex justify-between">
          <Skeleton className="h-3 w-12" />
          <Skeleton className="h-3 w-8" />
        </div>
      </div>
    </div>
  );
}

// Table skeleton
function SkeletonTable({ rows = 5, columns = 5, className }) {
  return (
    <div
      className={cn(
        "rounded-xl border border-white/10 overflow-hidden",
        className,
      )}
    >
      {/* Header */}
      <div className="flex bg-white/[0.02] p-4 gap-4">
        {Array(columns)
          .fill(null)
          .map((_, i) => (
            <Skeleton key={i} className="h-4 flex-1" />
          ))}
      </div>
      {/* Body */}
      <div className="divide-y divide-white/5">
        {Array(rows)
          .fill(null)
          .map((_, i) => (
            <div key={i} className="flex p-4 gap-4">
              {Array(columns)
                .fill(null)
                .map((_, j) => (
                  <Skeleton key={j} className="h-4 flex-1" />
                ))}
            </div>
          ))}
      </div>
    </div>
  );
}

// Project list skeleton
function SkeletonProjectList({ count = 3 }) {
  return (
    <div className="space-y-4">
      {Array(count)
        .fill(null)
        .map((_, i) => (
          <SkeletonCard key={i} />
        ))}
    </div>
  );
}

export {
  Skeleton,
  SkeletonText,
  SkeletonAvatar,
  SkeletonCard,
  SkeletonTable,
  SkeletonProjectList,
};
