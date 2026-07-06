// 验厂资料管理（销售提交 + 总监审批 + 资料包预览）
import { useEffect, useState, useCallback } from "react";
import {
  Upload, CheckCircle2, Clock, X, FileText, Eye, Download,
  ExternalLink, Send, Loader2, AlertCircle, ClipboardCheck,
} from "lucide-react";
import { PageHeader } from "../../components/layout";
import {
  Alert, AlertDescription, Badge, Button, Card, CardContent,
  CardHeader, CardTitle, Textarea,
} from "../../components/ui";
import { cn } from "../../lib/utils";
import {
  submitAuditPack, reviewAuditPack, listAuditPacks, getAuditPackDetail,
} from "../../services/api/presaleAuditPack";

const STATUS_CFG = {
  pending: { label: "待审批", variant: "warning", icon: Clock },
  approved: { label: "已通过", variant: "success", icon: CheckCircle2 },
  rejected: { label: "已拒绝", variant: "danger", icon: AlertCircle },
};

export default function AuditPack() {
  const [activeTab, setActiveTab] = useState("submit");
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await listAuditPacks();
      setItems(r?.items || []);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="container mx-auto px-4 py-6">
        <PageHeader title="验厂资料" description="上传客户验厂清单 → 总监审批 → AI 自动准备资料包" />

        {/* Tab */}
        <div className="mb-6 flex gap-2">
          {[
            { key: "submit", label: "提交请求", icon: Upload },
            { key: "list", label: "请求列表", icon: ClipboardCheck },
          ].map((t) => (
            <button
              key={t.key}
              onClick={() => setActiveTab(t.key)}
              className={cn(
                "flex items-center gap-2 rounded-lg border px-4 py-2 text-sm transition",
                activeTab === t.key
                  ? "border-cyan-500/50 bg-cyan-500/15 text-cyan-300"
                  : "border-white/10 bg-white/5 text-slate-400 hover:text-slate-200"
              )}
            >
              <t.icon className="h-4 w-4" />
              {t.label}
            </button>
          ))}
        </div>

        {activeTab === "submit" && <SubmitForm onSubmitted={() => { setActiveTab("list"); load(); }} />}
        {activeTab === "list" && (
          <RequestList items={items} loading={loading} onRefresh={load} />
        )}
      </div>
    </div>
  );
}

// ============= 提交表单 =============

