

import {
  OPPORTUNITY_PRIORITY_CONFIGS,
  SALES_SOURCE_CONFIGS,
  OPPORTUNITY_TYPE_CONFIGS,
} from "../../components/opportunity-board";

export default function CreateOpportunityDialog({
  open,
  onOpenChange,
  newOpportunity,
  setNewOpportunity,
  owners,
  onSubmit,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto bg-surface-1 border-border">
        <DialogHeader>
          <DialogTitle className="text-white">创建销售机会</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm text-text-secondary mb-1 block">机会名称 *</label>
              <Input
                value={newOpportunity.name}
                onChange={(e) => setNewOpportunity({ ...newOpportunity, name: e.target.value })}
                placeholder="输入机会名称"
                className="bg-surface-2 border-border" />

            </div>
            <div>
              <label className="text-sm text-text-secondary mb-1 block">客户 *</label>
              <Input
                value={newOpportunity.customerId}
                onChange={(e) => setNewOpportunity({ ...newOpportunity, customerId: e.target.value })}
                placeholder="选择客户"
                className="bg-surface-2 border-border" />

            </div>
            <div>
              <label className="text-sm text-text-secondary mb-1 block">预期金额 *</label>
              <Input
                type="number"
                value={newOpportunity.expectedAmount}
                onChange={(e) => setNewOpportunity({ ...newOpportunity, expectedAmount: e.target.value })}
                placeholder="输入金额"
                className="bg-surface-2 border-border" />

            </div>
            <div>
              <label className="text-sm text-text-secondary mb-1 block">预期成交日期 *</label>
              <Input
                type="date"
                value={newOpportunity.expectedCloseDate}
                onChange={(e) => setNewOpportunity({ ...newOpportunity, expectedCloseDate: e.target.value })}
                className="bg-surface-2 border-border" />

            </div>
            <div>
              <label className="text-sm text-text-secondary mb-1 block">优先级</label>
              <Select
                value={newOpportunity.priority}
                onValueChange={(value) => setNewOpportunity({ ...newOpportunity, priority: value })}>

                <SelectTrigger className="bg-surface-2 border-border">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-surface-2 border-border">
                  {Object.entries(OPPORTUNITY_PRIORITY_CONFIGS).map(([key, config]) =>
                  <SelectItem key={key} value={key || "unknown"}>
                      {config.label}
                  </SelectItem>
                  )}
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-sm text-text-secondary mb-1 block">来源</label>
              <Select
                value={newOpportunity.source}
                onValueChange={(value) => setNewOpportunity({ ...newOpportunity, source: value })}>

                <SelectTrigger className="bg-surface-2 border-border">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-surface-2 border-border">
                  {Object.entries(SALES_SOURCE_CONFIGS).map(([key, config]) =>
                  <SelectItem key={key} value={key || "unknown"}>
                      {config.label}
                  </SelectItem>
                  )}
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-sm text-text-secondary mb-1 block">类型</label>
              <Select
                value={newOpportunity.type}
                onValueChange={(value) => setNewOpportunity({ ...newOpportunity, type: value })}>

                <SelectTrigger className="bg-surface-2 border-border">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-surface-2 border-border">
                  {Object.entries(OPPORTUNITY_TYPE_CONFIGS).map(([key, config]) =>
                  <SelectItem key={key} value={key || "unknown"}>
                      {config.label}
                  </SelectItem>
                  )}
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-sm text-text-secondary mb-1 block">负责人</label>
              <Select
                value={newOpportunity.ownerId}
                onValueChange={(value) => setNewOpportunity({ ...newOpportunity, ownerId: value })}>

                <SelectTrigger className="bg-surface-2 border-border">
                  <SelectValue placeholder="选择负责人" />
                </SelectTrigger>
                <SelectContent className="bg-surface-2 border-border">
                  {(owners || []).map((owner) =>
                  <SelectItem key={owner.id} value={owner.id}>
                      {owner.name}
                  </SelectItem>
                  )}
                </SelectContent>
              </Select>
            </div>
          </div>
          <div>
            <label className="text-sm text-text-secondary mb-1 block">描述</label>
            <textarea
              value={newOpportunity.description}
              onChange={(e) => setNewOpportunity({ ...newOpportunity, description: e.target.value })}
              placeholder="描述销售机会详情..."
              rows={3}
              className="w-full bg-surface-2 border border-border rounded-lg p-2 text-white" />

          </div>
        </div>
        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            className="bg-surface-2 border-border">

            取消
          </Button>
          <Button
            onClick={onSubmit}
            className="bg-accent hover:bg-accent/90">

            创建机会
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
