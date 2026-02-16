/**
 * AI 供应商推荐组件
 * @component SupplierRecommendation
 * @description 显示 AI 推荐的供应商信息和多维度评分
 */

import React from 'react';
import { TrendingUp, Award, DollarSign, Clock, History } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../../../../components/ui/card';
import { Badge } from '../../../../components/ui/badge';
import { Progress } from '../../../../components/ui/progress';
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
  Tooltip,
} from 'recharts';
import type { PurchaseSuggestion } from '../../../../types/purchase';

interface SupplierRecommendationProps {
  suggestion: PurchaseSuggestion;
}

const SupplierRecommendation: React.FC<SupplierRecommendationProps> = ({ suggestion }) => {
  /**
   * 准备雷达图数据
   */
  const radarData = [
    {
      subject: '绩效',
      value: suggestion.recommendation_reason.performance_score,
      fullMark: 100,
    },
    {
      subject: '价格',
      value: suggestion.recommendation_reason.price_score,
      fullMark: 100,
    },
    {
      subject: '交期',
      value: suggestion.recommendation_reason.delivery_score,
      fullMark: 100,
    },
    {
      subject: '历史',
      value: suggestion.recommendation_reason.history_score,
      fullMark: 100,
    },
  ];

  /**
   * 获取置信度颜色
   */
  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 80) return 'text-green-600';
    if (confidence >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  /**
   * 获取置信度描述
   */
  const getConfidenceLabel = (confidence: number) => {
    if (confidence >= 80) return '高';
    if (confidence >= 60) return '中';
    return '低';
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-blue-600" />
            AI 推荐供应商
          </CardTitle>
          <Badge className="bg-blue-100 text-blue-800">
            AI 分析
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* 推荐供应商信息 */}
        <div className="p-6 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg border-2 border-blue-200">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h3 className="text-xl font-bold text-blue-900">
                {suggestion.suggested_supplier_name}
              </h3>
              <p className="text-sm text-blue-700 mt-1">推荐供应商</p>
            </div>
            <div className="text-right">
              <p className="text-3xl font-bold text-blue-600">
                {suggestion.recommendation_reason.total_score.toFixed(1)}
              </p>
              <p className="text-sm text-blue-700">综合评分</p>
            </div>
          </div>

          {/* 置信度显示 */}
          <div className="mt-4 p-4 bg-white rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">AI 置信度</span>
              <span className={`text-lg font-bold ${getConfidenceColor(suggestion.ai_confidence)}`}>
                {suggestion.ai_confidence.toFixed(1)}% ({getConfidenceLabel(suggestion.ai_confidence)})
              </span>
            </div>
            <Progress value={suggestion.ai_confidence} className="h-2" />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* 多维度评分 - 雷达图 */}
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-4">多维度评分分析</h4>
            <ResponsiveContainer width="100%" height={300}>
              <RadarChart data={radarData}>
                <PolarGrid />
                <PolarAngleAxis dataKey="subject" />
                <PolarRadiusAxis angle={90} domain={[0, 100]} />
                <Radar
                  name="评分"
                  dataKey="value"
                  stroke="#3b82f6"
                  fill="#3b82f6"
                  fillOpacity={0.6}
                />
                <Tooltip />
              </RadarChart>
            </ResponsiveContainer>
          </div>

          {/* 详细评分 */}
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-4">评分详情</h4>
            <div className="space-y-4">
              {/* 绩效评分 */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Award className="h-4 w-4 text-purple-600" />
                    <span className="text-sm font-medium">绩效表现</span>
                    <span className="text-xs text-gray-500">(权重 40%)</span>
                  </div>
                  <span className="text-sm font-bold text-purple-600">
                    {suggestion.recommendation_reason.performance_score.toFixed(1)}
                  </span>
                </div>
                <Progress
                  value={suggestion.recommendation_reason.performance_score}
                  className="h-2 bg-purple-100"
                />
              </div>

              {/* 价格评分 */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <DollarSign className="h-4 w-4 text-green-600" />
                    <span className="text-sm font-medium">价格竞争力</span>
                    <span className="text-xs text-gray-500">(权重 30%)</span>
                  </div>
                  <span className="text-sm font-bold text-green-600">
                    {suggestion.recommendation_reason.price_score.toFixed(1)}
                  </span>
                </div>
                <Progress
                  value={suggestion.recommendation_reason.price_score}
                  className="h-2 bg-green-100"
                />
              </div>

              {/* 交期评分 */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Clock className="h-4 w-4 text-blue-600" />
                    <span className="text-sm font-medium">交期准时性</span>
                    <span className="text-xs text-gray-500">(权重 20%)</span>
                  </div>
                  <span className="text-sm font-bold text-blue-600">
                    {suggestion.recommendation_reason.delivery_score.toFixed(1)}
                  </span>
                </div>
                <Progress
                  value={suggestion.recommendation_reason.delivery_score}
                  className="h-2 bg-blue-100"
                />
              </div>

              {/* 历史评分 */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <History className="h-4 w-4 text-orange-600" />
                    <span className="text-sm font-medium">历史合作</span>
                    <span className="text-xs text-gray-500">(权重 10%)</span>
                  </div>
                  <span className="text-sm font-bold text-orange-600">
                    {suggestion.recommendation_reason.history_score.toFixed(1)}
                  </span>
                </div>
                <Progress
                  value={suggestion.recommendation_reason.history_score}
                  className="h-2 bg-orange-100"
                />
              </div>
            </div>
          </div>
        </div>

        {/* AI 推荐说明 */}
        <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
          <h4 className="text-sm font-medium text-gray-700 mb-2">AI 推荐算法说明</h4>
          <ul className="text-sm text-gray-600 space-y-1 list-disc list-inside">
            <li>综合考虑供应商绩效、价格、交期、历史合作等多个维度</li>
            <li>基于历史采购数据和供应商评估记录进行智能分析</li>
            <li>推荐评分 ≥ 80 为优秀，60-80 为良好，&lt; 60 需谨慎选择</li>
            <li>置信度反映了推荐结果的可靠程度，建议优先选择高置信度推荐</li>
          </ul>
        </div>
      </CardContent>
    </Card>
  );
};

export default SupplierRecommendation;
