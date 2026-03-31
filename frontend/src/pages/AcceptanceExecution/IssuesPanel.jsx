import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';
import { cn } from '../../lib/utils';
import { issueSeverityLabels, issueSeverityColors, issueStatusLabels } from './constants';

/**
 * Right sidebar panel listing all reported issues for the acceptance order.
 */
export function IssuesPanel({ issues }) {
    return (
        <Card>
            <CardHeader>
                <CardTitle>问题列表</CardTitle>
            </CardHeader>
            <CardContent>
                {(issues || []).length === 0 ? (
                    <div className="text-center py-8 text-slate-400">暂无问题</div>
                ) : (
                    <div className="space-y-3">
                        {(issues || []).map((issue) => (
                            <IssueRow key={issue.id} issue={issue} />
                        ))}
                    </div>
                )}
            </CardContent>
        </Card>
    );
}

function IssueRow({ issue }) {
    const severityColor = issueSeverityColors[issue.severity] || 'bg-slate-500';
    const severityLabel = issueSeverityLabels[issue.severity] || issue.severity;
    const statusLabel = issueStatusLabels[issue.status] || issue.status;

    return (
        <div className="border rounded-lg p-3">
            <div className="flex items-start justify-between mb-2">
                <div className="flex-1">
                    <div className="font-medium text-sm">
                        {issue.item_name || '通用问题'}
                    </div>
                    <div className="text-xs text-slate-500 mt-1">{issue.category}</div>
                </div>
                <Badge className={cn(severityColor)}>{severityLabel}</Badge>
            </div>
            <div className="text-xs text-slate-600 mt-2">{issue.description}</div>
            <div className="text-xs text-slate-400 mt-1">{statusLabel}</div>
        </div>
    );
}
