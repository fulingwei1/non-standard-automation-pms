// 售前方案审核队列（售前工程师用）
import { useEffect, useState } from "react";
import { Clock, CheckCircle2, AlertCircle, GitBranch, Eye, X } from "lucide-react";
import { PageHeader } from "../../components/layout";
import { Alert, AlertDescription, Badge, Button, Card, CardContent, Textarea } from "../../components/ui";
import { cn } from "../../lib/utils";
import {
  listProposals, getProposalDetail, reviewProposal,
} from "../../services/api/presaleProposals";

export default function PresaleProposalReview() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("pending_review");
  const [detail, setDetail] = useState(null); // 选中的方案详情
  const [reviewComment, setReviewComment] = useState("");
  const [reviewing, setReviewing] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const r = await listProposals(filter);
      setItems(r?.items || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [filter]);

  const handleView = async (id) => {
    const d = await getProposalDetail(id);
    setDetail(d);
    setReviewComment("");
  };

  const handleReview = async (action) => {
    if (!detail) return;
    setReviewing(true);
    try {
      await reviewProposal(detail.id, action, reviewComment);
      setDetail(null);
      load();
    } catch (e) {
      console.error(e);
    } finally {
      setReviewing(false);
    }
  };

  const statusCfg = {
    draft: { label: "迭代中", variant: "info" },
    pending_review: { label: "待审核", variant: "warning" },
    approved: { label: "已通过", variant: "success" },
    rejected: { label: "已打回", variant: "danger" },
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="container mx-auto px-4 py-6">
        <PageHeader
          title="售前方案审核"
          description="审核销售提交的售前方案，通过/打回/修改"
        />

        {/* 状态筛选 */}
        <div className="mb-4 flex gap-2">
          {[
            { key: "pending_review", label: "待审核" },
            { key: "approved", label: "已通过" },
            { key: "rejected", label: "已打回" },
            { key: "draft", label: "迭代中" },
          ].map((f) => (
            <button
              key={f.key}
              onClick={() => setFilter(f.key)}
              className={cn(
                "rounded-full border px-4 py-1.5 text-xs transition",
                filter === f.key
                  ? "border-cyan-500/50 bg-cyan-500/15 text-cyan-300"
                  : "border-white/10 bg-white/5 text-slate-400 hover:text-slate-200"
              )}
            >
              {f.label}
            </button>
          ))}
        </div>

        {/* 方案列表 */}
        <div className="space-y-3">
          {loading ? (
            <div className="py-8 text-center text-slate-500">加载中...</div>
          ) : items.length === 0 ? (
            <Card className="border-white/10 bg-slate-950/40">
              <CardContent className="py-8 text-center text-sm text-slate-500">
                暂无{statusCfg[filter]?.label || ""}方案
              </CardContent>
            </Card>
          ) : (
            items.map((p) => {
              const sc = statusCfg[p.status] || {};
              return (
                <Card key={p.id} className="border-white/10 bg-slate-950/40 hover:border-white/20">
                  <CardContent className="flex items-center justify-between pt-5">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-slate-100">{p.title}</span>
                        <Badge variant={sc.variant}>{sc.label}</Badge>
                        <span className="text-[10px] text-slate-500">
                          v{p.version_count} · {p.created_by_name} · {p.created_at?.slice(5, 16)}
                        </span>
                      </div>
                      <p className="mt-1 text-xs text-slate-500">{p.requirement_text}</p>
                      {p.review_comment && (
                        <p className="mt-1 text-[11px] text-amber-300/80">审核意见：{p.review_comment}</p>
                      )}
                    </div>
                    <Button variant="outline" size="sm" onClick={() => handleView(p.id)} className="border-cyan-500/30 text-cyan-300">
                      <Eye className="mr-1.5 h-3.5 w-3.5" />
                      查看
                    </Button>
                  </CardContent>
                </Card>
              );
            })
          )}
        </div>

        {/* 详情/审核弹层 */}
        {detail && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" onClick={() => setDetail(null)}>
            <div
              className="flex max-h-[90vh] w-full max-w-5xl flex-col overflow-hidden rounded-lg border border-white/10 bg-slate-950"
              onClick={(e) => e.stopPropagation()}
            >
              {/* 头部 */}
              <div className="flex items-center justify-between border-b border-white/10 p-4">
                <div className="flex items-center gap-2">
                  <GitBranch className="h-5 w-5 text-violet-400" />
                  <h2 className="text-lg font-semibold text-white">{detail.title}</h2>
                  <Badge variant={(statusCfg[detail.status] || {}).variant}>
                    {(statusCfg[detail.status] || {}).label}
                  </Badge>
                </div>
                <button onClick={() => setDetail(null)} className="text-slate-400 hover:text-white">
                  <X className="h-5 w-5" />
                </button>
              </div>

              {/* 内容区 */}
              <div className="flex-1 overflow-y-auto p-4">
                {/* 迭代历史 */}
                <p className="mb-2 text-xs font-medium text-slate-300">迭代历史（{detail.versions?.length || 0} 版）</p>
                <div className="mb-4 space-y-1.5">
                  {(detail.versions || []).map((v, i) => (
                    <div key={i} className="rounded border border-white/5 bg-slate-900/40 p-2 text-xs">
                      <div className="flex items-center gap-2">
                        <Badge variant={v.operation === "create" ? "info" : v.operation === "submit" ? "warning" : v.operation === "approve" ? "success" : v.operation === "reject" ? "danger" : "secondary"}>
                          v{v.version_no} {v.operation}
                        </Badge>
                        <span className="text-slate-500">{v.operated_by_name}</span>
                        <span className="text-[10px] text-slate-600">{v.created_at?.slice(5, 16)}</span>
                      </div>
                      {v.change_request && v.change_request !== "(AI 初稿)" && v.change_request !== "(提交审核)" && (
                        <p className="mt-1 text-slate-400">📝 {v.change_request}</p>
                      )}
                      {v.changes_summary && (
                        <p className="mt-0.5 text-cyan-300/80">→ {v.changes_summary}</p>
                      )}
                    </div>
                  ))}
                </div>

                {/* 方案内容摘要 */}
                <p className="mb-2 text-xs font-medium text-slate-300">方案内容摘要</p>
                <ProposalSummary solution={detail.current_solution} />
              </div>

              {/* 审核操作（仅 pending_review） */}
              {detail.status === "pending_review" && (
                <div className="border-t border-white/10 p-4">
                  <Textarea
                    value={reviewComment}
                    onChange={(e) => setReviewComment(e.target.value)}
                    placeholder="审核意见（可选）：通过理由 / 打回原因 / 修改建议"
                    rows={2}
                    className="mb-3 resize-none border-white/10 bg-slate-900/60 text-slate-100"
                  />
                  <div className="flex justify-end gap-2">
                    <Button
                      variant="outline"
                      onClick={() => handleReview("reject")}
                      disabled={reviewing}
                      className="border-red-500/30 text-red-300 hover:bg-red-500/10"
                    >
                      <AlertCircle className="mr-1.5 h-4 w-4" />
                      打回修改
                    </Button>
                    <Button
                      onClick={() => handleReview("approve")}
                      disabled={reviewing}
                      className="bg-emerald-600 hover:bg-emerald-500"
                    >
                      <CheckCircle2 className="mr-1.5 h-4 w-4" />
                      通过定稿
                    </Button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// 方案内容摘要（精简展示）
function ProposalSummary({ solution }) {
  if (!solution) return <p className="text-sm text-slate-500">无方案数据</p>;
  const steps = solution.steps || {};
  const ds = steps.deep_solution || {};
  const dsData = ds.ok ? ds : (steps.generate_solution?.solution || {});

  return (
    <div className="space-y-2 text-xs">
      {dsData.system_architecture && (
        <div><span className="text-slate-500">架构：</span><span className="text-slate-300">{dsData.system_architecture}</span></div>
      )}
      {dsData.line_layout && (
        <div><span className="text-slate-500">布局：</span><span className="text-slate-300">{dsData.line_layout}</span></div>
      )}
      {dsData.tiers?.length > 0 && (
        <div>
          <span className="text-slate-500">报价档位：</span>
          {dsData.tiers.map((t, i) => (
            <span key={i} className="mr-2 text-emerald-300">{t.tier}: {t.price}</span>
          ))}
        </div>
      )}
      {dsData.equipment_selection?.length > 0 && (
        <div>
          <span className="text-slate-500">设备选型（{dsData.equipment_selection.length}项）：</span>
          <div className="mt-1 ml-4 text-slate-400">
            {dsData.equipment_selection.slice(0, 6).map((e, i) => (
              <div key={i}>· {e.item}: {e.brand_suggestion}</div>
            ))}
          </div>
        </div>
      )}
      {steps.risk_warnings?.risks?.length > 0 && (
        <div>
          <span className="text-slate-500">关键风险：</span>
          {steps.risk_warnings.risks.slice(0, 3).map((r, i) => (
            <span key={i} className="mr-2 text-amber-300">[{r.severity}] {r.tag || r.category}</span>
          ))}
        </div>
      )}
    </div>
  );
}
