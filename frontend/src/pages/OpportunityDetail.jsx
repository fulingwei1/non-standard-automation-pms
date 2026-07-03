/**
 * Opportunity Detail Page - 商机详情页面
 * Features: 商机详情、阶段流转、阶段门管理
 */
import { useState, useEffect, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  RefreshCw,
  CheckCircle2,
  AlertTriangle
} from "lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle
} from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Progress } from "../components/ui/progress";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter
} from "../components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from "../components/ui/select";
import { cn, formatDate } from "../lib/utils";
import api, { opportunityApi } from "../services/api";
import AiFeedbackButtons from "../components/ai/AiFeedbackButtons";
import SolutionReviewCard from "../components/opportunity/SolutionReviewCard";
import WinRateAnalysisCard from "../components/opportunity/WinRateAnalysisCard";
import QuickActivityLog from "../components/sales/QuickActivityLog";

const stageConfigs = {
  DISCOVERY: { label: "发现", color: "bg-blue-500", order: 1 },
  QUALIFICATION: { label: "需求挖掘", color: "bg-amber-500", order: 2 },
  PROPOSAL: { label: "方案介绍", color: "bg-purple-500", order: 3 },
  NEGOTIATION: { label: "价格谈判", color: "bg-orange-500", order: 4 },
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
  const [enriching, setEnriching] = useState(false);
  const handleEnrichRequirement = async () => {
    setEnriching(true);
    try {
      const { data } = await api.post(`/sales/opportunities/${id}/ai-enrich-requirement`);
      await fetchOpportunityDetail();
      const d = data?.data || data;
      alert(`AI 已完善需求：${d?.equipment_type || ""} · 成熟度${d?.requirement_maturity || ""}`);
    } catch (e) {
      alert(e?.response?.data?.detail || "AI 完善需求失败，请先记录一些活动");
    } finally {
      setEnriching(false);
    }
  };
  const [quoting, setQuoting] = useState(false);
  const [quoteEst, setQuoteEst] = useState(null);
  const handleQuoteEstimate = async () => {
    setQuoting(true);
    try {
      const { data } = await api.post(`/sales/opportunities/${id}/ai-quote-estimate`);
      setQuoteEst(data?.data || data);
    } catch (e) {
      alert(e?.response?.data?.detail || "AI 报价失败，请先完善需求");
    } finally {
      setQuoting(false);
    }
  };
  const [acLoading, setAcLoading] = useState(false);
  const [acCriteria, setAcCriteria] = useState(null);
  const handleAcceptanceCriteria = async () => {
    setAcLoading(true);
    try {
      const { data } = await api.post(`/sales/opportunities/${id}/ai-acceptance-criteria`);
      setAcCriteria((data?.data || data)?.acceptance_criteria || []);
    } catch (e) {
      alert(e?.response?.data?.detail || "AI 生成验收标准失败，请先完善需求");
    } finally {
      setAcLoading(false);
    }
  };
  const [reviewLoading, setReviewLoading] = useState(false);
  const [reviews, setReviews] = useState(null);
  const handleSolutionReview = async () => {
    setReviewLoading(true);
    try {
      const { data } = await api.post(`/sales/opportunities/${id}/ai-solution-review`);
      setReviews((data?.data || data)?.reviews || []);
    } catch (e) {
      alert(e?.response?.data?.detail || "AI 方案评审失败，请先完善需求");
    } finally {
      setReviewLoading(false);
    }
  };
  const [similar, setSimilar] = useState(null);
  const handleSimilar = async () => {
    try {
      const { data } = await api.get(`/sales/opportunities/${id}/similar-cases`);
      setSimilar(data?.data || data);
    } catch (e) { alert("检索失败"); }
  };
  const [nextAct, setNextAct] = useState(null);
  const [naLoading, setNaLoading] = useState(false);
  const handleNextAction = async () => {
    setNaLoading(true);
    try {
      const { data } = await api.post(`/sales/opportunities/${id}/ai-next-action`);
      setNextAct(data?.data || data);
    } catch (e) { alert("生成失败"); } finally { setNaLoading(false); }
  };
  const [bomSel, setBomSel] = useState(null);
  const [bomLoading, setBomLoading] = useState(false);
  const handleBomSelection = async () => {
    setBomLoading(true);
    try { const { data } = await api.post(`/ai-eng/bom-selection`, { opportunity_id: Number(id) }); setBomSel((data?.data || data)?.selection || []); }
    catch (e) { alert(e?.response?.data?.detail || "选型失败，请先完善需求"); } finally { setBomLoading(false); }
  };
  const [design, setDesign] = useState(null);
  const [designLoading, setDesignLoading] = useState(false);
  const [coverage, setCoverage] = useState(null);
  const handleConfigDesign = async () => {
    setDesignLoading(true);
    setCoverage(null);
    try {
      // persist=true：方案落库（版本链），随后自动核对需求覆盖
      const { data } = await api.post(`/ai-eng/config-design`, { opportunity_id: Number(id), persist: true });
      const d = data?.data || data;
      setDesign(d);
      if (d?.solution_id) {
        try {
          const cov = await api.post(`/ai-eng/requirement-coverage`, {
            opportunity_id: Number(id), solution_id: d.solution_id,
          });
          setCoverage(cov.data?.data || cov.data);
        } catch (e) { /* 覆盖核对失败不阻断设计结果展示 */ }
      }
    }
    catch (e) { alert(e?.response?.data?.detail || "配置设计失败"); } finally { setDesignLoading(false); }
  };
  const docInputRef = useRef(null);
  const [docUploading, setDocUploading] = useState(false);
  const [docResult, setDocResult] = useState(null);
  const handleRequirementDoc = async (e) => {
    const f = e.target.files?.[0];
    e.target.value = "";
    if (!f) return;
    setDocUploading(true);
    setDocResult(null);
    try {
      const fd = new FormData();
      fd.append("file", f);
      const { data } = await api.post(`/sales/opportunities/${id}/requirement-document`, fd, {
        headers: { "Content-Type": "multipart/form-data" }, timeout: 180000,
      });
      const d = data?.data || data;
      setDocResult({ ...d, message: data?.message });
      await fetchOpportunityDetail();
      // 一步式：抽取成功后自动做需求缺口分析
      if (d?.enrichment) await handleRequirementGaps();
    } catch (err) {
      alert(err?.response?.data?.detail || "需求文档上传失败");
    } finally { setDocUploading(false); }
  };
  const [gaps, setGaps] = useState(null);
  const [gapsLoading, setGapsLoading] = useState(false);
  const handleRequirementGaps = async () => {
    setGapsLoading(true);
    try {
      const { data } = await api.post(`/sales/opportunities/${id}/ai-requirement-gaps`);
      setGaps(data?.data || data);
      await fetchOpportunityDetail(); // 成熟度已按 rubric 回写
    } catch (e) {
      alert(e?.response?.data?.detail || "需求缺口分析失败，请先记录一些活动");
    } finally { setGapsLoading(false); }
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

      {/* 赢单率分析 */}
      <WinRateAnalysisCard opportunity={opportunity} />

      {/* 销售活动（AI智能记录 + 时间线，自动挂本商机/客户） */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>销售活动</CardTitle>
          <div className="flex gap-2">
            <Button size="sm" variant="outline" onClick={handleEnrichRequirement} disabled={enriching}>
              {enriching ? "AI 完善中…" : "✨ AI 完善需求"}
            </Button>
            <Button size="sm" variant="outline" onClick={handleRequirementGaps} disabled={gapsLoading}>
              {gapsLoading ? "AI 分析中…" : "🧭 需求缺口追问"}
            </Button>
            <input ref={docInputRef} type="file" accept=".pdf,.docx,.txt,.md" className="hidden" onChange={handleRequirementDoc} />
            <Button size="sm" variant="outline" onClick={() => docInputRef.current?.click()} disabled={docUploading}>
              {docUploading ? "解析抽取中…" : "📄 传需求文档"}
            </Button>
            <Button size="sm" variant="outline" onClick={handleQuoteEstimate} disabled={quoting}>
              {quoting ? "AI 估价中…" : "💰 AI 报价估算"}
            </Button>
            <Button size="sm" variant="outline" onClick={handleAcceptanceCriteria} disabled={acLoading}>
              {acLoading ? "AI 生成中…" : "📋 AI 验收标准"}
            </Button>
            <Button size="sm" variant="outline" onClick={handleSolutionReview} disabled={reviewLoading}>
              {reviewLoading ? "AI 评审中…" : "🔍 AI 方案评审"}
            </Button>
            <Button size="sm" variant="outline" onClick={handleSimilar}>📚 相似案例</Button>
            <Button size="sm" variant="outline" onClick={handleNextAction} disabled={naLoading}>
              {naLoading ? "AI 中…" : "🎯 推进建议"}
            </Button>
            <Button size="sm" variant="outline" onClick={handleConfigDesign} disabled={designLoading}>
              {designLoading ? "AI 中…" : "🧩 配置式设计"}
            </Button>
            <Button size="sm" variant="outline" onClick={handleBomSelection} disabled={bomLoading}>
              {bomLoading ? "AI 中…" : "🔧 BOM 选型"}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {quoteEst && (
            <div className="mb-4 rounded-lg border border-emerald-500/30 bg-emerald-500/5 p-3 text-sm">
              <div className="font-medium mb-1 flex items-center justify-between">
                <span>💰 AI 报价估算（模块累加+风险加成，可微调）</span>
                <AiFeedbackButtons featureKey="opportunity_quote_estimate" refType="opportunity" refId={Number(id)} />
              </div>
              <div className="text-xs text-muted-foreground mb-2">{quoteEst.basis}</div>
              <div className="space-y-0.5">
                {(quoteEst.recommended_modules || []).map((m, i) => (
                  <div key={i} className="text-xs">· {m.module_name} ×{m.qty} = ¥{m.subtotal}</div>
                ))}
                {(quoteEst.custom_items || []).map((c, i) => (
                  <div key={`c${i}`} className="text-xs text-amber-600">· [定制] {c.name} = ¥{c.cost}</div>
                ))}
              </div>
              <div className="mt-2 grid grid-cols-2 gap-x-4 gap-y-0.5 text-xs">
                <div>材料成本：¥{quoteEst.material_cost}</div>
                <div>风险加成：{quoteEst.risk_factor}%</div>
                <div>含风险成本：¥{quoteEst.suggested_cost}</div>
                <div>建议毛利：{quoteEst.suggested_gross_margin}%</div>
                <div className="col-span-2 text-base font-bold text-emerald-600">建议报价：¥{quoteEst.suggested_price}</div>
              </div>
              {quoteEst.risk_reason && <div className="text-xs text-muted-foreground mt-1">风险原因：{quoteEst.risk_reason}</div>}
            </div>
          )}
          {docResult && (
            <div className="mb-4 rounded-lg border border-sky-500/30 bg-sky-500/5 p-3 text-sm">
              <div className="font-medium mb-1">📄 {docResult.message}</div>
              <div className="text-xs text-muted-foreground">
                {docResult.filename} · 提取 {docResult.extracted_chars} 字 · 活动 {docResult.communication_no} · 累计附件 {docResult.attachment_count} 份
              </div>
              {docResult.enrichment && (
                <div className="text-xs mt-1">
                  抽取回填：设备={docResult.enrichment.equipment_type || "-"} · 预算={docResult.enrichment.budget_range || "-"} ·
                  对象={docResult.enrichment.requirement?.product_object || "-"} · 节拍={docResult.enrichment.requirement?.ct_seconds ?? "-"}s ·
                  验收={docResult.enrichment.requirement?.acceptance_criteria?.slice(0, 40) || "-"}
                </div>
              )}
            </div>
          )}
          {gaps && (
            <div className="mb-4 rounded-lg border border-cyan-500/30 bg-cyan-500/5 p-3 text-sm">
              <div className="font-medium mb-1">
                🧭 需求完备度 {gaps.score}/100
                <span className={`ml-2 text-xs ${gaps.maturity === "HIGH" ? "text-emerald-600" : gaps.maturity === "MEDIUM" ? "text-amber-600" : "text-red-500"}`}>
                  {gaps.maturity}
                </span>
              </div>
              <div className="grid grid-cols-2 gap-x-4 gap-y-0.5 mb-2">
                {(gaps.elements || []).map((e, i) => (
                  <div key={i} className="text-xs" title={e.evidence || ""}>
                    {e.status === "filled" ? "✅" : e.status === "partial" ? "🟡" : "❌"} {e.label}
                  </div>
                ))}
              </div>
              {(gaps.questions || []).length > 0 && (
                <div className="border-t border-cyan-500/20 pt-2">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-medium">📝 下次拜访追问清单</span>
                    <button
                      className="text-[10px] border rounded px-1.5 py-0.5 hover:bg-muted"
                      onClick={() => navigator.clipboard?.writeText((gaps.questions || []).map((q, i) => `${i + 1}. ${q}`).join("\n"))}>
                      复制清单
                    </button>
                  </div>
                  {(gaps.questions || []).map((q, i) => (
                    <div key={i} className="text-xs text-muted-foreground">{i + 1}. {q}</div>
                  ))}
                </div>
              )}
            </div>
          )}
          {design && (
            <div className="mb-4 rounded-lg border border-teal-500/30 bg-teal-500/5 p-3 text-sm">
              <div className="font-medium mb-1">
                🧩 AI 配置式设计（复用率 {design.reuse_rate}）
                {design.solution_no && (
                  <span className="ml-2 text-xs text-emerald-600">已落库 {design.solution_no} {design.solution_version}</span>
                )}
              </div>
              <div className="text-xs text-muted-foreground mb-1">{design.architecture}</div>
              {(design.modules || []).map((m, i) => <div key={i} className="text-xs">· {m.module_name} ×{m.qty} — {m.role}</div>)}
              {(design.custom_parts || []).map((c, i) => <div key={`c${i}`} className="text-xs text-amber-600">· [定制] {c.name}（{c.reason}）</div>)}
              {(design.risk_reminders || []).length > 0 && (
                <div className="mt-2 border-t border-teal-500/20 pt-1.5">
                  <div className="text-xs font-medium mb-0.5">⚠️ 历史坑提醒</div>
                  {(design.risk_reminders || []).map((rr, i) => (
                    <div key={i} className="text-xs text-amber-600">· {rr.reminder} <span className="text-muted-foreground">（{rr.source}）</span></div>
                  ))}
                </div>
              )}
            </div>
          )}
          {coverage && (
            <div className="mb-4 rounded-lg border border-lime-500/30 bg-lime-500/5 p-3 text-sm">
              <div className="font-medium mb-1">
                ✅ 需求-方案符合性矩阵（覆盖率 {coverage.coverage_rate}）
                {(coverage.uncovered || []).length > 0 && (
                  <span className="ml-2 text-xs text-red-500">未覆盖 {(coverage.uncovered || []).length} 项</span>
                )}
              </div>
              <div className="space-y-0.5">
                {(coverage.matrix || []).map((m, i) => (
                  <div key={i} className="text-xs">
                    {m.coverage === "满足" ? "✅" : m.coverage === "部分" ? "🟡" : "❌"} {m.requirement}
                    {m.covered_by && <span className="text-muted-foreground"> ← {m.covered_by}</span>}
                    {m.note && m.coverage !== "满足" && <span className="text-amber-600">（{m.note}）</span>}
                  </div>
                ))}
              </div>
            </div>
          )}
          {bomSel && (
            <div className="mb-4 rounded-lg border p-3 text-sm">
              <div className="font-medium mb-1">🔧 AI BOM 选型</div>
              {bomSel.map((x, i) => (
                <div key={i} className="text-xs"><b>{x.part}</b>：{x.brand_model} <span className="text-emerald-600">¥{x.est_price}</span> <span className="text-muted-foreground">（{x.reason}）</span></div>
              ))}
            </div>
          )}
          {similar && (
            <div className="mb-4 rounded-lg border p-3 text-sm">
              <div className="font-medium mb-1">📚 相似案例（同类『{similar.equipment_type}』）</div>
              {similar.reference && <div className="text-xs text-emerald-600 mb-1">{similar.reference}</div>}
              <div className="space-y-0.5">
                {(similar.cases || []).map((c, i) => (
                  <div key={i} className="text-xs flex justify-between cursor-pointer hover:underline"
                       onClick={() => navigate(`/sales/opportunities/${c.opportunity_id}`)}>
                    <span>· {c.name} <span className={c.stage === "WON" ? "text-emerald-600" : "text-muted-foreground"}>[{c.stage}]</span></span>
                    <span>¥{c.quote_amount || c.est_amount}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
          {nextAct && (
            <div className="mb-4 rounded-lg border border-indigo-500/30 bg-indigo-500/5 p-3 text-sm">
              <div className="font-medium mb-1 flex items-center justify-between">
                <span>🎯 AI 推进建议</span>
                <AiFeedbackButtons featureKey="opportunity_next_action" refType="opportunity" refId={Number(id)} />
              </div>
              <div className="text-xs"><b>下一步：</b>{(nextAct.next_actions || []).join("；")}</div>
              <div className="text-xs text-amber-600"><b>短板：</b>{(nextAct.gaps || []).join("；")}</div>
              <div className="text-xs text-muted-foreground"><b>阶段：</b>{nextAct.stage_advice}</div>
            </div>
          )}
          {reviews && <SolutionReviewCard opportunityId={Number(id)} reviews={reviews} />}
          {acCriteria && (
            <div className="mb-4 rounded-lg border border-blue-500/30 bg-blue-500/5 p-3 text-sm">
              <div className="font-medium mb-2 flex items-center justify-between">
                <span>📋 AI 可测量验收标准（与客户/售前对齐，减少验收扯皮）</span>
                <AiFeedbackButtons featureKey="opportunity_acceptance_criteria" refType="opportunity" refId={Number(id)} />
              </div>
              <div className="space-y-1">
                {acCriteria.map((c, i) => (
                  <div key={i} className="text-xs border-l-2 border-blue-500/40 pl-2">
                    <b>{c.item}</b>：{c.target} <span className="text-muted-foreground">（{c.method}；判定：{c.criteria}）</span>
                  </div>
                ))}
              </div>
            </div>
          )}
          <QuickActivityLog
            opportunityId={opportunity.id}
            customerId={opportunity.customer_id}
          />
        </CardContent>
      </Card>

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
