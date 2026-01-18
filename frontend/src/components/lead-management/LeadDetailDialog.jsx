

import { cn } from "../../lib/utils";

export default function LeadDetailDialog({
  open,
  onOpenChange,
  lead,
  statusConfig,
  followUps,
  onAddFollowUp,
}) {
  if (!lead) {return null;}

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>线索详情</DialogTitle>
          <DialogDescription>查看线索详细信息和跟进记录</DialogDescription>
        </DialogHeader>
        <div className="space-y-6">
          {/* 基本信息 */}
          <div>
            <h3 className="text-lg font-semibold mb-4">基本信息</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-slate-400">线索编码</Label>
                <p className="text-white">{lead.lead_code}</p>
              </div>
              <div>
                <Label className="text-slate-400">状态</Label>
                <Badge
                  className={cn(
                    statusConfig[lead.status]?.color,
                    "mt-1"
                  )}
                >
                  {statusConfig[lead.status]?.label}
                </Badge>
              </div>
              <div>
                <Label className="text-slate-400">客户名称</Label>
                <p className="text-white">{lead.customer_name}</p>
              </div>
              <div>
                <Label className="text-slate-400">来源</Label>
                <p className="text-white">{lead.source || "-"}</p>
              </div>
              <div>
                <Label className="text-slate-400">行业</Label>
                <p className="text-white">{lead.industry || "-"}</p>
              </div>
              <div>
                <Label className="text-slate-400">联系人</Label>
                <p className="text-white">{lead.contact_name || "-"}</p>
              </div>
              <div>
                <Label className="text-slate-400">联系电话</Label>
                <p className="text-white">{lead.contact_phone || "-"}</p>
              </div>
              <div>
                <Label className="text-slate-400">创建时间</Label>
                <p className="text-white">
                  {lead.created_at
                    ? new Date(lead.created_at).toLocaleString("zh-CN")
                    : "-"}
                </p>
              </div>
              <div className="col-span-2">
                <Label className="text-slate-400">需求摘要</Label>
                <p className="text-white mt-1">{lead.demand_summary || "-"}</p>
              </div>
            </div>
          </div>

          {/* 跟进记录 */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">跟进记录</h3>
              {lead.status !== "CONVERTED" && (
                <Button variant="outline" size="sm" onClick={onAddFollowUp}>
                  <Plus className="mr-2 h-4 w-4" />
                  添加跟进
                </Button>
              )}
            </div>
            {followUps.length === 0 ? (
              <p className="text-center text-slate-400 py-8">暂无跟进记录</p>
            ) : (
              <div className="space-y-3">
                {followUps.map((followUp) => (
                  <Card key={followUp.id}>
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <Badge variant="outline">{followUp.follow_up_type}</Badge>
                            <span className="text-sm text-slate-400">
                              {followUp.creator_name || "未知"}
                            </span>
                            <span className="text-sm text-slate-500">
                              {followUp.created_at
                                ? new Date(followUp.created_at).toLocaleString("zh-CN")
                                : ""}
                            </span>
                          </div>
                          <p className="text-white mb-2">{followUp.content}</p>
                          {followUp.next_action && (
                            <p className="text-sm text-slate-400">
                              下次行动: {followUp.next_action}
                            </p>
                          )}
                          {followUp.next_action_at && (
                            <p className="text-sm text-slate-400">
                              行动时间:{" "}
                              {new Date(followUp.next_action_at).toLocaleDateString(
                                "zh-CN"
                              )}
                            </p>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            关闭
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
