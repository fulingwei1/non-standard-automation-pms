import { motion } from "framer-motion";
import {
  Edit,
  Trash2,
  Power,
  PowerOff,
  CheckCircle2,
  XCircle,
} from "lucide-react";
import { Card, CardContent } from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Badge } from "../../components/ui/badge";
import { fadeIn } from "../../lib/animations";
import { cn } from "../../lib/utils";
import {
  ruleTypeOptions,
  targetTypeOptions,
  operatorOptions,
  formatFrequency,
  formatLevel,
  getLevelColor,
} from "./constants";

export function RuleCard({ rule, onToggle, onEdit, onDelete }) {
  return (
    <motion.div variants={fadeIn}>
      <Card className="bg-surface-1/50 hover:bg-surface-1 transition-colors">
        <CardContent className="p-4">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <h3 className="text-lg font-semibold text-white">
                  {rule.rule_name}
                </h3>
                {rule.is_system && (
                  <Badge variant="outline" className="text-xs">
                    系统预置
                  </Badge>
                )}
                <Badge
                  variant={rule.is_enabled ? "default" : "secondary"}
                  className={cn(
                    rule.is_enabled
                      ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/30"
                      : "bg-slate-500/20 text-slate-400 border-slate-500/30"
                  )}
                >
                  {rule.is_enabled ? (
                    <>
                      <CheckCircle2 className="w-3 h-3 mr-1" />
                      已启用
                    </>
                  ) : (
                    <>
                      <XCircle className="w-3 h-3 mr-1" />
                      已禁用
                    </>
                  )}
                </Badge>
                <Badge
                  className={`bg-${getLevelColor(rule.alert_level)}-500/20 text-${getLevelColor(rule.alert_level)}-400 border-${getLevelColor(rule.alert_level)}-500/30`}
                >
                  {formatLevel(rule.alert_level)}
                </Badge>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-slate-400 mb-3">
                <div>
                  <span className="text-slate-500">规则编码:</span>{" "}
                  <span className="text-white">{rule.rule_code}</span>
                </div>
                <div>
                  <span className="text-slate-500">规则类型:</span>{" "}
                  <span className="text-white">
                    {ruleTypeOptions.find((o) => o.value === rule.rule_type)
                      ?.label || rule.rule_type}
                  </span>
                </div>
                <div>
                  <span className="text-slate-500">监控对象:</span>{" "}
                  <span className="text-white">
                    {targetTypeOptions.find((o) => o.value === rule.target_type)
                      ?.label || rule.target_type}
                  </span>
                </div>
                <div>
                  <span className="text-slate-500">检查频率:</span>{" "}
                  <span className="text-white">
                    {formatFrequency(rule.check_frequency)}
                  </span>
                </div>
              </div>
              {rule.description && (
                <p className="text-sm text-slate-400 mb-2">
                  {rule.description}
                </p>
              )}
              {rule.threshold_value && (
                <div className="text-sm text-slate-400">
                  <span className="text-slate-500">阈值:</span>{" "}
                  <span className="text-white">{rule.threshold_value}</span>
                  {rule.condition_operator && (
                    <>
                      {" "}
                      <span className="text-slate-500">运算符:</span>{" "}
                      <span className="text-white">
                        {operatorOptions.find(
                          (o) => o.value === rule.condition_operator
                        )?.label || rule.condition_operator}
                      </span>
                    </>
                  )}
                </div>
              )}
            </div>
            <div className="flex items-center gap-2 ml-4">
              <Button
                variant="outline"
                size="sm"
                onClick={() => onToggle(rule)}
                className="gap-2"
                title={rule.is_enabled ? "禁用规则" : "启用规则"}
              >
                {rule.is_enabled ? (
                  <PowerOff className="w-4 h-4" />
                ) : (
                  <Power className="w-4 h-4" />
                )}
              </Button>
              {!rule.is_system && (
                <>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => onEdit(rule)}
                    className="gap-2"
                  >
                    <Edit className="w-4 h-4" />
                    编辑
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => onDelete(rule)}
                    className="gap-2 text-red-400 hover:text-red-300"
                  >
                    <Trash2 className="w-4 h-4" />
                    删除
                  </Button>
                </>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
