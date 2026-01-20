/**
 * Competency Radar Chart - 能力维度雷达图组件
 * 用于展示员工任职资格各维度能力得分
 */
import { useMemo } from "react";
import { cn as _cn } from "../../lib/utils";

export function CompetencyRadarChart({
  data,
  size = 400,
  maxScore = 100,
  showLabels = true,
  showScores = true
}) {
  // data格式: { technical_skills: 85, business_skills: 80, ... }

  const dimensions = useMemo(() => {
    if (!data || typeof data !== "object") {return [];}

    const dimensionNames = {
      technical_skills: "专业技能",
      business_skills: "业务能力",
      communication_skills: "沟通协作",
      learning_skills: "学习成长",
      project_management_skills: "项目管理",
      customer_service_skills: "客户服务",
      quality_skills: "质量意识",
      efficiency_skills: "效率能力"
    };

    return Object.entries(data).
    filter(([key]) => dimensionNames[key]).
    map(([key, value]) => ({
      key,
      label: dimensionNames[key],
      score:
      typeof value === "object" && value.score ?
      value.score :
      typeof value === "number" ?
      value :
      0
    }));
  }, [data]);

  const radius = size / 2 - 50;
  const centerX = size / 2;
  const centerY = size / 2;
  const angleStep = dimensions.length > 0 ? 2 * Math.PI / dimensions.length : 0;

  // 计算每个维度的坐标点
  const points = useMemo(() => {
    if (dimensions.length === 0) {return [];}
    return dimensions.map((dim, index) => {
      const angle = index * angleStep - Math.PI / 2;
      const normalizedScore = Math.min(dim.score / maxScore, 1);
      const r = radius * normalizedScore;
      return {
        x: centerX + r * Math.cos(angle),
        y: centerY + r * Math.sin(angle),
        label: dim.label,
        score: dim.score,
        key: dim.key,
        angle: angle + Math.PI / 2
      };
    });
  }, [dimensions, radius, centerX, centerY, angleStep, maxScore]);

  // 生成网格线（5个等级）
  const gridLevels = 5;
  const gridLines = useMemo(() => {
    if (dimensions.length === 0) {return [];}
    return Array.from({ length: gridLevels }, (_, i) => {
      const level = (i + 1) / gridLevels;
      const levelRadius = radius * level;
      return dimensions.map((_, index) => {
        const angle = index * angleStep - Math.PI / 2;
        return {
          x: centerX + levelRadius * Math.cos(angle),
          y: centerY + levelRadius * Math.sin(angle)
        };
      });
    });
  }, [dimensions.length, radius, centerX, centerY, angleStep]);

  // 生成数据区域路径
  const dataPath = useMemo(() => {
    if (points.length === 0) {return "";}
    return points.map((p) => `${p.x},${p.y}`).join(" ");
  }, [points]);

  // 计算平均分
  const avgScore = useMemo(() => {
    if (dimensions.length === 0) {return 0;}
    const sum = dimensions.reduce((acc, dim) => acc + dim.score, 0);
    return Math.round(sum / dimensions.length);
  }, [dimensions]);

  if (dimensions.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-gray-400">
        暂无数据
      </div>);

  }

  return (
    <div className="flex flex-col items-center space-y-4">
      <svg width={size} height={size} className="overflow-visible">
        {/* 网格线 */}
        <g opacity="0.15">
          {gridLines.map((line, i) =>
          <polygon
            key={i}
            points={line.map((p) => `${p.x},${p.y}`).join(" ")}
            fill="none"
            stroke="currentColor"
            strokeWidth="1"
            className="text-gray-400" />

          )}
        </g>

        {/* 轴线 */}
        <g opacity="0.3">
          {dimensions.map((_, index) => {
            const angle = index * angleStep - Math.PI / 2;
            const x2 = centerX + radius * Math.cos(angle);
            const y2 = centerY + radius * Math.sin(angle);
            return (
              <line
                key={index}
                x1={centerX}
                y1={centerY}
                x2={x2}
                y2={y2}
                stroke="currentColor"
                strokeWidth="1"
                className="text-gray-400" />);


          })}
        </g>

        {/* 数据区域 */}
        {points.length > 2 &&
        <polygon
          points={dataPath}
          fill="rgba(59, 130, 246, 0.15)"
          stroke="rgb(59, 130, 246)"
          strokeWidth="2.5"
          className="transition-all" />

        }

        {/* 数据点 */}
        {points.map((point, index) =>
        <g key={index}>
            <circle
            cx={point.x}
            cy={point.y}
            r="5"
            fill="rgb(59, 130, 246)"
            className="transition-all hover:r-7" />

            {/* 分数标签 */}
            {showScores &&
          <text
            x={point.x}
            y={point.y - 10}
            textAnchor="middle"
            className="text-sm font-bold fill-blue-600">

                {point.score}
          </text>
          }
            {/* 维度标签 */}
            {showLabels &&
          <text
            x={point.x + (point.x > centerX ? 12 : -12)}
            y={point.y + (point.y > centerY ? 18 : -8)}
            textAnchor={point.x > centerX ? "start" : "end"}
            className="text-xs fill-gray-700 dark:fill-gray-300"
            fontWeight="500">

                {point.label}
          </text>
          }
        </g>
        )}

        {/* 中心点 */}
        <circle cx={centerX} cy={centerY} r="3" fill="rgb(59, 130, 246)" />
      </svg>

      {/* 平均分显示 */}
      <div className="text-center">
        <div className="text-2xl font-bold text-blue-600">{avgScore}</div>
        <div className="text-xs text-gray-500">平均得分</div>
      </div>
    </div>);

}
