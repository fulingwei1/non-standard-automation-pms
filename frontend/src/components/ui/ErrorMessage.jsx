import { AlertCircle, RefreshCw, XCircle, Lightbulb } from "lucide-react";
import { Card, CardContent } from "./card";
import { Button } from "./button";
import { Badge } from "./badge";
import { cn } from "../../lib/utils";
import { getFriendlyError } from "../../utils/friendlyErrors";

export function ErrorMessage({
  title,
  message,
  error,
  onRetry,
  className,
  variant = "default",
}) {
  // 如果传入了 error 对象，自动转换为友好信息
  const friendly = error ? getFriendlyError(error) : null;
  const displayTitle = title || friendly?.title || "加载失败";
  const displayMessage = message || friendly?.message || "数据加载失败，请稍后重试";
  const displaySuggestion = friendly?.suggestion;

  const variantStyles = {
    default: "bg-red-500/10 border-red-500/20",
    warning: "bg-amber-500/10 border-amber-500/20",
    info: "bg-blue-500/10 border-blue-500/20",
  };

  return (
    <Card className={cn("border", variantStyles[variant], className)}>
      <CardContent className="p-6">
        <div className="flex items-start gap-4">
          <div className="flex-shrink-0">
            {variant === "warning" ? (
              <AlertCircle className="w-6 h-6 text-amber-400" />
            ) : variant === "info" ? (
              <AlertCircle className="w-6 h-6 text-blue-400" />
            ) : (
              <XCircle className="w-6 h-6 text-red-400" />
            )}
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="text-lg font-semibold text-white mb-1">{displayTitle}</h3>
            <p className="text-slate-400 text-sm">{displayMessage}</p>
            {displaySuggestion && (
              <div className="flex items-start gap-2 mt-3 p-3 rounded-lg bg-white/[0.03] border border-white/5">
                <Lightbulb className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
                <p className="text-sm text-slate-300">{displaySuggestion}</p>
              </div>
            )}
            {onRetry && (
              <Button
                variant="outline"
                size="sm"
                onClick={onRetry}
                className="mt-4 gap-2"
              >
                <RefreshCw className="w-4 h-4" />
                重试
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export function EmptyState({
  icon: Icon,
  title = "暂无数据",
  message = "当前没有数据可显示",
  action,
  actionLabel,
  className,
}) {
  return (
    <Card className={className}>
      <CardContent className="p-12 text-center">
        {Icon && (
          <div className="flex justify-center mb-4">
            <Icon className="w-16 h-16 text-slate-500" />
          </div>
        )}
        <h3 className="text-lg font-semibold text-white mb-2">{title}</h3>
        <p className="text-slate-400 mb-4">{message}</p>
        {action && actionLabel && (
          <Button onClick={action} variant="outline">
            {actionLabel}
          </Button>
        )}
      </CardContent>
    </Card>
  );
}

export function ApiIntegrationError({
  error,
  apiEndpoint,
  onRetry,
  className,
}) {
  const friendly = getFriendlyError(error);

  return (
    <Card
      className={cn("border-2 border-amber-500/30 bg-amber-500/5", className)}
    >
      <CardContent className="p-6">
        <div className="flex items-start gap-4">
          <div className="flex-shrink-0">
            <AlertCircle className="w-6 h-6 text-amber-400" />
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="text-lg font-semibold text-amber-400 mb-2">
              {friendly.title}
            </h3>

            <p className="text-slate-300 mb-2">{friendly.message}</p>

            {friendly.suggestion && (
              <div className="flex items-start gap-2 mt-2 mb-4 p-3 rounded-lg bg-white/[0.03] border border-white/5">
                <Lightbulb className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
                <p className="text-sm text-slate-300">{friendly.suggestion}</p>
              </div>
            )}

            {onRetry && (
              <Button
                variant="outline"
                size="sm"
                onClick={onRetry}
                className="gap-2"
              >
                <RefreshCw className="w-4 h-4" />
                重试
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
