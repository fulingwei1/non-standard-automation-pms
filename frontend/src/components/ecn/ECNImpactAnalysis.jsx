/**
 * ECN Impact Analysis Component
 * ECN 影响分析组件
 */

import { useState } from "react";
import { Badge } from "../../components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Textarea } from "../../components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter } from
"../../components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue } from
"../../components/ui/select";
import {
  GitBranch,
  AlertTriangle,
  Users,
  DollarSign,
  Calendar,
  FileText,
  TrendingUp } from
"lucide-react";
import {
  impactTypeConfigs as _impactTypeConfigs } from
"@/lib/constants/ecn";
import { cn as _cn, formatDate as _formatDate } from "../../lib/utils";

export function ECNImpactAnalysis({
  ecn,
  bomImpactSummary,
  obsoleteRisks,
  onAnalyzeBomImpact,
  onCheckObsoleteRisk,
  onResponsibilityAllocation,
  onRcaAnalysis,
  analyzingBom
}) {
  const [showResponsibilityDialog, setShowResponsibilityDialog] = useState(false);
  const [showRcaDialog, setShowRcaDialog] = useState(false);
  const [responsibilityForm, setResponsibilityForm] = useState({
    allocation_type: "",
    allocation_description: ""
  });
  const [rcaForm, setRcaForm] = useState({
    root_cause: "",
    root_cause_analysis: "",
    root_cause_category: ""
  });

  const handleResponsibilityAllocation = () => {
    onResponsibilityAllocation({
      ecn_id: ecn.id,
      ...responsibilityForm,
      allocated_by: "current_user",
      allocated_time: new Date().toISOString()
    });
    setResponsibilityForm({
      allocation_type: "",
      allocation_description: ""
    });
    setShowResponsibilityDialog(false);
  };

  const handleRcaAnalysis = () => {
    onRcaAnalysis({
      ecn_id: ecn.id,
      ...rcaForm,
      analyzed_by: "current_user",
      analyzed_time: new Date().toISOString()
    });
    setRcaForm({
      root_cause: "",
      root_cause_analysis: "",
      root_cause_category: ""
    });
    setShowRcaDialog(false);
  };

  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle className="text-base">影响分析工具</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-3">
            <Button
              variant="outline"
              onClick={onAnalyzeBomImpact}
              disabled={analyzingBom || !ecn.machine_id}
              className="h-auto p-4 flex flex-col items-center gap-2">

              <GitBranch className="w-6 h-6" />
              <span>BOM影响分析</span>
              <span className="text-xs opacity-70">
                {analyzingBom ? "分析中..." : "分析BOM变更影响"}
              </span>
            </Button>
            
            <Button
              variant="outline"
              onClick={onCheckObsoleteRisk}
              disabled={analyzingBom}
              className="h-auto p-4 flex flex-col items-center gap-2">

              <AlertTriangle className="w-6 h-6" />
              <span>检查呆滞料风险</span>
              <span className="text-xs opacity-70">识别物料呆滞风险</span>
            </Button>
            
            <Button
              variant="outline"
              onClick={() => setShowResponsibilityDialog(true)}
              className="h-auto p-4 flex flex-col items-center gap-2">

              <Users className="w-6 h-6" />
              <span>责任分摊</span>
              <span className="text-xs opacity-70">分配变更责任</span>
            </Button>
            
            <Button
              variant="outline"
              onClick={() => setShowRcaDialog(true)}
              className="h-auto p-4 flex flex-col items-center gap-2">

              <FileText className="w-6 h-6" />
              <span>RCA分析</span>
              <span className="text-xs opacity-70">根本原因分析</span>
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* BOM影响分析结果 */}
      {bomImpactSummary && bomImpactSummary.has_impact &&
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
                  ¥{bomImpactSummary.total_cost_impact?.toLocaleString() || 0}
                </div>
              </div>
              <div>
                <div className="text-sm text-slate-500 mb-1">受影响物料项</div>
                <div className="text-xl font-bold">
                  {bomImpactSummary.total_affected_items || 0} 项
                </div>
              </div>
              <div>
                <div className="text-sm text-slate-500 mb-1">最大交期影响</div>
                <div className="text-xl font-bold text-orange-600">
                  {bomImpactSummary.max_schedule_impact_days || 0} 天
                </div>
              </div>
            </div>
            
            {bomImpactSummary.bom_impacts && bomImpactSummary.bom_impacts?.length > 0 &&
          <div className="space-y-2">
                <div className="text-sm font-medium">BOM影响明细：</div>
                {(bomImpactSummary.bom_impacts || []).map((impact, idx) =>
            <div key={idx} className="p-2 bg-white rounded text-sm">
                    BOM #{impact.bom_id}: {impact.affected_item_count}
                    项受影响, 成本影响¥{impact.cost_impact?.toLocaleString()}, 
                    交期影响{impact.schedule_impact_days}天
            </div>
            )}
          </div>
          }
          </CardContent>
      </Card>
      }

      {/* 呆滞料风险分析结果 */}
      {obsoleteRisks && obsoleteRisks.length > 0 &&
      <Card className="border-red-200 bg-red-50/30">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-red-600" />
              呆滞料风险分析
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {(obsoleteRisks || []).map((risk, idx) =>
            <Card key={idx} className="p-3">
                  <div className="flex justify-between items-start">
                    <div>
                      <div className="font-medium">{risk.material_code}</div>
                      <div className="text-sm text-slate-600">{risk.material_name}</div>
                      <div className="text-sm text-slate-500">
                        库存量: {risk.current_stock} {risk.unit}
                      </div>
                    </div>
                    <div className="text-right">
                      <Badge className="bg-red-100 text-red-800">
                        风险值: {risk.risk_score}
                      </Badge>
                      <div className="text-sm text-slate-600 mt-1">
                        损失约: ¥{risk.potential_loss?.toLocaleString()}
                      </div>
                    </div>
                  </div>
            </Card>
            )}
            </div>
          </CardContent>
      </Card>
      }

      {/* 责任分摊对话框 */}
      <Dialog open={showResponsibilityDialog} onOpenChange={setShowResponsibilityDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>责任分摊</DialogTitle>
          </DialogHeader>
          <DialogBody className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block">分摊类型</label>
              <Select
                value={responsibilityForm.allocation_type}
                onValueChange={(value) =>
                setResponsibilityForm({ ...responsibilityForm, allocation_type: value })
                }>

                <SelectTrigger>
                  <SelectValue placeholder="选择分摊类型" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="COST">成本分摊</SelectItem>
                  <SelectItem value="RESPONSIBILITY">责任分摊</SelectItem>
                  <SelectItem value="WORKLOAD">工作量分摊</SelectItem>
                  <SelectItem value="RISK">风险分摊</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">分摊说明</label>
              <Textarea
                value={responsibilityForm.allocation_description}
                onChange={(e) =>
                setResponsibilityForm({ ...responsibilityForm, allocation_description: e.target.value })
                }
                placeholder="详细描述分摊方案..."
                rows={4} />

            </div>
          </DialogBody>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowResponsibilityDialog(false)}>
              取消
            </Button>
            <Button onClick={handleResponsibilityAllocation}>确认分摊</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* RCA分析对话框 */}
      <Dialog open={showRcaDialog} onOpenChange={setShowRcaDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>根本原因分析 (RCA)</DialogTitle>
          </DialogHeader>
          <DialogBody className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block">根本原因</label>
              <Textarea
                value={rcaForm.root_cause}
                onChange={(e) =>
                setRcaForm({ ...rcaForm, root_cause: e.target.value })
                }
                placeholder="分析问题的根本原因..."
                rows={3} />

            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">原因分析</label>
              <Textarea
                value={rcaForm.root_cause_analysis}
                onChange={(e) =>
                setRcaForm({ ...rcaForm, root_cause_analysis: e.target.value })
                }
                placeholder="详细的原因分析过程..."
                rows={4} />

            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">原因分类</label>
              <Select
                value={rcaForm.root_cause_category}
                onValueChange={(value) =>
                setRcaForm({ ...rcaForm, root_cause_category: value })
                }>

                <SelectTrigger>
                  <SelectValue placeholder="选择原因分类" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="DESIGN">设计问题</SelectItem>
                  <SelectItem value="PROCESS">工艺问题</SelectItem>
                  <SelectItem value="MATERIAL">材料问题</SelectItem>
                  <SelectItem value="EQUIPMENT">设备问题</SelectItem>
                  <SelectItem value="HUMAN">人员问题</SelectItem>
                  <SelectItem value="ENVIRONMENT">环境问题</SelectItem>
                  <SelectItem value="MANAGEMENT">管理问题</SelectItem>
                  <SelectItem value="EXTERNAL">外部因素</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </DialogBody>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowRcaDialog(false)}>
              取消
            </Button>
            <Button onClick={handleRcaAnalysis}>保存分析</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>);

}