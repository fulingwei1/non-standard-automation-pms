/**
 * 阶段门校验结果展示组件
 *
 * Issue 1.4 & 3.3: 可视化展示阶段门校验进度，缺失项列表和操作链接
 */

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Progress,
} from "../ui";
import {
  CheckCircle2,
  XCircle,
  AlertCircle,
  ArrowRight,
  ExternalLink,
  RefreshCw,
  Loader2,
} from "lucide-react";
import { cn } from "../../lib/utils";
import { projectApi } from "../../services/api";
import { toast } from "../ui/toast";

// 阶段门配置
const GATE_CONFIG = {
  G1: { name: "G1: 需求进入", from: "S1", to: "S2", description: "需求确认" },
  G2: {
    name: "G2: 方案设计",
    from: "S2",
    to: "S3",
    description: "方案评审通过",
  },
  G3: { name: "G3: 采购备料", from: "S3", to: "S4", description: "合同签订" },
  G4: { name: "G4: 加工制造", from: "S4", to: "S5", description: "BOM发布" },
  G5: { name: "G5: 装配调试", from: "S5", to: "S6", description: "物料齐套" },
  G6: { name: "G6: 出厂验收", from: "S6", to: "S7", description: "装配完成" },
  G7: { name: "G7: 包装发运", from: "S7", to: "S8", description: "FAT通过" },
  G8: { name: "G8: 现场安装", from: "S8", to: "S9", description: "终验收通过" },
};

