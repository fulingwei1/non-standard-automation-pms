/**
 * 预警列表组件
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { ALERT_LEVELS, ALERT_STATUS } from '../../constants';
import { ChevronRight, AlertCircle, Package, Calendar } from 'lucide-react';

const AlertList = ({ alerts = [], loading = false }) => {
  const navigate = useNavigate();

  if (loading) {
    return (
      <Card>
        <CardContent className="p-12 text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-500">加载中...</p>
        </CardContent>
      </Card>
    );
  }

  if (alerts?.length === 0) {
    return (
      <Card>
        <CardContent className="p-12 text-center">
          <AlertCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500">暂无预警数据</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {(alerts || []).map((alert) => {
        const levelConfig = ALERT_LEVELS[alert.alert_level];
        const statusConfig = ALERT_STATUS[alert.status];

        return (
          <Card
            key={alert.id}
            className={`hover:shadow-md transition-shadow cursor-pointer ${levelConfig.borderColor} border-l-4`}
            onClick={() => navigate(`/shortage/alerts/${alert.id}`)}
          >
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  {/* 顶部信息 */}
                  <div className="flex items-start gap-3 mb-3">
                    <span className="text-2xl">{levelConfig.icon}</span>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="font-semibold text-lg">
                          {alert.material_name}
                        </h3>
                        <Badge variant="outline" className={levelConfig.textColor}>
                          {levelConfig.label}
                        </Badge>
                        <Badge variant="outline" className={statusConfig.color}>
                          {statusConfig.label}
                        </Badge>
                      </div>
                      <p className="text-sm text-gray-500">
                        预警单号: {alert.alert_no} | 物料编码: {alert.material_code}
                      </p>
                    </div>
                  </div>

                  {/* 详细信息 */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                    <div className="flex items-center gap-2">
                      <Package className="h-4 w-4 text-gray-400" />
                      <div>
                        <p className="text-xs text-gray-500">缺料数量</p>
                        <p className="font-semibold text-red-600">
                          {alert.shortage_qty} / {alert.required_qty}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Calendar className="h-4 w-4 text-gray-400" />
                      <div>
                        <p className="text-xs text-gray-500">需求日期</p>
                        <p className="font-semibold">
                          {alert.required_date}
                          {alert.days_to_shortage !== undefined && (
                            <span className="text-xs text-gray-500 ml-1">
                              ({alert.days_to_shortage}天后)
                            </span>
                          )}
                        </p>
                      </div>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500 mb-1">风险评分</p>
                      <div className="flex items-center gap-2">
                        <Progress 
                          value={alert.risk_score} 
                          className="flex-1"
                        />
                        <span className="text-sm font-semibold" style={{ 
                          color: levelConfig.color 
                        }}>
                          {alert.risk_score}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* 影响信息 */}
                  {(alert.estimated_delay_days || alert.estimated_cost_impact) && (
                    <div className="flex items-center gap-4 text-sm bg-gray-50 p-3 rounded">
                      {alert.estimated_delay_days && (
                        <div>
                          <span className="text-gray-500">预计延期: </span>
                          <span className="font-semibold text-red-600">
                            {alert.estimated_delay_days} 天
                          </span>
                        </div>
                      )}
                      {alert.estimated_cost_impact && (
                        <div>
                          <span className="text-gray-500">成本影响: </span>
                          <span className="font-semibold text-orange-600">
                            ¥{parseFloat(alert.estimated_cost_impact).toLocaleString()}
                          </span>
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* 右侧箭头 */}
                <ChevronRight className="h-5 w-5 text-gray-400 flex-shrink-0 ml-4" />
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
};

export default AlertList;
