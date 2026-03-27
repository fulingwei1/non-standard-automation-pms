import { AlertCircle, RefreshCw, Inbox, Lightbulb } from "lucide-react";
import { Button } from "../ui/button";
import { Card, CardContent } from "../ui/card";
import { cn } from "../../lib/utils";
import { getFriendlyError } from "../../utils/friendlyErrors";

export function ErrorMessage({
  error,
  onRetry,
  title,
  className,
  showDetails = false,
}) {
  const friendly = error ? getFriendlyError(error) : null;
  const displayTitle = title || friendly?.title || "加载失败";
  const displayMessage = friendly?.message || error?.message || "未知错误";
  const displaySuggestion = friendly?.suggestion;

  return (
    <Card className={cn("border-red-500/20 bg-red-500/5", className)}>
      <CardContent className="p-6">
        <div className="flex items-start gap-4">
          <AlertCircle className="w-6 h-6 text-red-400 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-red-400 mb-2">{displayTitle}</h3>
            <p className="text-slate-300 mb-3">{displayMessage}</p>
            {displaySuggestion && (
              <div className="flex items-start gap-2 mb-4 p-3 rounded-lg bg-white/[0.03] border border-white/5">
                <Lightbulb className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
                <p className="text-sm text-slate-300">{displaySuggestion}</p>
              </div>
            )}
            {showDetails && error?.response?.data && (
              <details className="mb-4">
                <summary className="text-sm text-slate-500 cursor-pointer mb-2">
                  详细信息
                </summary>
                <pre className="text-xs text-slate-500 bg-slate-900 p-3 rounded overflow-auto">
                  {JSON.stringify(error.response.data, null, 2)}
                </pre>
              </details>
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

export function EmptyState({
  icon: Icon = Inbox,
  title = "暂无数据",
  description,
  action,
  className,
}) {
  const IconComponent = Icon;
  return (
    <Card className={className}>
      <CardContent className="p-12 text-center">
        <IconComponent className="w-16 h-16 text-slate-500 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-white mb-2">{title}</h3>
        {description && <p className="text-slate-400 mb-4">{description}</p>}
        {action && <div className="mt-4">{action}</div>}
      </CardContent>
    </Card>
  );
}