export default function GateCheckPanel({ projectId, currentStage, onAdvance }) {
  const [loading, setLoading] = useState(false);
  const [gateCheckResult, setGateCheckResult] = useState(null);
  const [targetStage, setTargetStage] = useState(null);

  // 根据当前阶段确定目标阶段
  useEffect(() => {
    if (currentStage) {
      const stageOrder = parseInt(currentStage.replace("S", ""));
      if (stageOrder < 9) {
        const nextStage = `S${stageOrder + 1}`;
        setTargetStage(nextStage);
        loadGateCheckResult(nextStage);
      }
    }
  }, [currentStage, projectId]);

  const loadGateCheckResult = async (stage) => {
    if (!projectId || !stage) return;

    setLoading(true);
    try {
      const response = await projectApi.getGateCheckResult(projectId, stage);
      setGateCheckResult(response.data);
    } catch (err) {
      console.error("Failed to load gate check result:", err);
      toast.error("无法加载阶段门校验结果");
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    if (targetStage) {
      loadGateCheckResult(targetStage);
    }
  };

  const handleAdvance = async () => {
    if (!targetStage) return;

    try {
      const response = await projectApi.advanceStage(projectId, {
        target_stage: targetStage,
        skip_gate_check: false,
      });

      if (response.data?.gate_check_result?.passed) {
        toast.success(`项目已推进至 ${targetStage} 阶段`);
        if (onAdvance) {
          onAdvance();
        }
      } else {
        toast.error(
          response.data?.gate_check_result?.message || "阶段门校验未通过",
        );
      }
    } catch (err) {
      console.error("Failed to advance stage:", err);
      toast.error(err.response?.data?.detail || "无法推进项目阶段");
    }
  };

  if (!targetStage || !gateCheckResult) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="text-center text-slate-400">
            {loading ? (
              <div className="flex items-center justify-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>加载中...</span>
              </div>
            ) : (
              <span>暂无阶段门校验信息</span>
            )}
          </div>
        </CardContent>
      </Card>
    );
  }

  const gateConfig = GATE_CONFIG[gateCheckResult.gate_code] || {
    name: gateCheckResult.gate_name,
    from: gateCheckResult.from_stage,
    to: gateCheckResult.to_stage,
  };

  const progressPct =
    gateCheckResult.total_conditions > 0
      ? (gateCheckResult.passed_conditions / gateCheckResult.total_conditions) *
        100
      : 0;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-lg">{gateConfig.name}</CardTitle>
            <p className="text-sm text-slate-400 mt-1">
              {gateConfig.from} → {gateConfig.to}: {gateConfig.description}
            </p>
          </div>
          <Button
            size="sm"
            variant="ghost"
            onClick={handleRefresh}
            disabled={loading}
          >
            <RefreshCw className={cn("h-4 w-4", loading && "animate-spin")} />
          </Button>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* 校验状态 */}
        <div className="flex items-center justify-between p-4 rounded-xl bg-white/5">
          <div className="flex items-center gap-3">
            {gateCheckResult.passed ? (
              <CheckCircle2 className="h-6 w-6 text-emerald-400" />
            ) : (
              <XCircle className="h-6 w-6 text-red-400" />
            )}
            <div>
              <div className="font-medium text-white">
                {gateCheckResult.passed ? "校验通过" : "校验未通过"}
              </div>
              <div className="text-sm text-slate-400">
                {gateCheckResult.passed_conditions} /{" "}
                {gateCheckResult.total_conditions} 项通过
              </div>
            </div>
          </div>
          <Badge variant={gateCheckResult.passed ? "success" : "destructive"}>
            {gateCheckResult.passed ? "可推进" : "不可推进"}
          </Badge>
        </div>

        {/* 进度条 */}
        <div>
          <div className="flex justify-between text-xs mb-2">
            <span className="text-slate-400">校验进度</span>
            <span className="text-white font-medium">
              {Math.round(progressPct)}%
            </span>
          </div>
          <Progress
            value={progressPct}
            color={gateCheckResult.passed ? "success" : "warning"}
          />
        </div>

        {/* 校验条件列表 */}
        {gateCheckResult.conditions &&
          gateCheckResult.conditions.length > 0 && (
            <div className="space-y-2">
              <div className="text-sm font-medium text-slate-300 mb-2">
                校验条件详情
              </div>
              {gateCheckResult.conditions.map((condition, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className={cn(
                    "flex items-start gap-3 p-3 rounded-lg border",
                    condition.status === "passed"
                      ? "bg-emerald-500/10 border-emerald-500/20"
                      : "bg-red-500/10 border-red-500/20",
                  )}
                >
                  {condition.status === "passed" ? (
                    <CheckCircle2 className="h-5 w-5 text-emerald-400 flex-shrink-0 mt-0.5" />
                  ) : (
                    <XCircle className="h-5 w-5 text-red-400 flex-shrink-0 mt-0.5" />
                  )}
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-white text-sm">
                      {condition.condition_name}
                    </div>
                    {condition.condition_desc && (
                      <div className="text-xs text-slate-400 mt-1">
                        {condition.condition_desc}
                      </div>
                    )}
                    {condition.message && (
                      <div
                        className={cn(
                          "text-xs mt-1",
                          condition.status === "passed"
                            ? "text-emerald-300"
                            : "text-red-300",
                        )}
                      >
                        {condition.message}
                      </div>
                    )}
                    {condition.action_url && condition.action_text && (
                      <Button
                        size="sm"
                        variant="ghost"
                        className="mt-2 h-7 text-xs"
                        onClick={() => {
                          // 导航到操作页面
                          window.location.href = condition.action_url;
                        }}
                      >
                        {condition.action_text}
                        <ExternalLink className="h-3 w-3 ml-1" />
                      </Button>
                    )}
                  </div>
                </motion.div>
              ))}
            </div>
          )}

        {/* 缺失项提示 */}
        {gateCheckResult.missing_items &&
          gateCheckResult.missing_items.length > 0 && (
            <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20">
              <div className="flex items-start gap-2">
                <AlertCircle className="h-5 w-5 text-amber-400 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <div className="font-medium text-amber-300 text-sm mb-1">
                    缺失项
                  </div>
                  <ul className="text-xs text-amber-200/80 space-y-1">
                    {gateCheckResult.missing_items.map((item, index) => (
                      <li key={index}>• {item}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}

        {/* 建议 */}
        {gateCheckResult.suggestions &&
          gateCheckResult.suggestions.length > 0 && (
            <div className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/20">
              <div className="flex items-start gap-2">
                <AlertCircle className="h-5 w-5 text-blue-400 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <div className="font-medium text-blue-300 text-sm mb-1">
                    建议
                  </div>
                  <ul className="text-xs text-blue-200/80 space-y-1">
                    {gateCheckResult.suggestions.map((suggestion, index) => (
                      <li key={index}>• {suggestion}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}

        {/* 操作按钮 */}
        <div className="flex items-center gap-2 pt-2 border-t border-white/10">
          <Button
            variant={gateCheckResult.passed ? "default" : "secondary"}
            onClick={handleAdvance}
            disabled={!gateCheckResult.passed || loading}
            className="flex-1"
          >
            {gateCheckResult.passed ? (
              <>
                推进至 {targetStage} 阶段
                <ArrowRight className="h-4 w-4 ml-2" />
              </>
            ) : (
              "完成缺失项后可推进"
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