function SubmitForm({ onSubmitted }) {
  const [customerName, setCustomerName] = useState("");
  const [customerIndustry, setCustomerIndustry] = useState("");
  const [auditPurpose, setAuditPurpose] = useState("");
  const [checklistText, setChecklistText] = useState("");
  const [deadline, setDeadline] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const EXAMPLE_CHECKLIST = `1. 公司营业执照副本
2. 高新技术企业证书
3. ISO9001质量管理体系认证
4. 公司简介及发展历程
5. 主要生产设备清单
6. 质量控制流程
7. 主要客户名单及案例
8. 产品技术参数说明
9. 环保合规声明（RoHS）
10. ESD防护体系`;

  const handleSubmit = async () => {
    if (!customerName.trim() || !checklistText.trim()) {
      setError("请填写客户名称和验厂清单");
      return;
    }
    setError("");
    setSubmitting(true);
    try {
      await submitAuditPack({
        customer_name: customerName.trim(),
        customer_industry: customerIndustry.trim() || null,
        audit_purpose: auditPurpose.trim() || null,
        checklist_text: checklistText,
        deadline: deadline || null,
      });
      setCustomerName(""); setCustomerIndustry(""); setAuditPurpose("");
      setChecklistText(""); setDeadline("");
      onSubmitted();
    } catch (e) {
      setError(e?.response?.data?.detail || e.message || "提交失败");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Card className="border-white/10 bg-slate-950/40">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-white">
          <Upload className="h-5 w-5 text-cyan-400" />
          提交验厂资料请求
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && (
          <Alert className="border-red-500/30 bg-red-500/10 text-red-100">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
          <input
            value={customerName}
            onChange={(e) => setCustomerName(e.target.value)}
            placeholder="客户名称 *（如：比亚迪）"
            className="rounded-md border border-white/10 bg-slate-900/60 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-500 focus:border-cyan-500/50 focus:outline-none"
          />
          <input
            value={customerIndustry}
            onChange={(e) => setCustomerIndustry(e.target.value)}
            placeholder="客户行业（如：新能源汽车）"
            className="rounded-md border border-white/10 bg-slate-900/60 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-500 focus:border-cyan-500/50 focus:outline-none"
          />
        </div>

        <input
          value={auditPurpose}
          onChange={(e) => setAuditPurpose(e.target.value)}
          placeholder="验厂目的（如：供应商入库验厂 / 资质审查 / 正式验厂）"
          className="w-full rounded-md border border-white/10 bg-slate-900/60 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-500 focus:border-cyan-500/50 focus:outline-none"
        />

        <div>
          <div className="mb-2 flex items-center justify-between">
            <span className="text-xs text-slate-400">客户验厂清单 *</span>
            <button
              onClick={() => setChecklistText(EXAMPLE_CHECKLIST)}
              className="text-[10px] text-cyan-400 hover:text-cyan-300"
            >
              填入示例清单
            </button>
          </div>
          <Textarea
            value={checklistText}
            onChange={(e) => setChecklistText(e.target.value)}
            placeholder={"把客户发来的验厂清单/问卷内容粘贴到这里，每行一条要求。\nAI 会逐条匹配公司资料，生成资料包。"}
            rows={8}
            className="resize-none border-white/10 bg-slate-900/60 text-slate-100 placeholder:text-slate-500"
          />
        </div>

        <input
          value={deadline}
          onChange={(e) => setDeadline(e.target.value)}
          type="date"
          className="rounded-md border border-white/10 bg-slate-900/60 px-3 py-2 text-sm text-slate-100 focus:border-cyan-500/50 focus:outline-none"
        />

        <Button
          onClick={handleSubmit}
          disabled={submitting}
          className="bg-cyan-600 hover:bg-cyan-500"
        >
          {submitting ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Send className="mr-2 h-4 w-4" />}
          {submitting ? "提交中..." : "提交审批"}
        </Button>
        <p className="text-xs text-slate-500">
          提交后销售总监审批，通过后 AI 自动读清单生成验厂资料包
        </p>
      </CardContent>
    </Card>
  );
}

// ============= 请求列表（含审批 + 预览） =============

function RequestList({ items, loading, onRefresh }) {
  const [detail, setDetail] = useState(null);
  const [reviewComment, setReviewComment] = useState("");
  const [reviewing, setReviewing] = useState(false);

  const handleView = async (id) => {
    const d = await getAuditPackDetail(id);
    setDetail(d);
    setReviewComment("");
  };

  const handleReview = async (action) => {
    if (!detail) return;
    setReviewing(true);
    try {
      await reviewAuditPack(detail.id, action, reviewComment);
      setDetail(null);
      onRefresh();
    } catch (e) { console.error(e); }
    finally { setReviewing(false); }
  };

  if (loading) return <div className="py-8 text-center text-slate-500"><Loader2 className="mx-auto h-6 w-6 animate-spin" /></div>;
  if (items.length === 0) return (
    <Card className="border-white/10 bg-slate-950/40">
      <CardContent className="py-8 text-center text-sm text-slate-500">暂无验厂资料请求</CardContent>
    </Card>
  );

  return (
    <div className="space-y-3">
      {items.map((item) => {
        const sc = STATUS_CFG[item.status] || {};
        return (
          <Card key={item.id} className="border-white/10 bg-slate-950/40 hover:border-white/20">
            <CardContent className="flex items-center justify-between pt-5">
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-slate-100">{item.customer_name}</span>
                  <Badge variant={sc.variant}>{sc.label}</Badge>
                  {item.has_html && <Badge variant="info"><FileText className="mr-1 h-3 w-3" />资料包已生成</Badge>}
                  <span className="text-[10px] text-slate-500">
                    {item.customer_industry || ""} | {item.submitted_by_name} | {item.created_at?.slice(0, 10)}
                  </span>
                </div>
                <p className="mt-1 text-xs text-slate-500">{item.audit_purpose}</p>
                {item.review_comment && (
                  <p className="mt-1 text-[11px] text-amber-300/80">审批意见：{item.review_comment}</p>
                )}
              </div>
              <Button variant="outline" size="sm" onClick={() => handleView(item.id)} className="border-cyan-500/30 text-cyan-300">
                <Eye className="mr-1.5 h-3.5 w-3.5" />
                {item.status === "pending" ? "审批" : "查看"}
              </Button>
            </CardContent>
          </Card>
        );
      })}

      {/* 详情/审批/预览弹层 */}
      {detail && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" onClick={() => setDetail(null)}>
          <div
            className="flex max-h-[90vh] w-full max-w-4xl flex-col overflow-hidden rounded-lg border border-white/10 bg-slate-950"
            onClick={(e) => e.stopPropagation()}
          >
            {/* 头部 */}
            <div className="flex items-center justify-between border-b border-white/10 p-4">
              <div className="flex items-center gap-2">
                <FileText className="h-5 w-5 text-cyan-400" />
                <h2 className="text-lg font-semibold text-white">{detail.customer_name} - 验厂资料</h2>
                <Badge variant={(STATUS_CFG[detail.status] || {}).variant}>{(STATUS_CFG[detail.status] || {}).label}</Badge>
              </div>
              <button onClick={() => setDetail(null)} className="text-slate-400 hover:text-white"><X className="h-5 w-5" /></button>
            </div>

            {/* 内容 */}
            <div className="flex-1 overflow-y-auto p-4">
              {/* 验厂清单 */}
              <div className="mb-4">
                <p className="mb-1 text-xs font-medium text-slate-300">客户验厂清单</p>
                <pre className="whitespace-pre-wrap rounded-lg border border-white/10 bg-slate-900/40 p-3 text-xs text-slate-400">{detail.checklist_text}</pre>
              </div>

              {/* AI 生成的资料包 */}
              {detail.generated_html ? (
                <div>
                  <div className="mb-2 flex items-center justify-between">
                    <p className="text-xs font-medium text-emerald-300">✓ AI 已生成验厂资料包</p>
                    <div className="flex gap-2">
                      <Button variant="outline" size="sm" onClick={() => {
                        const blob = new Blob([detail.generated_html], { type: "text/html;charset=utf-8" });
                        const url = URL.createObjectURL(blob);
                        window.open(url, "_blank");
                        setTimeout(() => URL.revokeObjectURL(url), 5000);
                      }} className="border-cyan-500/30 text-cyan-300">
                        <ExternalLink className="mr-1 h-3 w-3" />新窗口
                      </Button>
                      <Button variant="outline" size="sm" onClick={() => {
                        const blob = new Blob([detail.generated_html], { type: "text/html;charset=utf-8" });
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement("a");
                        a.href = url;
                        a.download = `验厂资料_${detail.customer_name}.html`;
                        a.click();
                        URL.revokeObjectURL(url);
                      }} className="border-white/20 text-slate-300">
                        <Download className="mr-1 h-3 w-3" />下载
                      </Button>
                    </div>
                  </div>
                  <iframe srcDoc={detail.generated_html} className="h-[400px] w-full rounded border border-white/10 bg-white" title="验厂资料包" />
                </div>
              ) : detail.status === "approved" ? (
                <p className="text-sm text-amber-300">资料包生成中...</p>
              ) : (
                <p className="text-sm text-slate-500">审批通过后 AI 自动生成资料包</p>
              )}
            </div>

            {/* 审批操作（仅 pending） */}
            {detail.status === "pending" && (
              <div className="border-t border-white/10 p-4">
                <input
                  value={reviewComment}
                  onChange={(e) => setReviewComment(e.target.value)}
                  placeholder="审批意见（可选）"
                  className="mb-3 w-full rounded border border-white/10 bg-slate-900/60 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-500 focus:border-cyan-500/50 focus:outline-none"
                />
                <div className="flex justify-end gap-2">
                  <Button variant="outline" onClick={() => handleReview("reject")} disabled={reviewing} className="border-red-500/30 text-red-300 hover:bg-red-500/10">
                    <X className="mr-1.5 h-4 w-4" />拒绝
                  </Button>
                  <Button onClick={() => handleReview("approve")} disabled={reviewing} className="bg-emerald-600 hover:bg-emerald-500">
                    {reviewing ? <Loader2 className="mr-1.5 h-4 w-4 animate-spin" /> : <CheckCircle2 className="mr-1.5 h-4 w-4" />}
                    通过（自动生成资料包）
                  </Button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
