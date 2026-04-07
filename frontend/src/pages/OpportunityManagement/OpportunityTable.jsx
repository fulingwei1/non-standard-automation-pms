



import { formatDateTime } from "@/lib/formatters";
import { stageConfig, isGatePassed } from "./constants";

export default function OpportunityTable({
  opportunities,
  stageUpdating,
  onViewDetail,
  onEdit,
  onOpenGate,
  onStageChange,
  onOpenReview
}) {
  return (
    <Card>
      <CardContent className="p-0">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-800">
                <th className="text-left p-4 text-slate-400 text-sm">商机</th>
                <th className="text-left p-4 text-slate-400 text-sm">客户</th>
                <th className="text-left p-4 text-slate-400 text-sm">阶段</th>
                <th className="text-left p-4 text-slate-400 text-sm">负责人</th>
                <th className="text-left p-4 text-slate-400 text-sm">预估金额</th>
                <th className="text-left p-4 text-slate-400 text-sm">创建时间</th>
                <th className="text-left p-4 text-slate-400 text-sm">操作</th>
              </tr>
            </thead>
            <tbody>
              {(opportunities || []).map((opp) => (
                <tr
                  key={opp.id}
                  className="border-b border-slate-800 hover:bg-slate-800/50"
                >
                  <td className="p-4">
                    <div>
                      <div className="text-white font-medium">{opp.opp_name}</div>
                      <div className="text-xs text-slate-500">{opp.opp_code}</div>
                    </div>
                  </td>
                  <td className="p-4 text-slate-300">{opp.customer_name || "-"}</td>
                  <td className="p-4">
                    <div className="flex items-center gap-2">
                      <select
                        value={opp.stage}
                        onChange={(e) => onStageChange(opp, e.target.value)}
                        disabled={!!stageUpdating[opp.id]}
                        className="bg-slate-900 border border-slate-700 rounded-md px-2 py-1 text-xs text-white"
                      >
                        {Object.entries(stageConfig).map(([key, config]) => (
                          <option key={key} value={key || "unknown"}>
                            {config.label}
                          </option>
                        ))}
                      </select>
                      {stageUpdating[opp.id] && (
                        <span className="text-xs text-slate-500">更新中...</span>
                      )}
                    </div>
                  </td>
                  <td className="p-4 text-blue-400">{opp.owner_name || "-"}</td>
                  <td className="p-4 text-slate-300">
                    {opp.est_amount ? `${parseFloat(opp.est_amount).toLocaleString()} 元` : "-"}
                  </td>
                  <td className="p-4 text-slate-400 text-sm">
                    {formatDateTime(opp.created_at)}
                  </td>
                  <td className="p-4">
                    <div className="flex gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onViewDetail(opp)}
                        className="h-8 w-8 p-0"
                      >
                        <Eye className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onEdit(opp)}
                        className="h-8 w-8 p-0"
                      >
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onOpenGate(opp)}
                        className="h-8 w-8 p-0 text-emerald-400"
                      >
                        <CheckCircle2 className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onOpenReview(opp)}
                        className="h-8 w-8 p-0 text-violet-400"
                        disabled={!isGatePassed(opp.gate_status)}
                        title={
                          isGatePassed(opp.gate_status) ?
                          "" :
                          "阶段门未通过，无法申请评审"
                        }
                      >
                        <FileText className="h-4 w-4" />
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}
