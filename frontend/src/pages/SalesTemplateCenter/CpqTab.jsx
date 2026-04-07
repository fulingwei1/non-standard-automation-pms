


export default function CpqTab({
  ruleSets,
  loading,
  onShowDialog,
}) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">CPQ 定价规则</h3>
          <p className="text-sm text-muted-foreground">
            配置参数选项、定价矩阵与审批阈值，驱动智能预测。
          </p>
        </div>
        <Button onClick={onShowDialog}>新增规则集</Button>
      </div>
      {ruleSets.length === 0 && !loading && (
        <div className="text-center text-muted-foreground py-8 border rounded-md">
          规则集为空，先创建一个基础规则集。
        </div>
      )}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {(ruleSets || []).map((rule) => (
          <Card key={rule.id}>
            <CardHeader>
              <CardTitle className="flex items-center justify-between text-base">
                <span>{rule.rule_name}</span>
                <Badge variant="outline">{rule.status}</Badge>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <div className="text-xs text-muted-foreground">
                编码: {rule.rule_code} · 基准价 {rule.base_price}
              </div>
              <div className="text-xs text-muted-foreground">
                审批阈值: {JSON.stringify(rule.approval_threshold || {})}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
