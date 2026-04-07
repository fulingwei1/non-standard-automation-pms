


export default function FunnelView({ funnelData }) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <SalesFunnel data={funnelData} />
      <Card className="bg-surface-1 border-border">
        <CardHeader>
          <CardTitle className="text-white">转化分析</CardTitle>
        </CardHeader>
        <CardContent>
          {/* Conversion analysis content */}
          <div className="space-y-4">
            {funnelData.slice(0, -1).map((stage, index) => {
            const nextStage = funnelData[index + 1];
            const conversionRate = stage.count > 0 ?
            ((nextStage?.count || 0) / stage.count * 100).toFixed(1) :
            0;

            return (
              <div key={stage.stage} className="flex items-center justify-between">
                  <span className="text-sm text-white">
                    {stage.label} → {nextStage?.label || "完成"}
                  </span>
                  <div className="flex items-center gap-2">
                    <div className="w-32 bg-surface-2 rounded-full h-2">
                      <div
                      className="bg-accent h-2 rounded-full"
                      style={{ width: `${conversionRate}%` }} />

                    </div>
                    <span className="text-sm text-white font-medium">
                      {conversionRate}%
                    </span>
                  </div>
              </div>);

          })}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
