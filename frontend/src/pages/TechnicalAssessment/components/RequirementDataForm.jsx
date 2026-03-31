import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../../../components/ui";

export function RequirementDataForm({
  requirementData,
  setRequirementData,
  enableAI,
  setEnableAI,
}) {
  return (
    <Card className="bg-gray-800 border-gray-700">
      <CardHeader>
        <CardTitle>需求数据</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">
              需求数据 (JSON格式)
            </label>
            <textarea
              className="w-full h-64 p-3 bg-gray-700 border border-gray-600 rounded text-white font-mono text-sm"
              value={JSON.stringify(requirementData, null, 2)}
              onChange={(e) => {
                try {
                  setRequirementData(JSON.parse(e.target.value));
                } catch (_err) {
                  // 忽略解析错误
                }
              }}
              placeholder='{"industry": "新能源", "budgetStatus": "明确", ...}'
            />
          </div>
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="enableAI"
              checked={enableAI}
              onChange={(e) => setEnableAI(e.target.checked)}
            />
            <label htmlFor="enableAI" className="text-sm">
              启用AI分析（需要配置API密钥）
            </label>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
