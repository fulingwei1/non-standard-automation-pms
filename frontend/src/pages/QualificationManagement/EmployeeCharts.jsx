/**
 * EmployeeCharts - 员工认证可视化图表区域
 */
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "../../components/ui/card";
import { CompetencyRadarChart } from "../../components/qualification/CompetencyRadarChart";
import { LEVEL_CODES, LEVEL_LABELS, POSITION_TYPES, POSITION_LABELS } from "./constants";

export function EmployeeCharts({ qualifications }) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* 能力维度分析 - 平均分 */}
      <Card>
        <CardHeader>
          <CardTitle>平均能力维度</CardTitle>
          <CardDescription>所有已认证员工的平均能力得分</CardDescription>
        </CardHeader>
        <CardContent>
          {(() => {
          // 计算所有员工的能力维度平均值
          const dimensionScores = {};
          let _count = 0;
          (qualifications || []).forEach((qual) => {
            if (qual.assessment_details) {
              Object.keys(qual.assessment_details).forEach((key) => {
                if (!dimensionScores[key]) {
                  dimensionScores[key] = { total: 0, count: 0 };
                }
                const score =
                typeof qual.assessment_details[key] === "object" ?
                qual.assessment_details[key].score :
                qual.assessment_details[key];
                if (typeof score === "number") {
                  dimensionScores[key].total += score;
                  dimensionScores[key].count += 1;
                }
              });
              _count += 1;
            }
          });

          const avgScores = {};
          Object.keys(dimensionScores).forEach((key) => {
            avgScores[key] =
            dimensionScores[key].count > 0 ?
            dimensionScores[key].total / dimensionScores[key].count :
            0;
          });

          return Object.keys(avgScores).length > 0 ?
          <CompetencyRadarChart data={avgScores} size={300} /> :

          <div className="flex items-center justify-center h-64 text-gray-400">
                暂无评估数据
          </div>;

        })()}
        </CardContent>
      </Card>

      {/* 等级分布 */}
      <Card>
        <CardHeader>
          <CardTitle>等级分布统计</CardTitle>
          <CardDescription>已认证员工的等级分布情况</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {LEVEL_CODES.map(
            (levelCode) => {
              const count = (qualifications || []).filter(
                (q) => q.level?.level_code === levelCode
              ).length;
              const percentage =
              qualifications.length > 0 ?
              (count / qualifications.length * 100).toFixed(1) :
              0;
              return (
                <div key={levelCode} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">
                        {LEVEL_LABELS[levelCode]}
                      </span>
                      <span className="text-sm text-gray-500">
                        {count} 人 ({percentage}%)
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                      className="bg-blue-600 h-2 rounded-full transition-all"
                      style={{ width: `${percentage}%` }} />

                    </div>
                </div>);

            }
          )}
          </div>
        </CardContent>
      </Card>

      {/* 岗位类型分布 */}
      <Card>
        <CardHeader>
          <CardTitle>岗位类型分布</CardTitle>
          <CardDescription>不同岗位类型的认证人数</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {POSITION_TYPES.map(
            (positionType) => {
              const count = (qualifications || []).filter(
                (q) => q.position_type === positionType
              ).length;
              const percentage =
              qualifications.length > 0 ?
              (count / qualifications.length * 100).toFixed(1) :
              0;
              return (
                <div key={positionType} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">
                        {POSITION_LABELS[positionType]}
                      </span>
                      <span className="text-sm text-gray-500">
                        {count} 人 ({percentage}%)
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                      className="bg-green-600 h-2 rounded-full transition-all"
                      style={{ width: `${percentage}%` }} />

                    </div>
                </div>);

            }
          )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
