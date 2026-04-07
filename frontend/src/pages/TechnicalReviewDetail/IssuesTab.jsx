

import { formatDate } from "../../lib/utils";
import { getStatusBadge, ISSUE_LEVEL_COLORS } from "./constants";

const ISSUE_STATUS_LABELS = {
    OPEN: "开放",
    PROCESSING: "处理中",
    RESOLVED: "已解决",
    VERIFIED: "已验证",
    CLOSED: "已关闭",
};

/**
 * Renders the "问题" (Issues) tab content.
 */
export function IssuesTab({ isNew, issues, users, onCreateIssue }) {
    return (
        <div className="space-y-4">
            <Card className="bg-slate-900/50 border-slate-800">
                <CardHeader className="flex flex-row items-center justify-between">
                    <CardTitle>评审问题</CardTitle>
                    {!isNew && (
                        <Button
                            size="sm"
                            onClick={onCreateIssue}
                            className="bg-blue-600 hover:bg-blue-700"
                        >
                            <Plus className="w-4 h-4 mr-2" />
                            创建问题
                        </Button>
                    )}
                </CardHeader>
                <CardContent>
                    {(issues?.length ?? 0) === 0 ? (
                        <p className="text-center text-slate-400 py-8">暂无问题</p>
                    ) : (
                        <div className="space-y-3">
                            {(issues || []).map((issue) => {
                                const assignee = (users || []).find(
                                    (u) => u.id === issue.assignee_id
                                );
                                const assigneeName =
                                    assignee?.real_name ||
                                    assignee?.username ||
                                    `用户${issue.assignee_id}`;

                                return (
                                    <div
                                        key={issue.id}
                                        className="p-4 bg-slate-800/50 rounded-lg space-y-2"
                                    >
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-2">
                                                <Badge
                                                    className={
                                                        ISSUE_LEVEL_COLORS[issue.issue_level] ||
                                                        "bg-blue-500/20 text-blue-400"
                                                    }
                                                >
                                                    {issue.issue_level}类问题
                                                </Badge>
                                                <span className="text-sm text-slate-400">
                                                    {issue.issue_no}
                                                </span>
                                            </div>
                                            <Badge className={getStatusBadge(issue.status).color}>
                                                {ISSUE_STATUS_LABELS[issue.status] ?? issue.status}
                                            </Badge>
                                        </div>
                                        <p className="text-slate-200">{issue.description}</p>
                                        <div className="flex items-center gap-4 text-sm text-slate-400">
                                            <span>类别: {issue.category}</span>
                                            <span>责任人: {assigneeName}</span>
                                            <span>
                                                期限: {formatDate(issue.deadline, "YYYY-MM-DD")}
                                            </span>
                                        </div>
                                        {issue.solution && (
                                            <p className="text-sm text-slate-300">
                                                解决方案: {issue.solution}
                                            </p>
                                        )}
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}
