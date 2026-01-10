import React from "react";
import { Card, CardHeader, CardTitle, CardContent } from "../ui/card";
import { Badge } from "../ui/badge";
import { Progress } from "../ui/progress";
import {
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Info,
} from "lucide-react";

/**
 * 中标概率等级配置
 */
const PROBABILITY_LEVELS = {
  VERY_HIGH: {
    label: "极高",
    color: "bg-green-500",
    textColor: "text-green-700",
    threshold: 80,
  },
  HIGH: {
    label: "高",
    color: "bg-blue-500",
    textColor: "text-blue-700",
    threshold: 60,
  },
  MEDIUM: {
    label: "中",
    color: "bg-yellow-500",
    textColor: "text-yellow-700",
    threshold: 40,
  },
  LOW: {
    label: "低",
    color: "bg-orange-500",
    textColor: "text-orange-700",
    threshold: 20,
  },
  VERY_LOW: {
    label: "极低",
    color: "bg-red-500",
    textColor: "text-red-700",
    threshold: 0,
  },
};

/**
 * 五维评估分数展示组件
 */
const DimensionScores = ({ scores }) => {
  const dimensions = [
    { key: "requirement_maturity", label: "需求成熟度" },
    { key: "technical_feasibility", label: "技术可行性" },
    { key: "business_feasibility", label: "商务可行性" },
    { key: "delivery_risk", label: "交付风险" },
    { key: "customer_relationship", label: "客户关系" },
  ];

  return (
    <div className="space-y-2">
      {dimensions.map((dim) => {
        const score = scores?.[dim.key] || 0;
        const color =
          score >= 70
            ? "bg-green-500"
            : score >= 50
              ? "bg-yellow-500"
              : "bg-red-500";

        return (
          <div key={dim.key} className="flex items-center gap-2">
            <span className="text-xs text-slate-600 w-20 truncate">
              {dim.label}
            </span>
            <div className="flex-1">
              <Progress
                value={score}
                className="h-2"
                indicatorClassName={color}
              />
            </div>
            <span className="text-xs font-medium w-8 text-right">{score}</span>
          </div>
        );
      })}
    </div>
  );
};

/**
 * 中标率预测卡片
 */
