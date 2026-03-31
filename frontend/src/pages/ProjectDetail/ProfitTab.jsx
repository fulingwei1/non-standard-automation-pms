import { Card, CardContent } from "../../components/ui";
import ProfitAnalysisCard from "../../components/project/ProfitAnalysisCard";

export default function ProfitTab({ projectId }) {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ProfitAnalysisCard projectId={projectId} />
        <Card>
          <CardContent className="p-6">
            <h3 className="text-lg font-semibold mb-4">利润改善</h3>
            <div className="space-y-3 text-sm text-gray-600">
              <p>在概览页右侧可查看实时利润分析卡片。</p>
              <p>API 端点：</p>
              <ul className="list-disc list-inside space-y-1 text-xs">
                <li>综合分析: GET /costs/profit-optimization</li>
                <li>毛利率: GET /costs/margin-analysis</li>
                <li>优化建议: GET /costs/cost-optimization</li>
                <li>报价偏差: GET /costs/quote-cost-variance</li>
                <li>高利润特征: GET /costs/high-profit-patterns</li>
                <li>低利润根因: GET /costs/low-profit-root-cause</li>
              </ul>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
