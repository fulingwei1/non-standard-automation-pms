import { motion } from "framer-motion";
import { ArrowUpRight, ArrowDownRight } from "lucide-react";
import { cn } from "../../lib/utils";
import { fadeIn } from "../../lib/animations";

export function StatCard({
  title,
  value,
  subtitle,
  trend,
  icon: Icon,
  color = "text-white",
  iconColor,
  valueColor,
  bg = "bg-slate-800",
  size = "normal",
  layout = "default",
  trendSuffix = "%",
  trendLabel = "vs 上月",
  trendShowSign = true,
  showDecoration = true,
  headerSlot,
  titleClassName,
  valueClassName,
  subtitleClassName,
  cardClassName,
  iconWrapperClassName,
  iconClassName,
  hoverScale,
  onClick,
  children
}) {
  const textSize =
    size === "large" ? "text-3xl" : size === "small" ? "text-xl" : "text-2xl";
  const resolvedIconColor = iconColor || color;
  const resolvedValueColor = valueColor || color;
  const trendMagnitude = trendShowSign ? trend : Math.abs(trend);
  const trendValue =
    trendShowSign && trend > 0
      ? `+${trend}${trendSuffix}`
      : `${trendMagnitude}${trendSuffix}`;
  return (
    <motion.div
      variants={fadeIn}
      onClick={onClick}
      whileHover={hoverScale ? { scale: hoverScale } : undefined}
      className={cn(
        "relative overflow-hidden rounded-lg border border-slate-700/50 bg-gradient-to-br from-slate-800/50 to-slate-900/50 p-5 backdrop-blur transition-all hover:border-slate-600/80 hover:shadow-lg",
        onClick && "cursor-pointer",
        cardClassName
      )}
    >
      {headerSlot ? headerSlot : null}
      {layout === "compact" ? (
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {Icon && (
              <div className={cn("rounded-lg p-3 bg-opacity-20", bg, iconWrapperClassName)}>
                <Icon className={cn("h-6 w-6", resolvedIconColor, iconClassName)} />
              </div>
            )}
            <div>
              <p className={cn("text-sm text-slate-400 mb-1", titleClassName)}>{title}</p>
              <p className={cn("font-bold", textSize, resolvedValueColor, valueClassName)}>{value}</p>
              {subtitle && (
                <p className={cn("text-xs text-slate-500 mt-1", subtitleClassName)}>{subtitle}</p>
              )}
            </div>
          </div>
          {trend !== undefined && (
            <div className="flex items-center gap-1 text-xs">
              {trend > 0 ? (
                <>
                  <ArrowUpRight className="w-3 h-3 text-emerald-400" />
                  <span className="text-emerald-400">{trendValue}</span>
                </>
              ) : trend < 0 ? (
                <>
                  <ArrowDownRight className="w-3 h-3 text-red-400" />
                  <span className="text-red-400">{trendValue}</span>
                </>
              ) : null}
              {trend !== 0 && trendLabel ? (
                <span className="text-slate-500">{trendLabel}</span>
              ) : null}
            </div>
          )}
        </div>
      ) : layout === "row" ? (
        <>
          <div className="flex items-center justify-between">
            <p className={cn("text-sm text-slate-400", titleClassName)}>{title}</p>
            <div className="flex items-center gap-2">
              <p className={cn("font-bold", textSize, resolvedValueColor, valueClassName)}>{value}</p>
              {Icon && (
                <div className={cn("rounded-lg p-2 bg-opacity-20", bg, iconWrapperClassName)}>
                  <Icon className={cn("h-5 w-5", resolvedIconColor, iconClassName)} />
                </div>
              )}
            </div>
          </div>
          {subtitle && (
            <p className={cn("text-xs text-slate-500 mt-2", subtitleClassName)}>{subtitle}</p>
          )}
          {trend !== undefined && (
            <div className="flex items-center gap-1 mt-2 text-xs">
              {trend > 0 ? (
                <>
                  <ArrowUpRight className="w-3 h-3 text-emerald-400" />
                  <span className="text-emerald-400">{trendValue}</span>
                </>
              ) : trend < 0 ? (
                <>
                  <ArrowDownRight className="w-3 h-3 text-red-400" />
                  <span className="text-red-400">{trendValue}</span>
                </>
              ) : null}
              {trend !== 0 && trendLabel ? (
                <span className="text-slate-500">{trendLabel}</span>
              ) : null}
            </div>
          )}
        </>
      ) : (
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <p className={cn("text-sm text-slate-400 mb-2", titleClassName)}>{title}</p>
            <p className={cn("font-bold mb-1", textSize, resolvedValueColor, valueClassName)}>{value}</p>
            {subtitle && (
              <p className={cn("text-xs text-slate-500", subtitleClassName)}>{subtitle}</p>
            )}
            {trend !== undefined && (
              <div className="flex items-center gap-1 mt-2">
                {trend > 0 ? (
                  <>
                    <ArrowUpRight className="w-3 h-3 text-emerald-400" />
                    <span className="text-xs text-emerald-400">{trendValue}</span>
                  </>
                ) : trend < 0 ? (
                  <>
                    <ArrowDownRight className="w-3 h-3 text-red-400" />
                    <span className="text-xs text-red-400">{trendValue}</span>
                  </>
                ) : null}
                {trend !== 0 && trendLabel ? (
                  <span className="text-xs text-slate-500 ml-1">{trendLabel}</span>
                ) : null}
              </div>
            )}
          </div>
          {Icon && (
            <div className={cn("rounded-lg p-3 bg-opacity-20", bg, iconWrapperClassName)}>
              <Icon className={cn("h-6 w-6", resolvedIconColor, iconClassName)} />
            </div>
          )}
        </div>
      )}
      {children ? <div className="mt-3">{children}</div> : null}
      {showDecoration ? (
        <div className="absolute right-0 bottom-0 h-20 w-20 rounded-full bg-gradient-to-br from-purple-500/10 to-transparent blur-2xl opacity-30" />
      ) : null}
    </motion.div>
  );
}

export default StatCard;
