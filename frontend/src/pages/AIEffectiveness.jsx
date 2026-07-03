/**
 * AI 效果看板：采纳率统计 + AI 报价对账。
 * 持续优化环节的人工消费入口——经营侧月度复盘看这里决定 AI 建议往哪校准。
 */
import { useEffect, useState } from "react";

import api from "../services/api";

const FEATURE_LABELS = {
  presale_requirement_analysis: "AI 需求分析（确认即采纳）",
  opportunity_solution_review: "AI 方案评审（处置即消费）",
  opportunity_next_action: "AI 推进建议",
  opportunity_quote_estimate: "AI 报价估算",
  opportunity_acceptance_criteria: "AI 验收标准",
};

const TIER_LABELS = { basic: "基础档", standard: "标准档", premium: "高级档" };

const pct = (v) => (v == null ? "—" : `${(v * 100).toFixed(1)}%`);
const money = (v) => (v == null ? "—" : `¥${Number(v).toLocaleString()}`);

export default function AIEffectiveness() {
  const [stats, setStats] = useState(null);
  const [calibration, setCalibration] = useState(null);

  useEffect(() => {
    api.get("/ai-feedback/stats").then(({ data }) => setStats(data?.data || data)).catch(() => setStats({ items: [] }));
    api.get("/ai-feedback/quote-calibration").then(({ data }) => setCalibration(data?.data || data)).catch(() => setCalibration(null));
  }, []);

  const statItems = stats?.items || [];
  const calItems = calibration?.items || [];
  const summary = calibration?.summary || {};

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-xl font-bold">AI 效果看板</h1>
        <p className="text-sm text-muted-foreground">
          采纳率与报价对账：AI 建议是否被用、报价离成交有多远——校准的依据都在这里。
        </p>
      </div>

      <div className="rounded-lg border p-4">
        <div className="font-medium mb-3">👍 各 AI 功能采纳率（同一产出多次反馈按最新计）</div>
        {statItems.length === 0 ? (
          <div className="text-sm text-muted-foreground">暂无反馈数据——在 AI 建议卡片上点"采纳/驳回"即开始积累。</div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-muted-foreground border-b">
                <th className="py-1.5">AI 功能</th>
                <th>反馈数</th>
                <th>采纳</th>
                <th>驳回</th>
                <th>部分</th>
                <th>采纳率</th>
              </tr>
            </thead>
            <tbody>
              {statItems.map((s) => (
                <tr key={s.feature_key} className="border-b last:border-0">
                  <td className="py-1.5">
                    {FEATURE_LABELS[s.feature_key] || s.feature_key}
                    <span className="ml-1 text-xs text-muted-foreground">{s.feature_key}</span>
                  </td>
                  <td>{s.total}</td>
                  <td className="text-emerald-600">{s.adopted}</td>
                  <td className="text-red-500">{s.rejected}</td>
                  <td>{s.partial}</td>
                  <td className="font-medium">{pct(s.adoption_rate)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div className="rounded-lg border p-4">
        <div className="font-medium mb-1">💰 AI 三档报价 vs 成交金额对账</div>
        {!calibration ? (
          <div className="text-sm text-muted-foreground">对账数据加载失败或暂无。</div>
        ) : (
          <>
            <div className="text-xs text-muted-foreground mb-3">
              已成交对账 {summary.matched ?? 0} 单 · 未成交 {summary.unmatched ?? 0} 单
              （实际成本对账待成本归集口径修复后接入）
            </div>
            <div className="grid grid-cols-3 gap-3 mb-4">
              {Object.entries(TIER_LABELS).map(([tier, label]) => (
                <div key={tier} className="rounded border p-2 text-center">
                  <div className="text-xs text-muted-foreground">{label}平均偏差</div>
                  <div className="text-lg font-bold">
                    {pct(summary.mean_abs_deviation?.[tier])}
                  </div>
                </div>
              ))}
            </div>
            {calItems.length > 0 && (
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-xs text-muted-foreground border-b">
                    <th className="py-1.5">商机</th>
                    <th>成交金额</th>
                    <th>基础档</th>
                    <th>标准档</th>
                    <th>高级档</th>
                    <th>最贴近</th>
                  </tr>
                </thead>
                <tbody>
                  {calItems.map((r) => (
                    <tr key={r.presale_ticket_id} className="border-b last:border-0">
                      <td className="py-1.5">#{r.opportunity_id}</td>
                      <td>{money(r.contract_amount)}</td>
                      <td>{money(r.tiers?.basic)}</td>
                      <td>{money(r.tiers?.standard)}</td>
                      <td>{money(r.tiers?.premium)}</td>
                      <td className="font-medium">{r.closest_tier}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </>
        )}
      </div>
    </div>
  );
}
