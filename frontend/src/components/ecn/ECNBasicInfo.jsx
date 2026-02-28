/**
 * ECN Basic Info Component
 * ECN 基本信息展示组件
 */

import { Badge } from "../../components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { cn, formatDate } from "../../lib/utils";
import {
  statusConfigs as _statusConfigs,
  typeConfigs as _typeConfigs,
  priorityConfigs as _priorityConfigs,
  getStatusConfig,
  getTypeConfig,
  getPriorityConfig } from
"@/lib/constants/ecn";

export function ECNBasicInfo({ ecn, loading }) {
  if (loading) {
    return (
      <div className="grid grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">基本信息</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="animate-pulse">
              <div className="h-4 bg-slate-700 rounded mb-2" />
              <div className="h-4 bg-slate-700 rounded mb-2" />
              <div className="h-4 bg-slate-700 rounded" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">影响评估</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="animate-pulse">
              <div className="h-4 bg-slate-700 rounded mb-2" />
              <div className="h-4 bg-slate-700 rounded mb-2" />
              <div className="h-4 bg-slate-700 rounded" />
            </div>
          </CardContent>
        </Card>
      </div>);

  }

  const statusConfig = getStatusConfig(ecn.status);
  const typeConfig = getTypeConfig(ecn.change_type);
  const priorityConfig = getPriorityConfig(ecn.priority);

  return (
    <div className="grid grid-cols-2 gap-4">
      {/* 基本信息 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">基本信息</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-sm text-slate-500 mb-1">ECN编号</div>
              <div className="text-white font-mono">{ecn.ecn_no}</div>
            </div>
            <div>
              <div className="text-sm text-slate-500 mb-1">创建日期</div>
              <div className="text-white">{formatDate(ecn.created_time)}</div>
            </div>
            <div>
              <div className="text-sm text-slate-500 mb-1">状态</div>
              <div>
                <Badge className={cn(statusConfig.color, statusConfig.textColor, "text-xs")}>
                  {statusConfig.label}
                </Badge>
              </div>
            </div>
            <div>
              <div className="text-sm text-slate-500 mb-1">优先级</div>
              <div>
                <Badge className={cn(priorityConfig.color, priorityConfig.textColor, "text-xs")}>
                  {priorityConfig.label}
                </Badge>
              </div>
            </div>
            <div>
              <div className="text-sm text-slate-500 mb-1">变更类型</div>
              <div className="flex items-center gap-2">
                <span>{typeConfig.icon}</span>
                <span className="text-white text-sm">{typeConfig.label}</span>
              </div>
            </div>
            <div>
              <div className="text-sm text-slate-500 mb-1">创建人</div>
              <div className="text-white">{ecn.created_by_name || ecn.created_by}</div>
            </div>
          </div>
          
          {/* 变更内容 */}
          <div>
            <div className="text-sm text-slate-500 mb-2">变更内容</div>
            <div className="text-white bg-slate-800/50 p-3 rounded-lg text-sm">
              {ecn.change_content || ecn.description || "-"}
            </div>
          </div>

          {/* 变更原因 */}
          <div>
            <div className="text-sm text-slate-500 mb-2">变更原因</div>
            <div className="text-white bg-slate-800/50 p-3 rounded-lg text-sm">
              {ecn.change_reason || ecn.reason || "-"}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 影响评估 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">影响评估</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-sm text-slate-500 mb-1">成本影响</div>
              <div className="text-white">
                {ecn.cost_impact ? `¥${ecn.cost_impact.toLocaleString()}` : "-"}
              </div>
            </div>
            <div>
              <div className="text-sm text-slate-500 mb-1">进度影响</div>
              <div className="text-white">
                {ecn.schedule_impact ? `${ecn.schedule_impact}天` : "-"}
              </div>
            </div>
            <div>
              <div className="text-sm text-slate-500 mb-1">质量影响</div>
              <div className="text-white">
                {ecn.quality_impact || "-"}
              </div>
            </div>
            <div>
              <div className="text-sm text-slate-500 mb-1">安全影响</div>
              <div className="text-white">
                {ecn.safety_impact || "-"}
              </div>
            </div>
          </div>

          {/* 关联项目 */}
          <div>
            <div className="text-sm text-slate-500 mb-2">关联项目</div>
            <div className="text-white">
              {ecn.project_name || ecn.project_code || "-"}
            </div>
          </div>

          {/* 关联产品 */}
          <div>
            <div className="text-sm text-slate-500 mb-2">关联产品</div>
            <div className="text-white">
              {ecn.product_name || ecn.product_code || "-"}
            </div>
          </div>

          {/* 关联机台 */}
          <div>
            <div className="text-sm text-slate-500 mb-2">关联机台</div>
            <div className="text-white">
              {ecn.machine_name || ecn.machine_code || "-"}
            </div>
          </div>

          {/* 受影响部门 */}
          {ecn.affected_departments && ecn.affected_departments?.length > 0 &&
          <div>
              <div className="text-sm text-slate-500 mb-2">受影响部门</div>
              <div className="flex flex-wrap gap-1">
                {(ecn.affected_departments || []).map((dept, index) =>
              <Badge key={index} variant="outline" className="text-xs">
                    {dept}
              </Badge>
              )}
              </div>
          </div>
          }
        </CardContent>
      </Card>
    </div>);

}