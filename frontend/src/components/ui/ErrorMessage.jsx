import { cn } from "../../lib/utils";

export function ErrorMessage({
  title = "加载失败",
  message = "数据加载失败，请稍后重试",
  onRetry,
  className,
  variant = "default",
}) {
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
            <h3 className="text-lg font-semibold text-white mb-1">{title}</h3>
            <p className="text-slate-400 text-sm">{message}</p>
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
  // 处理 FastAPI 的验证错误格式 (detail 可能是数组)
  const rawDetail = error?.response?.data?.detail;
  let errorMessage = "API 调用失败";
  if (typeof rawDetail === "string") {
    errorMessage = rawDetail;
  } else if (Array.isArray(rawDetail)) {
    // FastAPI validation errors: [{type, loc, msg, input}, ...]
    errorMessage = rawDetail
      .map((e) => e.msg || e.message || JSON.stringify(e))
      .join("; ");
  } else if (error?.message) {
    errorMessage = error.message;
  }

  const statusCode = error?.response?.status;
  const statusText = error?.response?.statusText;

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
            <div className="flex items-center gap-2 mb-2">
              <h3 className="text-lg font-semibold text-amber-400">
                ⚠️ API 集成未完成
              </h3>
              {statusCode && (
                <Badge variant="outline" className="text-xs">
                  {statusCode} {statusText}
                </Badge>
              )}
            </div>

            <p className="text-slate-300 mb-2">{errorMessage}</p>

            {apiEndpoint && (
              <p className="text-xs text-slate-500 mb-3">
                API 端点:{" "}
                <code className="bg-slate-800 px-1 py-0.5 rounded">
                  {apiEndpoint}
                </code>
              </p>
            )}

            <div className="bg-slate-900/50 border border-slate-700 rounded p-3 mb-4">
              <p className="text-xs text-amber-300 font-medium mb-1">💡 说明</p>
              <p className="text-xs text-slate-400">
                后端 API 端点可能未实现或不可用。此页面已移除 fallback 逻辑，
                以确保能清楚识别 API 集成状态。
              </p>
            </div>

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
