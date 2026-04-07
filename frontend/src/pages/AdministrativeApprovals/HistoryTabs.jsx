import { CheckCircle2, XCircle, Clock } from "lucide-react";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function EmptyState({ Icon, message }) {
  return (
    <Card>
      <CardContent className="p-12 text-center">
        <Icon className="h-12 w-12 text-slate-600 mx-auto mb-4" />
        <p className="text-slate-400">{message}</p>
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Approved tab
// ---------------------------------------------------------------------------

/**
 * Props:
 *   approvedList — array of approved approval items
 */
export function ApprovedTab({ approvedList }) {
  if (!approvedList.length) {
    return <EmptyState Icon={CheckCircle2} message="暂无已批准记录" />;
  }

  const approvedBadge = (
    <Badge className="bg-green-500/20 text-green-400 border-green-500/30">
      <CheckCircle2 className="w-3 h-3 mr-1" />
      已批准
    </Badge>
  );

  return (
    <div className="space-y-4">
      {(approvedList || []).map((approval) => (
        <ApprovalCard
          key={approval.id}
          approval={approval}
          statusBadge={approvedBadge}
        />
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Rejected tab
// ---------------------------------------------------------------------------

/**
 * Props:
 *   rejectedList — array of rejected approval items
 */
export function RejectedTab({ rejectedList }) {
  if (!rejectedList.length) {
    return <EmptyState Icon={XCircle} message="暂无已拒绝记录" />;
  }

  const rejectedBadge = (
    <Badge className="bg-red-500/20 text-red-400 border-red-500/30">
      <XCircle className="w-3 h-3 mr-1" />
      已拒绝
    </Badge>
  );

  return (
    <div className="space-y-4">
      {(rejectedList || []).map((approval) => (
        <ApprovalCard
          key={approval.id}
          approval={approval}
          statusBadge={rejectedBadge}
        />
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// History tab (combined, sorted by resolved time)
// ---------------------------------------------------------------------------

/**
 * Props:
 *   approvedList — array
 *   rejectedList — array
 */
export function HistoryTab({ approvedList, rejectedList }) {
  const isEmpty = approvedList.length === 0 && rejectedList.length === 0;

  if (isEmpty) {
    return <EmptyState Icon={Clock} message="暂无审批历史记录" />;
  }

  const combined = [
    ...(approvedList || []).map((item) => ({ ...item, _status: "approved" })),
    ...(rejectedList || []).map((item) => ({ ...item, _status: "rejected" })),
  ].sort((a, b) => {
    const timeA = a.approvedTime || a.rejectedTime || a.submitTime || "";
    const timeB = b.approvedTime || b.rejectedTime || b.submitTime || "";
    return timeB.localeCompare(timeA);
  });

  return (
    <div className="space-y-4">
      {combined.map((approval) => {
        const isApproved = approval._status === "approved";
        const statusBadge = isApproved ? (
          <Badge className="bg-green-500/20 text-green-400 border-green-500/30">
            <CheckCircle2 className="w-3 h-3 mr-1" />
            已批准
          </Badge>
        ) : (
          <Badge className="bg-red-500/20 text-red-400 border-red-500/30">
            <XCircle className="w-3 h-3 mr-1" />
            已拒绝
          </Badge>
        );

        return (
          <ApprovalCard
            key={`${approval._status}-${approval.id}`}
            approval={approval}
            statusBadge={statusBadge}
          />
        );
      })}
    </div>
  );
}
