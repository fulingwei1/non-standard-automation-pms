/**
 * 方案卡片组件
 */

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { SOLUTION_TYPES, getScoreColor } from '../../constants';
import { Trophy, ThumbsUp, ThumbsDown, AlertTriangle } from 'lucide-react';

const SolutionCard = ({ solution, onClick }) => {
  const solutionType = SOLUTION_TYPES[solution.solution_type] || {};
  const scoreColor = getScoreColor(solution.ai_score);

  return (
    <Card
      className={`cursor-pointer hover:shadow-lg transition-all ${
        solution.is_recommended ? 'border-2 border-yellow-400' : ''
      }`}
      onClick={() => onClick?.(solution)}
    >
      {/* 推荐标识 */}
      {solution.is_recommended && (
        <div className="bg-gradient-to-r from-yellow-400 to-orange-400 text-white px-4 py-2 flex items-center gap-2">
          <Trophy className="h-4 w-4" />
          <span className="text-sm font-semibold">AI 推荐方案</span>
        </div>
      )}

      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-2xl">{solutionType.icon}</span>
            <span className={solutionType.color}>{solutionType.label}</span>
          </div>
          <div className="text-right">
            <p className="text-xs text-gray-500">AI评分</p>
            <p className="text-2xl font-bold" style={{ color: scoreColor }}>
              {solution.ai_score}
            </p>
          </div>
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* 方案描述 */}
        <p className="text-sm text-gray-600">{solution.solution_description}</p>

        {/* 评分指标 */}
        <div className="space-y-2">
          <ScoreBar label="可行性" score={solution.feasibility_score} />
          <ScoreBar label="成本" score={solution.cost_score} />
          <ScoreBar label="时间" score={solution.time_score} />
          <ScoreBar label="风险" score={solution.risk_score} />
        </div>

        {/* 预计信息 */}
        <div className="grid grid-cols-2 gap-4 pt-4 border-t">
          <div>
            <p className="text-xs text-gray-500">预计成本</p>
            <p className="font-semibold text-orange-600">
              ¥{parseFloat(solution.estimated_cost || 0).toLocaleString()}
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-500">预计交期</p>
            <p className="font-semibold text-blue-600">
              {solution.estimated_lead_time} 天
            </p>
          </div>
        </div>

        {/* 优点/缺点/风险 */}
        <div className="space-y-3 pt-4 border-t">
          {solution.advantages && solution.advantages.length > 0 && (
            <div>
              <div className="flex items-center gap-1 mb-1">
                <ThumbsUp className="h-3 w-3 text-green-600" />
                <p className="text-xs font-semibold text-green-600">优点</p>
              </div>
              <ul className="text-xs text-gray-600 space-y-1">
                {solution.advantages.map((item, index) => (
                  <li key={index}>• {item}</li>
                ))}
              </ul>
            </div>
          )}

          {solution.disadvantages && solution.disadvantages.length > 0 && (
            <div>
              <div className="flex items-center gap-1 mb-1">
                <ThumbsDown className="h-3 w-3 text-orange-600" />
                <p className="text-xs font-semibold text-orange-600">缺点</p>
              </div>
              <ul className="text-xs text-gray-600 space-y-1">
                {solution.disadvantages.map((item, index) => (
                  <li key={index}>• {item}</li>
                ))}
              </ul>
            </div>
          )}

          {solution.risks && solution.risks.length > 0 && (
            <div>
              <div className="flex items-center gap-1 mb-1">
                <AlertTriangle className="h-3 w-3 text-red-600" />
                <p className="text-xs font-semibold text-red-600">风险</p>
              </div>
              <ul className="text-xs text-gray-600 space-y-1">
                {solution.risks.map((item, index) => (
                  <li key={index}>• {item}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

// 评分进度条组件
const ScoreBar = ({ label, score }) => {
  const color = getScoreColor(score);
  
  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs text-gray-600">{label}</span>
        <span className="text-xs font-semibold" style={{ color }}>
          {score}
        </span>
      </div>
      <Progress 
        value={score} 
        className="h-2"
        style={{ '--progress-background': color }}
      />
    </div>
  );
};

export default SolutionCard;
