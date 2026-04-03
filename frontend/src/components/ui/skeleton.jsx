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

// Dashboard stats skeleton
function SkeletonDashboardStats({ columns = 4, className }) {
  return (
    <div
      className={cn(
        "grid grid-cols-1 sm:grid-cols-2 gap-4",
        columns === 4 && "lg:grid-cols-4",
        columns === 3 && "lg:grid-cols-3",
        className,
      )}
    >
      {Array(columns)
        .fill(null)
        .map((_, i) => (
          <div
            key={i}
            className="rounded-2xl border border-white/10 bg-white/[0.02] p-5 space-y-3"
          >
            <div className="flex items-center justify-between">
              <Skeleton className="h-4 w-20" />
              <Skeleton className="h-8 w-8 rounded-lg" />
            </div>
            <Skeleton className="h-8 w-16" />
            <Skeleton className="h-3 w-24" />
          </div>
        ))}
    </div>
  );
}

// Dashboard full page skeleton
function SkeletonDashboard({ className }) {
  return (
    <div className={cn("space-y-6", className)}>
      {/* Header */}
      <div className="space-y-2">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-4 w-72" />
      </div>
      {/* Stats */}
      <SkeletonDashboardStats />
      {/* Content area */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <SkeletonCard className="h-80" />
        </div>
        <SkeletonCard className="h-80" />
      </div>
    </div>
  );
}

// Project detail skeleton
function SkeletonProjectDetail({ className }) {
  return (
    <div className={cn("space-y-6", className)}>
      {/* Header */}
      <div className="flex items-center space-x-4">
        <Skeleton className="h-10 w-10 rounded-lg" />
        <div className="space-y-2 flex-1">
          <Skeleton className="h-7 w-64" />
          <Skeleton className="h-4 w-96" />
        </div>
      </div>
      {/* Stat cards */}
      <SkeletonDashboardStats />
      {/* Tab nav */}
      <Skeleton className="h-10 w-[600px] rounded-lg" />
      {/* Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="rounded-2xl border border-white/10 bg-white/[0.02] p-6 space-y-4">
            <Skeleton className="h-6 w-32" />
            <div className="grid grid-cols-2 gap-4">
              {Array(6)
                .fill(null)
                .map((_, i) => (
                  <div key={i} className="space-y-2">
                    <Skeleton className="h-3 w-16" />
                    <Skeleton className="h-5 w-28" />
                  </div>
                ))}
            </div>
          </div>
          <SkeletonCard />
        </div>
        <div className="space-y-6">
          <SkeletonCard />
          <SkeletonCard />
        </div>
      </div>
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
  SkeletonDashboardStats,
  SkeletonDashboard,
  SkeletonProjectDetail,
};
