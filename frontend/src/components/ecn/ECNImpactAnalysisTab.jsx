import React from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  GitBranch, AlertTriangle, Users, FileText,
  DollarSign, Clock, Package
} from 'lucide-react';
import { cn } from '@/lib/utils';

const fadeIn = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5 } }
};

/**
 * BOM影响分析结果卡片
 */
const BomImpactCard = ({ summary }) => {
  if (!summary || !summary.has_impact) return null;

  return (
    <Card className="border-blue-200 bg-blue-50/30">
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          <GitBranch className="w-5 h-5 text-blue-600" />
          BOM影响分析结果
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-3 gap-4 mb-4">
          <div>
            <div className="text-sm text-slate-500 mb-1">总成本影响</div>
            <div className="text-xl font-bold text-red-600">
              ¥{summary.total_cost_impact?.toLocaleString() || 0}
            </div>
          </div>
          <div>
            <div className="text-sm text-slate-500 mb-1">受影响物料项</div>
            <div className="text-xl font-bold">
              {summary.total_affected_items || 0} 项
            </div>
          </div>
          <div>
            <div className="text-sm text-slate-500 mb-1">最大交期影响</div>
            <div className="text-xl font-bold text-orange-600">
              {summary.max_schedule_impact_days || 0} 天
            </div>
          </div>
        </div>
        
        {summary.bom_impacts && summary.bom_impacts.length > 0 && (
          <div className="space-y-2">
            <div className="text-sm font-medium">BOM影响明细：</div>
            {summary.bom_impacts.map((impact, idx) => (
              <div key={idx} className="p-2 bg-white rounded text-sm">
                BOM #{impact.bom_id}: {impact.affected_item_count}项受影响, 
                成本影响¥{impact.cost_impact?.toLocaleString()}, 
                交期影响{impact.schedule_impact_days}天
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

/**
 * 呆滞料预警卡片
 */
const ObsoleteAlertCard = ({ alert }) => {
  const riskLevelConfig = {
    CRITICAL: { label: '严重', color: 'bg-red-600' },
    HIGH: { label: '高', color: 'bg-red-500' },
    MEDIUM: { label: '中', color: 'bg-orange-500' },
    LOW: { label: '低', color: 'bg-yellow-500' }
  };

  const config = riskLevelConfig[alert.risk_level] || riskLevelConfig.LOW;

  return (
    <Card className="p-3">
      <div className="flex justify-between items-start mb-2">
        <div>
          <div className="font-semibold">{alert.material_name}</div>
          <div className="text-sm text-slate-500 font-mono">{alert.material_code}</div>
        </div>
        <Badge className={config.color}>{config.label}</Badge>
      </div>
      <div className="grid grid-cols-2 gap-2 text-sm">
        <div>
          <span className="text-slate-500">呆滞数量:</span> {alert.obsolete_quantity}
        </div>
        <div>
          <span className="text-slate-500">呆滞金额:</span> ¥{alert.obsolete_value?.toLocaleString()}
        </div>
        <div className="col-span-2">
          <span className="text-slate-500">风险原因:</span> {alert.risk_reason}
        </div>
      </div>
    </Card>
  );
};

/**
 * RCA分析卡片
 */
const RcaAnalysisCard = ({ rcaAnalysis }) => {
  if (!rcaAnalysis) return null;

  const categoryConfig = {
    DESIGN: { label: '设计问题', color: 'bg-blue-500' },
    PROCESS: { label: '工艺问题', color: 'bg-purple-500' },
    MATERIAL: { label: '物料问题', color: 'bg-amber-500' },
    QUALITY: { label: '质量问题', color: 'bg-red-500' },
    OTHER: { label: '其他', color: 'bg-slate-500' }
  };

  const config = categoryConfig[rcaAnalysis.root_cause_category] || categoryConfig.OTHER;

  return (
    <Card className="border-purple-200 bg-purple-50/30">
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          <FileText className="w-5 h-5 text-purple-600" />
          根因分析 (RCA)
          <Badge className={config.color}>{config.label}</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div>
          <div className="text-sm font-medium text-slate-700 mb-1">根本原因：</div>
          <div className="p-3 bg-white rounded text-sm">{rcaAnalysis.root_cause}</div>
        </div>
        <div>
          <div className="text-sm font-medium text-slate-700 mb-1">分析详情：</div>
          <div className="p-3 bg-white rounded text-sm whitespace-pre-wrap">
            {rcaAnalysis.root_cause_analysis}
          </div>
        </div>
        {rcaAnalysis.created_at && (
          <div className="text-xs text-slate-500">
            分析时间: {new Date(rcaAnalysis.created_at).toLocaleString()}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

/**
 * 影响分析标签页组件
 * 
 * @param {Object} props
 * @param {Object} props.ecn - ECN数据
 * @param {Object} props.bomImpactSummary - BOM影响分析摘要
 * @param {Array} props.obsoleteAlerts - 呆滞料预警列表
 * @param {Object} props.rcaAnalysis - RCA分析数据
 * @param {boolean} props.analyzingBom - BOM分析中状态
 * @param {Function} props.onAnalyzeBomImpact - BOM影响分析回调
 * @param {Function} props.onCheckObsoleteRisk - 检查呆滞料风险回调
 * @param {Function} props.onShowResponsibility - 显示责任分摊回调
 * @param {Function} props.onShowRca - 显示RCA分析回调
 */
export const ECNImpactAnalysisTab = ({
  ecn,
  bomImpactSummary,
  obsoleteAlerts = [],
  rcaAnalysis,
  analyzingBom = false,
  onAnalyzeBomImpact,
  onCheckObsoleteRisk,
  onShowResponsibility,
  onShowRca
}) => {
  return (
    <motion.div
      variants={fadeIn}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {/* 操作按钮 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">影响分析工具</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-3">
            <Button
              variant="outline"
              onClick={onAnalyzeBomImpact}
              disabled={analyzingBom || !ecn?.machine_id}
            >
              <GitBranch className="w-4 h-4 mr-2" />
              {analyzingBom ? "分析中..." : "BOM影响分析"}
            </Button>
            <Button
              variant="outline"
              onClick={onCheckObsoleteRisk}
              disabled={analyzingBom}
            >
              <AlertTriangle className="w-4 h-4 mr-2" />
              检查呆滞料风险
            </Button>
            <Button
              variant="outline"
              onClick={onShowResponsibility}
            >
              <Users className="w-4 h-4 mr-2" />
              责任分摊
            </Button>
            <Button
              variant="outline"
              onClick={onShowRca}
            >
              <FileText className="w-4 h-4 mr-2" />
              RCA分析
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* BOM影响分析结果 */}
      <BomImpactCard summary={bomImpactSummary} />

      {/* 呆滞料预警 */}
      {obsoleteAlerts.length > 0 && (
        <Card className="border-red-200 bg-red-50/30">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-red-600" />
              呆滞料预警
              <Badge className="bg-red-500">{obsoleteAlerts.length}</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {obsoleteAlerts.map((alert, idx) => (
                <ObsoleteAlertCard key={idx} alert={alert} />
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* RCA分析 */}
      <RcaAnalysisCard rcaAnalysis={rcaAnalysis} />

      {/* 空状态提示 */}
      {!bomImpactSummary?.has_impact && obsoleteAlerts.length === 0 && !rcaAnalysis && (
        <Card>
          <CardContent className="py-12 text-center">
            <Package className="w-12 h-12 text-slate-400 mx-auto mb-4" />
            <p className="text-slate-500 mb-2">暂无影响分析数据</p>
            <p className="text-sm text-slate-400">
              点击上方按钮执行影响分析操作
            </p>
          </CardContent>
        </Card>
      )}
    </motion.div>
  );
};

export default ECNImpactAnalysisTab;
