/**
 * AlertListItem - Single alert card in the list
 */

import { motion } from "framer-motion";
import { Eye } from "lucide-react";
import {
  Card,
  CardContent } from
"../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Badge } from "../../components/ui/badge";
import { fadeIn } from "../../lib/animations";
import {
  getAlertLevelConfig,
  getAlertStatusConfig,
  getAlertTypeConfig,
  getAvailableActions } from
"../../components/alert-center";

export default function AlertListItem({
  alert,
  index,
  isSelected,
  onSelect,
  onAcknowledge,
  onResolve,
  onViewDetail
}) {
  const levelConfig = getAlertLevelConfig(alert.alert_level);
  const statusConfig = getAlertStatusConfig(alert.status);
  const typeConfig = getAlertTypeConfig(alert.alert_type);
  const availableActions = getAvailableActions(alert);

  return (
    <motion.div
      key={alert.id}
      variants={fadeIn}
      custom={index}>

      <Card className="bg-slate-800/50 border-slate-700 hover:bg-slate-800/70 transition-colors">
        <CardContent className="p-4">
          <div className="flex items-start justify-between">
            <div className="flex items-start gap-3 flex-1">
              <input
                type="checkbox"
                checked={isSelected}
                onChange={(e) => onSelect(alert.id, e.target.checked)}
                className="mt-1" />

              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-3 mb-2">
                  <div className={`w-3 h-3 rounded-full ${levelConfig.color}`} />
                  <h4 className="text-lg font-semibold text-white">
                    {alert.title || '未命名预警'}
                  </h4>
                  <Badge className={levelConfig.color}>
                    {levelConfig.label}
                  </Badge>
                  <Badge className={statusConfig.color} variant="outline">
                    {statusConfig.label}
                  </Badge>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4 mb-3 text-sm">
                  <div>
                    <span className="text-slate-400">类型:</span>
                    <span className="text-white">{typeConfig.label}</span>
                  </div>
                  <div>
                    <span className="text-slate-400">项目:</span>
                    <span className="text-white">{alert.project_name || '未分配'}</span>
                  </div>
                  <div>
                    <span className="text-slate-400">触发时间:</span>
                    <span className="text-white">
                      {alert.triggered_at ? new Date(alert.triggered_at).toLocaleString() : '-'}
                    </span>
                  </div>
                </div>

                {alert.description &&
                <div className="mb-3">
                    <p className="text-sm text-slate-300 mb-1">描述:</p>
                    <p className="text-sm text-white line-clamp-2">
                      {alert.description}
                    </p>
                </div>
                }

                <div className="flex flex-wrap gap-2">
                  {availableActions.includes('确认') &&
                  <Button
                    size="sm"
                    onClick={() => onAcknowledge(alert.id)}
                    className="bg-blue-500 hover:bg-blue-600">

                      确认
                  </Button>
                  }
                  {availableActions.includes('解决') &&
                  <Button
                    size="sm"
                    onClick={() => onResolve(alert)}
                    className="bg-emerald-500 hover:bg-emerald-600">

                      解决
                  </Button>
                  }
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => onViewDetail(alert)}>

                    <Eye className="h-4 w-4 mr-2" />
                    详情
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