const WinRatePredictionCard = ({
  prediction,
  leadName,
  showRecommendations = true,
  compact = false,
}) => {
  if (!prediction) {
    return (
      <Card className="border-slate-200">
        <CardContent className="py-8 text-center text-slate-500">
          <Info className="h-8 w-8 mx-auto mb-2 opacity-50" />
          <p>暂无预测数据</p>
        </CardContent>
      </Card>
    );
  }

  const {
    predicted_win_rate,
    probability_level,
    confidence,
    factors,
    recommendations,
    similar_leads_count,
    similar_leads_win_rate,
  } = prediction;

  const levelConfig =
    PROBABILITY_LEVELS[probability_level] || PROBABILITY_LEVELS.MEDIUM;
  const winRatePercent = Math.round(predicted_win_rate * 100);

  // 获取预测图标
  const getPredictionIcon = () => {
    if (winRatePercent >= 60)
      return <TrendingUp className="h-5 w-5 text-green-600" />;
    if (winRatePercent >= 40)
      return <AlertTriangle className="h-5 w-5 text-yellow-600" />;
    return <TrendingDown className="h-5 w-5 text-red-600" />;
  };

  if (compact) {
    return (
      <div className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg">
        <div
          className={`w-12 h-12 rounded-full flex items-center justify-center ${levelConfig.color} bg-opacity-20`}
        >
          <span className={`text-lg font-bold ${levelConfig.textColor}`}>
            {winRatePercent}%
          </span>
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium">预测中标率</span>
            <Badge variant="outline" className={levelConfig.textColor}>
              {levelConfig.label}
            </Badge>
          </div>
          <p className="text-xs text-slate-500">
            置信度 {Math.round(confidence * 100)}%
          </p>
        </div>
      </div>
    );
  }

  return (
    <Card className="border-slate-200">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base flex items-center gap-2">
            {getPredictionIcon()}
            中标率预测
          </CardTitle>
          {leadName && (
            <span className="text-sm text-slate-500">{leadName}</span>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* 主要预测结果 */}
        <div className="flex items-center gap-4">
          <div
            className={`w-20 h-20 rounded-full flex items-center justify-center ${levelConfig.color} bg-opacity-20`}
          >
            <span className={`text-2xl font-bold ${levelConfig.textColor}`}>
              {winRatePercent}%
            </span>
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <Badge className={levelConfig.color}>
                {levelConfig.label}概率
              </Badge>
              <span className="text-sm text-slate-500">
                置信度 {Math.round(confidence * 100)}%
              </span>
            </div>
            {similar_leads_count > 0 && (
              <p className="text-xs text-slate-500">
                参考 {similar_leads_count} 个相似线索，历史中标率{" "}
                {Math.round(similar_leads_win_rate * 100)}%
              </p>
            )}
          </div>
        </div>

        {/* 五维评估分数 */}
        {factors?.dimension_scores && (
          <div>
            <h4 className="text-sm font-medium mb-2 text-slate-700">
              五维评估
            </h4>
            <DimensionScores scores={factors.dimension_scores} />
          </div>
        )}

        {/* 影响因素 */}
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="p-2 bg-slate-50 rounded">
            <span className="text-slate-500">销售历史中标率</span>
            <p className="font-medium">
              {Math.round((factors?.salesperson_win_rate || 0) * 100)}%
            </p>
          </div>
          <div className="p-2 bg-slate-50 rounded">
            <span className="text-slate-500">客户合作次数</span>
            <p className="font-medium">
              {factors?.customer_cooperation_count || 0} 次
            </p>
          </div>
          <div className="p-2 bg-slate-50 rounded">
            <span className="text-slate-500">竞争对手数量</span>
            <p className="font-medium">{factors?.competitor_count || 0} 家</p>
          </div>
          <div className="p-2 bg-slate-50 rounded">
            <span className="text-slate-500">基础评分</span>
            <p className="font-medium">
              {Math.round((factors?.base_score || 0) * 100)}
            </p>
          </div>
        </div>

        {/* 建议 */}
        {showRecommendations && recommendations?.length > 0 && (
          <div>
            <h4 className="text-sm font-medium mb-2 text-slate-700 flex items-center gap-1">
              <Info className="h-4 w-4" />
              提升建议
            </h4>
            <ul className="space-y-1">
              {recommendations.slice(0, 3).map((rec, index) => (
                <li
                  key={index}
                  className="text-xs text-slate-600 flex items-start gap-1"
                >
                  <span className="text-blue-500 mt-0.5">•</span>
                  <span>{rec}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

/**
 * 中标率趋势图
 */
const WinRateTrend = ({ data }) => {
  if (!data?.length) {
    return (
      <div className="text-center py-8 text-slate-500">
        <Info className="h-8 w-8 mx-auto mb-2 opacity-50" />
        <p>暂无趋势数据</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {data.map((item, index) => (
        <div key={index} className="flex items-center gap-3">
          <span className="text-xs text-slate-500 w-16">{item.month}</span>
          <div className="flex-1">
            <Progress
              value={item.win_rate * 100}
              className="h-4"
              indicatorClassName={
                item.win_rate >= 0.4
                  ? "bg-green-500"
                  : item.win_rate >= 0.2
                    ? "bg-yellow-500"
                    : "bg-red-500"
              }
            />
          </div>
          <span className="text-xs font-medium w-12 text-right">
            {Math.round(item.win_rate * 100)}%
          </span>
          <span className="text-xs text-slate-400 w-16">
            {item.won}/{item.total}
          </span>
        </div>
      ))}
    </div>
  );
};

export { WinRatePredictionCard, DimensionScores, WinRateTrend };
export default WinRatePredictionCard;
