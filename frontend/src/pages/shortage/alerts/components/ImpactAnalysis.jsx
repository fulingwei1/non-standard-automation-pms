/**
 * 影响分析组件
 */

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { AlertTriangle, Clock, DollarSign, Folder } from 'lucide-react';
import { getRiskScoreColor } from '../../constants';

const ImpactAnalysis = ({ alert }) => {
  if (!alert) return null;

  const riskColor = getRiskScoreColor(alert.risk_score);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <AlertTriangle className="h-5 w-5 text-orange-500" />
          影响分析
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* 风险评分 */}
        <div className="bg-gray-50 p-4 rounded-lg">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">风险评分</span>
            <span className="text-2xl font-bold" style={{ color: riskColor }}>
              {alert.risk_score}/100
            </span>
          </div>
          <Progress 
            value={alert.risk_score} 
            className="h-3"
            style={{ 
              '--progress-background': riskColor 
            }}
          />
          <p className="text-xs text-gray-500 mt-2">
            {alert.risk_score >= 75 && '极高风险，需立即处理'}
            {alert.risk_score >= 50 && alert.risk_score < 75 && '高风险，需尽快处理'}
            {alert.risk_score >= 25 && alert.risk_score < 50 && '中等风险，需关注'}
            {alert.risk_score < 25 && '低风险，正常跟进'}
          </p>
        </div>

        {/* 影响指标 */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* 预计延期天数 */}
          {alert.estimated_delay_days !== null && (
            <div className="flex items-start gap-3 p-4 bg-red-50 rounded-lg border border-red-200">
              <div className="p-2 bg-red-100 rounded-lg">
                <Clock className="h-5 w-5 text-red-600" />
              </div>
              <div className="flex-1">
                <p className="text-xs text-gray-600 mb-1">预计延期</p>
                <p className="text-2xl font-bold text-red-600">
                  {alert.estimated_delay_days} 天
                </p>
                {alert.is_critical_path && (
                  <Badge variant="destructive" className="mt-2">
                    关键路径
                  </Badge>
                )}
              </div>
            </div>
          )}

          {/* 成本影响 */}
          {alert.estimated_cost_impact !== null && (
            <div className="flex items-start gap-3 p-4 bg-orange-50 rounded-lg border border-orange-200">
              <div className="p-2 bg-orange-100 rounded-lg">
                <DollarSign className="h-5 w-5 text-orange-600" />
              </div>
              <div className="flex-1">
                <p className="text-xs text-gray-600 mb-1">成本影响</p>
                <p className="text-2xl font-bold text-orange-600">
                  ¥{parseFloat(alert.estimated_cost_impact).toLocaleString()}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  包含加急采购溢价和停工损失
                </p>
              </div>
            </div>
          )}
        </div>

        {/* 受影响项目 */}
        {alert.impact_projects && alert.impact_projects.length > 0 && (
          <div className="border-t pt-4">
            <div className="flex items-center gap-2 mb-3">
              <Folder className="h-4 w-4 text-gray-500" />
              <h4 className="font-semibold text-gray-900">
                受影响项目 ({alert.impact_projects.length})
              </h4>
            </div>
            <div className="space-y-2">
              {alert.impact_projects.map((project, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  <div>
                    <p className="font-medium text-gray-900">
                      {project.project_name || `项目 ${project.project_id}`}
                    </p>
                    <p className="text-sm text-gray-500">
                      需求数量: {project.required_qty}
                    </p>
                  </div>
                  <Badge variant="outline">
                    {project.priority || '普通'}
                  </Badge>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 其他指标 */}
        <div className="grid grid-cols-2 gap-4 pt-4 border-t">
          <div>
            <p className="text-sm text-gray-500 mb-1">距离缺料</p>
            <p className="text-lg font-semibold text-gray-900">
              {alert.days_to_shortage} 天
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500 mb-1">在途数量</p>
            <p className="text-lg font-semibold text-gray-900">
              {alert.in_transit_qty || 0}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default ImpactAnalysis;
