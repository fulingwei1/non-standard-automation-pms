/**
 * Acceptance Management — record detail dialog (checklist + issues)
 */




import { cn } from "../../lib/utils";
import { STATUS_CONFIG, TYPE_CONFIG, RESULT_CONFIG } from "./constants";

// ── Badge helper (local, only needed in this dialog) ─────────────────────────

const getStatusBadge = (status) => {
  const config = STATUS_CONFIG[status] || STATUS_CONFIG.draft;
  return (
    <Badge variant="outline" className={cn("border", config.color)}>
      {config.label}
    </Badge>
  );
};

// ── Checklist stats card ─────────────────────────────────────────────────────

const ChecklistStats = ({ stats }) => (
  <Card className="bg-surface-100/50">
    <CardHeader className="pb-3">
      <CardTitle className="text-base flex items-center gap-2">
        <ClipboardList className="w-4 h-4" />
        检查清单
      </CardTitle>
    </CardHeader>
    <CardContent>
      <div className="grid grid-cols-4 gap-4">
        <div className="text-center">
          <p className="text-2xl font-bold text-white">{stats.total}</p>
          <p className="text-xs text-slate-400">总计</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold text-emerald-400">{stats.passed}</p>
          <p className="text-xs text-slate-400">通过</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold text-red-400">{stats.failed}</p>
          <p className="text-xs text-slate-400">失败</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold text-slate-400">{stats.pending}</p>
          <p className="text-xs text-slate-400">待检</p>
        </div>
      </div>
    </CardContent>
  </Card>
);

// ── Issues stats card ────────────────────────────────────────────────────────

const IssuesStats = ({ stats }) => (
  <Card className="bg-surface-100/50">
    <CardHeader className="pb-3">
      <CardTitle className="text-base flex items-center gap-2">
        <AlertCircle className="w-4 h-4" />
        问题追踪
      </CardTitle>
    </CardHeader>
    <CardContent>
      <div className="grid grid-cols-4 gap-4">
        <div className="text-center">
          <p className="text-2xl font-bold text-white">{stats.total}</p>
          <p className="text-xs text-slate-400">总计</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold text-amber-400">{stats.open}</p>
          <p className="text-xs text-slate-400">待处理</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold text-blue-400">{stats.fixing}</p>
          <p className="text-xs text-slate-400">修复中</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold text-emerald-400">{stats.closed}</p>
          <p className="text-xs text-slate-400">已关闭</p>
        </div>
      </div>
    </CardContent>
  </Card>
);

// ── Dialog content ───────────────────────────────────────────────────────────

const DetailDialogContent = ({ record, onClose }) => {
  const checklist = record.checklist || [];
  const issues = record.issues || [];

  return (
    <DialogContent className="max-w-5xl max-h-[90vh] overflow-y-auto">
      <DialogHeader>
        <DialogTitle className="flex items-center gap-2">
          <ClipboardCheck className="w-5 h-5" />
          {record.acceptance_code} - {record.title}
        </DialogTitle>
        <DialogDescription>
          {record.project_name} | {TYPE_CONFIG[record.acceptance_type]?.label}验收
        </DialogDescription>
      </DialogHeader>

      <div className="space-y-6">
        {/* 基本信息 */}
        <div className="grid grid-cols-3 gap-4">
          <div>
            <p className="text-sm text-slate-400">状态</p>
            <div className="mt-1">{getStatusBadge(record.status)}</div>
          </div>
          <div>
            <p className="text-sm text-slate-400">计划日期</p>
            <p className="text-white mt-1">{record.scheduled_date || "-"}</p>
          </div>
          <div>
            <p className="text-sm text-slate-400">验收地点</p>
            <p className="text-white mt-1">{record.location || "-"}</p>
          </div>
          <div>
            <p className="text-sm text-slate-400">客户代表</p>
            <p className="text-white mt-1">{record.customer_representative || "-"}</p>
          </div>
          <div>
            <p className="text-sm text-slate-400">我方代表</p>
            <p className="text-white mt-1">{record.our_representative || "-"}</p>
          </div>
          <div>
            <p className="text-sm text-slate-400">总体结果</p>
            <p className="text-white mt-1">
              {record.overall_result ? (
                <Badge className={RESULT_CONFIG[record.overall_result]?.color}>
                  {RESULT_CONFIG[record.overall_result]?.label}
                </Badge>
              ) : (
                "-"
              )}
            </p>
          </div>
        </div>

        {/* 检查清单统计 */}
        {record.checklist_stats && <ChecklistStats stats={record.checklist_stats} />}

        {/* 检查清单项 */}
        {checklist.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-slate-400">检查项目</h4>
            <div className="max-h-48 overflow-y-auto space-y-2">
              {checklist.map((item) => (
                <div
                  key={item.id}
                  className="flex items-center justify-between p-3 bg-surface-100 rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <Badge variant="outline" className="text-xs">
                      {item.item_no}
                    </Badge>
                    <span className="text-sm text-white">{item.check_item}</span>
                  </div>
                  <Badge
                    variant="outline"
                    className={cn(
                      "text-xs",
                      item.status === "pass" &&
                        "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
                      item.status === "fail" &&
                        "bg-red-500/20 text-red-400 border-red-500/30",
                      item.status === "pending" &&
                        "bg-slate-500/20 text-slate-400 border-slate-500/30",
                      item.status === "na" &&
                        "bg-slate-500/20 text-slate-500 border-slate-500/30"
                    )}
                  >
                    {item.status}
                  </Badge>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 问题统计 */}
        {record.issues_stats && <IssuesStats stats={record.issues_stats} />}

        {/* 问题列表 */}
        {issues.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-slate-400">问题列表</h4>
            <div className="max-h-48 overflow-y-auto space-y-2">
              {issues.map((issue) => (
                <div
                  key={issue.id}
                  className="flex items-center justify-between p-3 bg-surface-100 rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <Badge
                      variant="outline"
                      className={cn(
                        "text-xs",
                        issue.severity === "critical" &&
                          "bg-red-500/20 text-red-400 border-red-500/30",
                        issue.severity === "major" &&
                          "bg-amber-500/20 text-amber-400 border-amber-500/30",
                        issue.severity === "minor" &&
                          "bg-slate-500/20 text-slate-400 border-slate-500/30"
                      )}
                    >
                      {issue.severity}
                    </Badge>
                    <span className="text-sm text-white">{issue.description}</span>
                  </div>
                  <Badge
                    variant="outline"
                    className={cn(
                      "text-xs",
                      issue.status === "open" &&
                        "bg-amber-500/20 text-amber-400 border-amber-500/30",
                      issue.status === "fixing" &&
                        "bg-blue-500/20 text-blue-400 border-blue-500/30",
                      issue.status === "resolved" &&
                        "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
                      issue.status === "closed" &&
                        "bg-slate-500/20 text-slate-400 border-slate-500/30"
                    )}
                  >
                    {issue.status}
                  </Badge>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <DialogFooter>
        <Button variant="outline" onClick={onClose}>
          关闭
        </Button>
      </DialogFooter>
    </DialogContent>
  );
};

// ── Dialog wrapper ───────────────────────────────────────────────────────────

const DetailDialog = ({ open, onOpenChange, record }) => {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      {record && (
        <DetailDialogContent record={record} onClose={() => onOpenChange(false)} />
      )}
    </Dialog>
  );
};

export default DetailDialog;
