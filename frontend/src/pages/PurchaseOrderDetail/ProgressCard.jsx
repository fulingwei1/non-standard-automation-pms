/**
 * Order progress card with progress bar
 */


const ProgressCard = ({ po, progress }) => (
  <Card>
    <CardHeader>
      <CardTitle className="flex items-center gap-2">
        <Zap className="w-5 h-5 text-amber-400" />
        {"\u8ba2\u5355\u8fdb\u5ea6"}
      </CardTitle>
    </CardHeader>
    <CardContent>
      <div className="space-y-3">
        <div>
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm text-slate-400">{"\u5b8c\u6210\u5ea6"}</p>
            <p className="text-sm font-medium text-slate-100">
              {progress.toFixed(0)}%
            </p>
          </div>
          <Progress value={progress || "unknown"} className="h-2" />
        </div>
        <p className="text-xs text-slate-500">
          {(po.timeline || []).filter((s) => s.status === "completed").length} /{" "}
          {po.timeline?.length} {"\u4e2a\u9636\u6bb5\u5df2\u5b8c\u6210"}
        </p>
      </div>
    </CardContent>
  </Card>
);

export default ProgressCard;
