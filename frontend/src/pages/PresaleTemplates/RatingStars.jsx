import { Star } from "lucide-react";

import { cn } from "../../lib/utils";

export function RatingStars({ value }) {
  return (
    <div className="flex items-center gap-1">
      {[1, 2, 3, 4, 5].map((star) => (
        <Star
          key={star}
          className={cn(
            "h-4 w-4",
            star <= Math.round(value)
              ? "text-amber-400 fill-amber-400"
              : "text-slate-600",
          )}
        />
      ))}
    </div>
  );
}
