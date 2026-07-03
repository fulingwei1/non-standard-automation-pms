import { Card, CardContent } from "../../components/ui/card";

export default function AutoFixOptions({
  autoFixTiming,
  setAutoFixTiming,
  autoFixMissing,
  setAutoFixMissing,
}) {
  return (
    <Card className="mb-6">
      <CardContent className="pt-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-8">
            <div className="flex items-center gap-3">
              <input
                type="checkbox"
                id="autoFixTiming"
                checked={autoFixTiming}
                onChange={(e) => setAutoFixTiming(e.target.checked)}
                className="w-4 h-4 text-blue-600 rounded border-slate-300"
              />
              <label
                htmlFor="autoFixTiming"
                className="text-sm text-slate-700 cursor-pointer"
              >
                自动修复时序冲突
              </label>
            </div>
            <div className="text-xs text-slate-500">(调整任务计划时间)</div>
          </div>

          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              id="autoFixMissing"
              checked={autoFixMissing}
              onChange={(e) => setAutoFixMissing(e.target.checked)}
              className="w-4 h-4 text-blue-600 rounded border-slate-300"
            />
            <label
              htmlFor="autoFixMissing"
              className="text-sm text-slate-700 cursor-pointer"
            >
              自动移除缺失依赖
            </label>
            <div className="text-xs text-slate-500">
              (删除指向不存在任务的依赖)
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
