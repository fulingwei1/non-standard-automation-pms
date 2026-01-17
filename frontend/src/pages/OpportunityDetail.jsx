/**
 * Opportunity Detail Page - 商机详情页面
 * Features: 商机详情、阶段流转、阶段门管理
 */
import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  Target,
  Building2,
  User,
  Calendar,
  DollarSign,
  TrendingUp,
  RefreshCw,
  CheckCircle2,
  XCircle,
  Clock,
  AlertTriangle } from
"lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle } from
"../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Progress } from "../components/ui/progress";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger } from
"../components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter } from
"../components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue } from
"../components/ui/select";
import { cn, formatDate, formatCurrency as _formatCurrency } from "../lib/utils";
import { opportunityApi } from "../services/api";
const stageConfigs = {
  DISCOVERY: { label: "发现", color: "bg-blue-500", order: 1 },
  QUALIFYING: { label: "资格评估", color: "bg-amber-500", order: 2 },
  PROPOSING: { label: "方案设计", color: "bg-purple-500", order: 3 },
  NEGOTIATING: { label: "商务谈判", color: "bg-orange-500", order: 4 },
  CLOSING: { label: "成交", color: "bg-emerald-500", order: 5 },
  WON: { label: "已成交", color: "bg-green-500", order: 6 },
  LOST: { label: "已丢失", color: "bg-red-500", order: 7 }
};
const gateStatusConfigs = {
  PENDING: { label: "待验证", color: "bg-slate-500" },
  PASS: { label: "已通过", color: "bg-emerald-500" },
  FAIL: { label: "未通过", color: "bg-red-500" }
};
export default function OpportunityDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [opportunity, setOpportunity] = useState(null);
  const [showGateDialog, setShowGateDialog] = useState(false);
  const [gateData, setGateData] = useState({
    gate_type: "G2",
    gate_status: "PASS",
    note: ""
  });
  useEffect(() => {
    if (id) {
      fetchOpportunityDetail();
    }
  }, [id]);
  const fetchOpportunityDetail = async () => {
    try {
      setLoading(true);
      const res = await opportunityApi.get(id);
      setOpportunity(res.data || res);
    } catch (error) {
      console.error("Failed to fetch opportunity detail:", error);
    } finally {
      setLoading(false);
    }
  };
  const handleSubmitGate = async () => {
    try {
      await opportunityApi.submitGate(
        id,
        {
          gate_status: gateData.gate_status,
          note: gateData.note
        },
        gateData.gate_type
      );
      setShowGateDialog(false);
      setGateData({
        gate_type: "G2",
        gate_status: "PASS",
        note: ""
      });
      fetchOpportunityDetail();
      alert("阶段门提交成功");
    } catch (error) {
      console.error("Failed to submit gate:", error);
      alert(
        "提交阶段门失败: " + (error.response?.data?.detail || error.message)
      );
    }
  };
  if (loading) {
    return (
      <div className="space-y-6 p-6">
        <div className="text-center py-8 text-slate-400">加载中...</div>
      </div>);

  }
  if (!opportunity) {
    return (
      <div className="space-y-6 p-6">
        <div className="text-center py-8 text-slate-400">商机不存在</div>
      </div>);

  }
  const currentStageOrder = stageConfigs[opportunity.stage]?.order || 0;
  const totalStages = Object.keys(stageConfigs).filter(
    (k) => k !== "WON" && k !== "LOST"
  ).length;
  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate("/sales/opportunities")}>

            <ArrowLeft className="w-4 h-4 mr-2" />
            返回列表
          </Button>
          <PageHeader
            title={`商机详情 - ${opportunity.opp_code || opportunity.opp_name}`}
            description="商机详情、阶段流转、阶段门管理" />

        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={fetchOpportunityDetail}>
            <RefreshCw className="w-4 h-4 mr-2" />
            刷新
          </Button>
          {opportunity.stage !== "WON" && opportunity.stage !== "LOST" &&
          <Button onClick={() => setShowGateDialog(true)}>
              <CheckCircle2 className="w-4 h-4 mr-2" />
              提交阶段门
            </Button>
          }
        </div>
      </div>
      {/* Stage Progress */}
      <Card>
        <CardHeader>
          <CardTitle>阶段进度</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              {Object.entries(stageConfigs).
              filter(([key]) => key !== "WON" && key !== "LOST").
              map(([key, config]) => {
                const isActive =
                stageConfigs[opportunity.stage]?.order >= config.order;
                const isCurrent = opportunity.stage === key;
                return (
                  <div
                    key={key}
                    className="flex-1 flex flex-col items-center">

                      <div
                      className={cn(
                        "w-12 h-12 rounded-full flex items-center justify-center mb-2",
                        isActive ? config.color : "bg-slate-200",
                        isCurrent && "ring-4 ring-blue-200"
                      )}>

                        {isActive ?
                      <CheckCircle2 className="w-6 h-6 text-white" /> :

                      <div className="w-6 h-6 rounded-full bg-white" />
                      }
                      </div>
                      <div
                      className={cn(
                        "text-sm font-medium",
                        isActive ? "text-slate-900" : "text-slate-400"
                      )}>

                        {config.label}
                      </div>
                      {isCurrent &&
                    <Badge className="mt-1" variant="outline">
                          当前
                        </Badge>
                    }
                    </div>);

              })}
            </div>
            <Progress
              value={currentStageOrder / totalStages * 100}
              className="h-2" />

          </div>
        </CardContent>
      </Card>
      {/* Basic Information */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>基本信息</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <div className="text-sm text-slate-500 mb-1">商机编码</div>
                <div className="font-mono font-medium">
                  {opportunity.opp_code}
                </div>
              </div>
              <div>
                <div className="text-sm text-slate-500 mb-1">商机名称</div>
                <div className="font-medium">{opportunity.opp_name}</div>
              </div>
              <div>
                <div className="text-sm text-slate-500 mb-1">当前阶段</div>
                <Badge
                  className={
                  stageConfigs[opportunity.stage]?.color || "bg-slate-500"
                  }>

                  {stageConfigs[opportunity.stage]?.label || opportunity.stage}
                </Badge>
              </div>
              <div>
                <div className="text-sm text-slate-500 mb-1">客户</div>
                <div>{opportunity.customer_name || "-"}</div>
              </div>
              <div>
                <div className="text-sm text-slate-500 mb-1">负责人</div>
                <div>{opportunity.owner_name || "-"}</div>
              </div>
              <div>
                <div className="text-sm text-slate-500 mb-1">阶段门状态</div>
                <Badge
                  className={
                  gateStatusConfigs[opportunity.gate_status]?.color ||
                  "bg-slate-500"
                  }>

                  {gateStatusConfigs[opportunity.gate_status]?.label ||
                  opportunity.gate_status}
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>商机信息</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {opportunity.budget_range &&
              <div>
                  <div className="text-sm text-slate-500 mb-1">预算范围</div>
                  <div className="font-medium">{opportunity.budget_range}</div>
                </div>
              }
              {opportunity.decision_chain &&
              <div>
                  <div className="text-sm text-slate-500 mb-1">决策链</div>
                  <div>{opportunity.decision_chain}</div>
                </div>
              }
              {opportunity.delivery_window &&
              <div>
                  <div className="text-sm text-slate-500 mb-1">交付窗口</div>
                  <div>{opportunity.delivery_window}</div>
                </div>
              }
              {opportunity.acceptance_basis &&
              <div>
                  <div className="text-sm text-slate-500 mb-1">验收标准</div>
                  <div>{opportunity.acceptance_basis}</div>
                </div>
              }
              {opportunity.score !== null &&
              opportunity.score !== undefined &&
              <div>
                    <div className="text-sm text-slate-500 mb-1">评分</div>
                    <div className="flex items-center gap-2">
                      <span className="text-2xl font-bold">
                        {opportunity.score}
                      </span>
                      <Progress
                    value={opportunity.score}
                    className="flex-1 h-2" />

                    </div>
                  </div>
              }
              {opportunity.gate_passed_at &&
              <div>
                  <div className="text-sm text-slate-500 mb-1">
                    阶段门通过时间
                  </div>
                  <div>{formatDate(opportunity.gate_passed_at)}</div>
                </div>
              }
            </div>
          </CardContent>
        </Card>
      </div>
      {/* Requirement Information */}
      {opportunity.requirement &&
      <Card>
          <CardHeader>
            <CardTitle>需求信息</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {opportunity.requirement.product_object &&
            <div>
                  <div className="text-sm text-slate-500 mb-1">产品对象</div>
                  <div>{opportunity.requirement.product_object}</div>
                </div>
            }
              {opportunity.requirement.ct_seconds &&
            <div>
                  <div className="text-sm text-slate-500 mb-1">节拍(秒)</div>
                  <div>{opportunity.requirement.ct_seconds}</div>
                </div>
            }
              {opportunity.requirement.interface_desc &&
            <div>
                  <div className="text-sm text-slate-500 mb-1">
                    接口/通信协议
                  </div>
                  <div>{opportunity.requirement.interface_desc}</div>
                </div>
            }
              {opportunity.requirement.site_constraints &&
            <div>
                  <div className="text-sm text-slate-500 mb-1">现场约束</div>
                  <div>{opportunity.requirement.site_constraints}</div>
                </div>
            }
              {opportunity.requirement.acceptance_criteria &&
            <div className="md:col-span-4">
                  <div className="text-sm text-slate-500 mb-1">验收依据</div>
                  <div>{opportunity.requirement.acceptance_criteria}</div>
                </div>
            }
            </div>
          </CardContent>
        </Card>
      }
      {/* Gate Dialog */}
      <Dialog open={showGateDialog} onOpenChange={setShowGateDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>提交阶段门</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">
                  阶段门类型 *
                </label>
                <Select
                  value={gateData.gate_type}
                  onValueChange={(val) =>
                  setGateData({ ...gateData, gate_type: val })
                  }>

                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="G1">G1: 线索→商机</SelectItem>
                    <SelectItem value="G2">G2: 商机→报价</SelectItem>
                    <SelectItem value="G3">G3: 报价→合同</SelectItem>
                    <SelectItem value="G4">G4: 合同→项目</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">
                  阶段门状态 *
                </label>
                <Select
                  value={gateData.gate_status}
                  onValueChange={(val) =>
                  setGateData({ ...gateData, gate_status: val })
                  }>

                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="PASS">通过</SelectItem>
                    <SelectItem value="FAIL">未通过</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              {gateData.gate_type === "G2" &&
              <div className="p-3 bg-amber-50 rounded-lg">
                  <div className="flex items-start gap-2">
                    <AlertTriangle className="w-5 h-5 text-amber-600 mt-0.5" />
                    <div className="text-sm text-amber-800">
                      <div className="font-medium mb-1">G2阶段门验证要求：</div>
                      <ul className="list-disc list-inside space-y-1 text-xs">
                        <li>预算范围、决策链、交付窗口、验收标准明确</li>
                        <li>技术可行性初评通过（评分≥60分）</li>
                      </ul>
                    </div>
                  </div>
                </div>
              }
              <div>
                <label className="text-sm font-medium mb-2 block">备注</label>
                <textarea
                  className="w-full min-h-[80px] p-3 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={gateData.note}
                  onChange={(e) =>
                  setGateData({ ...gateData, note: e.target.value })
                  }
                  placeholder="阶段门备注..." />

              </div>
            </div>
          </DialogBody>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowGateDialog(false)}>
              取消
            </Button>
            <Button onClick={handleSubmitGate}>提交</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>);

}