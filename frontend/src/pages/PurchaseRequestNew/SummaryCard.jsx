


export default function SummaryCard({
  itemCount,
  totalAmount,
  saving,
  onSave,
  onSubmit,
}) {
  return (
    <Card className="bg-slate-800/50 border-slate-700/50 sticky top-6">
      <CardHeader>
        <CardTitle className="text-slate-200">汇总信息</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <Label className="text-slate-400">物料数量</Label>
          <p className="text-2xl font-bold text-slate-200">{itemCount}</p>
        </div>
        <div>
          <Label className="text-slate-400">总金额</Label>
          <p className="text-2xl font-bold text-emerald-400">
            ¥{totalAmount.toFixed(2)}
          </p>
        </div>
        <div className="pt-4 border-t border-slate-700 space-y-2">
          <Button
            className="w-full bg-blue-600 hover:bg-blue-700"
            onClick={onSave}
            disabled={saving}
          >
            <Save className="w-4 h-4 mr-2" />
            {saving ? "保存中..." : "保存草稿"}
          </Button>
          <Button
            className="w-full bg-emerald-600 hover:bg-emerald-700"
            onClick={onSubmit}
            disabled={saving}
          >
            <Send className="w-4 h-4 mr-2" />
            {saving ? "提交中..." : "保存并提交"}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
