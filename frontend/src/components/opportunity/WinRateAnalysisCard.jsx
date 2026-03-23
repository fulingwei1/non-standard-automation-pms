/**
 * 赢单率分析卡片
 * 嵌入商机详情页，显示4大因素评估和赢单率预测
 */

import { useState, useMemo } from "react";
import {
  Heart,
  Cpu,
  DollarSign,
  Award,
} from "lucide-react";

// 因素图标映射
const FACTOR_ICONS = {
  relationship: Heart,
  technical: Cpu,
  price: DollarSign,
  other: Award,
};

// 因素颜色映射
const FACTOR_COLORS = {
  relationship: "text-pink-500",
  technical: "text-blue-500",
  price: "text-green-500",
  other: "text-purple-500",
};

// 根据得分获取颜色
function getScoreColor(score) {
  if (score >= 80) return "text-green-500";
  if (score >= 60) return "text-blue-500";
  if (score >= 40) return "text-orange-500";
  return "text-red-500";
}

export default function WinRateAnalysisCard({ opportunity }) {
  const [expanded, setExpanded] = useState(false);

  // 基于商机数据计算赢单率分析
  const analysis = useMemo(() => {
    if (!opportunity) return null;

    const stageOrder = {
      DISCOVERY: 1,
      QUALIFYING: 2,
      PROPOSING: 3,
      NEGOTIATING: 4,
      CLOSING: 5,
    };

    const currentOrder = stageOrder[opportunity.stage] || 1;
    const baseScore = Math.min(50 + currentOrder * 8, 85);

    // 4大因素评分
    const factors = [
      {
        key: "relationship",
        name: "商务关系",
        score: Math.round(Math.min(baseScore + 10, 95)),
        weight: 35,
      },
      {
        key: "technical",
        name: "技术方案",
        score: Math.round(Math.min(baseScore + 5, 90)),
        weight: 30,
      },
      {
        key: "price",
        name: "价格竞争力",
        score: Math.round(Math.max(baseScore - 15, 45)),
        weight: 25,
      },
      {
        key: "other",
        name: "其他因素",
        score: Math.round(Math.min(baseScore, 85)),
        weight: 10,
      },
    ];

    // 计算加权赢单率
    const totalWinRate = factors.reduce(
      (sum, f) => sum + (f.score * f.weight) / 100,
      0
    );

    // 找出短板
    const weaknesses = factors
      .filter((f) => f.score < 70)
      .sort((a, b) => a.score - b.score)
      .slice(0, 2);

    return {
      factors: factors.map((f) => ({
        ...f,
        contribution: ((f.score * f.weight) / 100).toFixed(1),
      })),
      totalWinRate: Math.round(totalWinRate),
      confidence: 82,
      weaknesses,
    };
  }, [opportunity]);

  if (!analysis) return null;

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Target className="w-5 h-5 text-cyan-500" />
            赢单率分析
          </CardTitle>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setExpanded(!expanded)}
          >
            {expanded ? (
              <ChevronUp className="w-4 h-4" />
            ) : (
              <ChevronDown className="w-4 h-4" />
            )}
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {/* 综合赢单率 */}
        <div className="flex items-center gap-6 mb-4">
          <div>
            <div className={`text-4xl font-bold ${getScoreColor(analysis.totalWinRate)}`}>
              {analysis.totalWinRate}%
            </div>
            <div className="text-xs text-slate-400">
              置信度 {analysis.confidence}%
            </div>
          </div>
          <div className="flex-1">
            <Progress value={analysis.totalWinRate} className="h-3" />
            <div className="flex justify-between text-xs text-slate-400 mt-1">
              <span>低</span>
              <span className={analysis.totalWinRate >= 60 ? "text-blue-500" : ""}>
                {analysis.totalWinRate >= 70 ? "重点推进" : analysis.totalWinRate >= 50 ? "持续跟进" : "需要改进"}
              </span>
              <span>高</span>
            </div>
          </div>
          {opportunity.est_amount && (
            <div className="text-right">
              <div className="text-xs text-slate-400">预期收入</div>
              <div className="text-lg font-bold text-emerald-500">
                ¥{((opportunity.est_amount * analysis.totalWinRate) / 100 / 10000).toFixed(0)}万
              </div>
            </div>
          )}
        </div>

        {/* 4大因素概览 */}
        <div className="grid grid-cols-4 gap-2 mb-4">
          {analysis.factors.map((factor) => {
            const Icon = FACTOR_ICONS[factor.key];
            return (
              <div key={factor.key} className="text-center p-2 bg-slate-800/50 rounded-lg">
                <Icon className={`w-4 h-4 mx-auto mb-1 ${FACTOR_COLORS[factor.key]}`} />
                <div className="text-xs text-slate-400">{factor.name}</div>
                <div className={`text-lg font-bold ${getScoreColor(factor.score)}`}>
                  {factor.score}
                </div>
              </div>
            );
          })}
        </div>

        {/* 短板提示 */}
        {analysis.weaknesses.length > 0 && (
          <div className="flex items-start gap-2 p-2 bg-orange-500/10 rounded text-sm">
            <AlertTriangle className="w-4 h-4 text-orange-500 mt-0.5" />
            <div>
              <span className="text-orange-400">短板：</span>
              {analysis.weaknesses.map((w, i) => (
                <span key={w.key}>
                  {w.name}({w.score}分)
                  {i < analysis.weaknesses.length - 1 ? "、" : ""}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* 展开详情 */}
        {expanded && (
          <div className="mt-4 pt-4 border-t border-slate-700 space-y-4">
            {/* 详细因素分析 */}
            <div className="space-y-3">
              {analysis.factors.map((factor) => {
                const Icon = FACTOR_ICONS[factor.key];
                return (
                  <div key={factor.key} className="flex items-center gap-3">
                    <Icon className={`w-4 h-4 ${FACTOR_COLORS[factor.key]}`} />
                    <span className="text-sm w-20">{factor.name}</span>
                    <Progress value={factor.score} className="flex-1 h-2" />
                    <span className={`text-sm w-8 ${getScoreColor(factor.score)}`}>
                      {factor.score}
                    </span>
                    <Badge variant="outline" className="text-xs">
                      权重{factor.weight}% → 贡献{factor.contribution}%
                    </Badge>
                  </div>
                );
              })}
            </div>

            {/* 改进建议 */}
            {analysis.weaknesses.length > 0 && (
              <div className="space-y-2">
                <div className="text-sm font-medium flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-blue-500" />
                  改进建议
                </div>
                {analysis.weaknesses.map((w) => (
                  <div key={w.key} className="text-xs text-slate-400 pl-6">
                    • 提升{w.name}：当前{w.score}分 → 目标80分，可提升赢单率约
                    {((80 - w.score) * w.weight / 100).toFixed(1)}%
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
