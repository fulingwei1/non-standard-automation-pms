

import { OpportunityUtils } from "../../components/opportunity-board";

export default function OpportunityDetailDialog({
  open,
  onOpenChange,
  selectedOpportunity,
  onDelete,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto bg-surface-1 border-border">
        {selectedOpportunity &&
        <>
            <DialogHeader>
              <DialogTitle className="text-white">{selectedOpportunity.name}</DialogTitle>
            </DialogHeader>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Basic Information */}
              <div className="space-y-4">
                <Card className="bg-surface-2 border-border">
                  <CardHeader>
                    <CardTitle className="text-sm text-white">基本信息</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-text-secondary">客户</span>
                      <span className="text-white">{selectedOpportunity.customerName}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-text-secondary">预期金额</span>
                      <span className="text-white font-semibold">
                        ¥{OpportunityUtils.formatCurrency(selectedOpportunity.expectedAmount)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-text-secondary">预期成交日期</span>
                      <span className="text-white">
                        {OpportunityUtils.formatDate(selectedOpportunity.expectedCloseDate)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-text-secondary">当前阶段</span>
                      <Badge className={OpportunityUtils.getStageConfig(selectedOpportunity.stage).color}>
                        {OpportunityUtils.getStageConfig(selectedOpportunity.stage).label}
                      </Badge>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-text-secondary">优先级</span>
                      <Badge variant="outline">
                        {OpportunityUtils.getPriorityConfig(selectedOpportunity.priority).label}
                      </Badge>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-text-secondary">机会评分</span>
                      <span className="text-white font-semibold">{selectedOpportunity.score}分</span>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Status and Actions */}
              <div className="space-y-4">
                <Card className="bg-surface-2 border-border">
                  <CardHeader>
                    <CardTitle className="text-sm text-white">状态信息</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-text-secondary">负责人</span>
                      <span className="text-white">{selectedOpportunity.owner}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-text-secondary">创建时间</span>
                      <span className="text-white">
                        {OpportunityUtils.formatDate(selectedOpportunity.createdDate)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-text-secondary">在当前阶段</span>
                      <span className="text-white">{selectedOpportunity.daysInStage}天</span>
                    </div>
                    {selectedOpportunity.nextActionDate &&
                  <div className="flex justify-between">
                        <span className="text-text-secondary">下次行动时间</span>
                        <span className="text-white">
                          {OpportunityUtils.formatDate(selectedOpportunity.nextActionDate)}
                        </span>
                  </div>
                  }
                    {OpportunityUtils.isOverdue(selectedOpportunity) &&
                  <div className="p-2 rounded-lg bg-red-500/10 text-red-300 text-sm">
                        <AlertTriangle className="w-4 h-4 inline mr-1" />
                        已超期 {OpportunityUtils.getOverdueDays(selectedOpportunity)} 天
                  </div>
                  }
                  </CardContent>
                </Card>
              </div>
            </div>

            <DialogFooter>
              <Button
              variant="outline"
              onClick={() => onOpenChange(false)}
              className="bg-surface-2 border-border">

                关闭
              </Button>
              <Button
              variant="destructive"
              onClick={onDelete}
              className="bg-red-500 hover:bg-red-600">

                <Trash2 className="w-4 h-4 mr-2" />
                删除
              </Button>
            </DialogFooter>
        </>
        }
      </DialogContent>
    </Dialog>
  );
}
