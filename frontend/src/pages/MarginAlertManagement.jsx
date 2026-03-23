/**
 * 毛利率预警管理
 * - 预警配置管理
 * - 待审批预警列表
 * - 审批操作
 * - 预警历史记录
 */

import { useState, useEffect } from "react";
import {
  CheckCircle,
  XCircle,
  Clock,
  Settings,
  Search,
  TrendingDown,
} from "lucide-react";
import { staggerContainer, fadeIn } from "../lib/animations";
import { marginAlertApi } from "../services/api/marginAlert";

// 预警级别颜色映射
const LEVEL_COLORS = {
  GREEN: { bg: "bg-emerald-500/20", text: "text-emerald-400", label: "正常" },
  YELLOW: { bg: "bg-amber-500/20", text: "text-amber-400", label: "警告" },
  RED: { bg: "bg-red-500/20", text: "text-red-400", label: "警报" },
};

// 状态颜色映射
const STATUS_COLORS = {
  PENDING: { bg: "bg-amber-500/20", text: "text-amber-400", label: "待审批" },
  APPROVED: { bg: "bg-emerald-500/20", text: "text-emerald-400", label: "已批准" },
  REJECTED: { bg: "bg-red-500/20", text: "text-red-400", label: "已驳回" },
  ESCALATED: { bg: "bg-purple-500/20", text: "text-purple-400", label: "已升级" },
  CANCELLED: { bg: "bg-slate-500/20", text: "text-slate-400", label: "已取消" },
};

function StatCard({ icon: Icon, label, value, color = "text-white" }) {
  return (
    <div className="bg-surface-1/50 border border-white/5 rounded-xl p-4">
      <div className="flex items-center gap-2 mb-2">
        <Icon className={`w-4 h-4 ${color}`} />
        <span className="text-xs text-slate-400">{label}</span>
      </div>
      <div className={`text-2xl font-bold ${color}`}>{value}</div>
    </div>
  );
}

function AlertBadge({ level }) {
  const config = LEVEL_COLORS[level] || LEVEL_COLORS.GREEN;
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium ${config.bg} ${config.text}`}>
      {config.label}
    </span>
  );
}

function StatusBadge({ status }) {
  const config = STATUS_COLORS[status] || STATUS_COLORS.PENDING;
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium ${config.bg} ${config.text}`}>
      {config.label}
    </span>
  );
}

export default function MarginAlertManagement() {
  const [activeTab, setActiveTab] = useState("pending"); // pending | history | config
  const [pendingAlerts, setPendingAlerts] = useState([]);
  const [historyAlerts, setHistoryAlerts] = useState([]);
  const [configs, setConfigs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedAlert, setSelectedAlert] = useState(null);
  const [approvalModal, setApprovalModal] = useState(false);
  const [approvalForm, setApprovalForm] = useState({ comment: "", validDays: 30 });

  // 加载数据
  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        const [pending, history, configList] = await Promise.all([
          marginAlertApi.listPending().catch(() => ({ data: [] })),
          marginAlertApi.listRecords({ page_size: 50 }).catch(() => ({ data: [] })),
          marginAlertApi.listConfigs().catch(() => ({ data: [] })),
        ]);
        setPendingAlerts(pending.data || pending.items || []);
        setHistoryAlerts(history.data || history.items || []);
        setConfigs(configList.data || configList.items || []);
      } catch (_err) {
        // 非关键操作失败时静默降级
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  // 审批通过
  const handleApprove = async () => {
    if (!selectedAlert) return;
    try {
      await marginAlertApi.approve(selectedAlert.id, {
        comment: approvalForm.comment,
        valid_days: approvalForm.validDays,
      });
      setPendingAlerts((prev) => prev.filter((a) => a.id !== selectedAlert.id));
      setApprovalModal(false);
      setSelectedAlert(null);
      setApprovalForm({ comment: "", validDays: 30 });
    } catch (err) {
      alert("审批失败: " + err.message);
    }
  };

  // 驳回
  const handleReject = async () => {
    if (!selectedAlert || !approvalForm.comment) {
      alert("请填写驳回原因");
      return;
    }
    try {
      await marginAlertApi.reject(selectedAlert.id, {
        comment: approvalForm.comment,
      });
      setPendingAlerts((prev) => prev.filter((a) => a.id !== selectedAlert.id));
      setApprovalModal(false);
      setSelectedAlert(null);
      setApprovalForm({ comment: "", validDays: 30 });
    } catch (err) {
      alert("驳回失败: " + err.message);
    }
  };

  const openApprovalModal = (alert) => {
    setSelectedAlert(alert);
    setApprovalModal(true);
  };

  // 统计数据
  const pendingCount = pendingAlerts.length;
  const approvedCount = historyAlerts.filter((a) => a.status === "APPROVED").length;
  const rejectedCount = historyAlerts.filter((a) => a.status === "REJECTED").length;
  const avgMarginGap = historyAlerts.length > 0
    ? (historyAlerts.reduce((sum, a) => sum + (a.margin_gap || 0), 0) / historyAlerts.length).toFixed(1)
    : 0;

  return (
    <div className="space-y-6">
      <PageHeader title="毛利率预警管理" subtitle="预警审批 · 配置管理 · 历史记录" />

      {loading ? (
        <div className="text-center text-slate-500 py-12">加载中...</div>
      ) : (
        <motion.div variants={staggerContainer} initial="hidden" animate="visible" className="space-y-6">
          {/* 统计卡片 */}
          <motion.div variants={fadeIn} className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard icon={Clock} label="待审批" value={pendingCount} color="text-amber-400" />
            <StatCard icon={CheckCircle} label="已批准" value={approvedCount} color="text-emerald-400" />
            <StatCard icon={XCircle} label="已驳回" value={rejectedCount} color="text-red-400" />
            <StatCard icon={TrendingDown} label="平均毛利差距" value={`${avgMarginGap}%`} color="text-blue-400" />
          </motion.div>

          {/* Tab 切换 */}
          <motion.div variants={fadeIn} className="flex gap-2">
            {[
              { key: "pending", label: "待审批", icon: Clock, count: pendingCount },
              { key: "history", label: "历史记录", icon: Search },
              { key: "config", label: "配置管理", icon: Settings },
            ].map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2 ${
                  activeTab === tab.key
                    ? "bg-blue-600 text-white"
                    : "bg-surface-1/50 text-slate-400 hover:text-white"
                }`}
              >
                <tab.icon className="w-4 h-4" />
                {tab.label}
                {tab.count !== undefined && tab.count > 0 && (
                  <span className="px-1.5 py-0.5 rounded-full bg-red-500 text-white text-xs">
                    {tab.count}
                  </span>
                )}
              </button>
            ))}
          </motion.div>

          {/* 待审批列表 */}
          {activeTab === "pending" && (
            <motion.div variants={fadeIn} className="bg-surface-1/50 border border-white/5 rounded-xl overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-slate-800/50">
                  <tr>
                    <th className="text-left text-slate-400 py-3 px-4">报价</th>
                    <th className="text-left text-slate-400 py-3 px-4">客户</th>
                    <th className="text-right text-slate-400 py-3 px-4">毛利率</th>
                    <th className="text-center text-slate-400 py-3 px-4">预警级别</th>
                    <th className="text-left text-slate-400 py-3 px-4">申请人</th>
                    <th className="text-left text-slate-400 py-3 px-4">申请时间</th>
                    <th className="text-center text-slate-400 py-3 px-4">操作</th>
                  </tr>
                </thead>
                <tbody>
                  {pendingAlerts.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="text-center text-slate-500 py-12">
                        暂无待审批预警
                      </td>
                    </tr>
                  ) : (
                    pendingAlerts.map((alert) => (
                      <tr key={alert.id} className="border-t border-white/5 hover:bg-white/[0.02]">
                        <td className="py-3 px-4 text-slate-300">
                          {alert.quote?.code || `报价 #${alert.quote_id}`}
                        </td>
                        <td className="py-3 px-4 text-slate-400">
                          {alert.customer?.name || "-"}
                        </td>
                        <td className="py-3 px-4 text-right">
                          <span className={`font-mono ${
                            alert.gross_margin > 20 ? "text-amber-400" : "text-red-400"
                          }`}>
                            {alert.gross_margin}%
                          </span>
                        </td>
                        <td className="py-3 px-4 text-center">
                          <AlertBadge level={alert.alert_level} />
                        </td>
                        <td className="py-3 px-4 text-slate-400">
                          {alert.requester?.name || "-"}
                        </td>
                        <td className="py-3 px-4 text-slate-500 text-xs">
                          {new Date(alert.requested_at).toLocaleString()}
                        </td>
                        <td className="py-3 px-4 text-center">
                          <button
                            onClick={() => openApprovalModal(alert)}
                            className="px-3 py-1 bg-blue-600 hover:bg-blue-500 text-white text-xs rounded transition-colors"
                          >
                            审批
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </motion.div>
          )}

          {/* 历史记录 */}
          {activeTab === "history" && (
            <motion.div variants={fadeIn} className="bg-surface-1/50 border border-white/5 rounded-xl overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-slate-800/50">
                  <tr>
                    <th className="text-left text-slate-400 py-3 px-4">报价</th>
                    <th className="text-right text-slate-400 py-3 px-4">毛利率</th>
                    <th className="text-center text-slate-400 py-3 px-4">级别</th>
                    <th className="text-center text-slate-400 py-3 px-4">状态</th>
                    <th className="text-left text-slate-400 py-3 px-4">审批人</th>
                    <th className="text-left text-slate-400 py-3 px-4">审批时间</th>
                  </tr>
                </thead>
                <tbody>
                  {historyAlerts.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="text-center text-slate-500 py-12">
                        暂无历史记录
                      </td>
                    </tr>
                  ) : (
                    historyAlerts.map((alert) => (
                      <tr key={alert.id} className="border-t border-white/5 hover:bg-white/[0.02]">
                        <td className="py-3 px-4 text-slate-300">
                          {alert.quote?.code || `报价 #${alert.quote_id}`}
                        </td>
                        <td className="py-3 px-4 text-right font-mono text-slate-300">
                          {alert.gross_margin}%
                        </td>
                        <td className="py-3 px-4 text-center">
                          <AlertBadge level={alert.alert_level} />
                        </td>
                        <td className="py-3 px-4 text-center">
                          <StatusBadge status={alert.status} />
                        </td>
                        <td className="py-3 px-4 text-slate-400">
                          {alert.approver?.name || "-"}
                        </td>
                        <td className="py-3 px-4 text-slate-500 text-xs">
                          {alert.approved_at ? new Date(alert.approved_at).toLocaleString() : "-"}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </motion.div>
          )}

          {/* 配置管理 */}
          {activeTab === "config" && (
            <motion.div variants={fadeIn} className="space-y-4">
              <div className="flex justify-between items-center">
                <h3 className="text-sm font-medium text-white">预警阈值配置</h3>
                <button className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white text-sm rounded-lg flex items-center gap-1">
                  <Plus className="w-4 h-4" />
                  新增配置
                </button>
              </div>

              <div className="grid gap-4">
                {configs.length === 0 ? (
                  <div className="text-center text-slate-500 py-12 bg-surface-1/50 border border-white/5 rounded-xl">
                    暂无配置，请添加预警阈值配置
                  </div>
                ) : (
                  configs.map((config) => (
                    <div
                      key={config.id}
                      className="bg-surface-1/50 border border-white/5 rounded-xl p-4"
                    >
                      <div className="flex items-start justify-between">
                        <div>
                          <h4 className="text-white font-medium">{config.name}</h4>
                          <p className="text-xs text-slate-500 mt-1">{config.code}</p>
                        </div>
                        <div className="flex items-center gap-2">
                          {config.is_default && (
                            <span className="px-2 py-0.5 bg-blue-500/20 text-blue-400 text-xs rounded">
                              默认
                            </span>
                          )}
                          <button className="p-1 hover:bg-white/5 rounded">
                            <Eye className="w-4 h-4 text-slate-400" />
                          </button>
                        </div>
                      </div>

                      <div className="grid grid-cols-4 gap-4 mt-4">
                        <div>
                          <span className="text-xs text-slate-500">标准毛利率</span>
                          <div className="text-emerald-400 font-mono">{config.standard_margin}%</div>
                        </div>
                        <div>
                          <span className="text-xs text-slate-500">警告阈值</span>
                          <div className="text-amber-400 font-mono">{config.warning_margin}%</div>
                        </div>
                        <div>
                          <span className="text-xs text-slate-500">警报阈值</span>
                          <div className="text-red-400 font-mono">{config.alert_margin}%</div>
                        </div>
                        <div>
                          <span className="text-xs text-slate-500">最低毛利率</span>
                          <div className="text-red-500 font-mono">{config.minimum_margin}%</div>
                        </div>
                      </div>

                      {(config.customer_level || config.project_type || config.industry) && (
                        <div className="flex gap-2 mt-3 pt-3 border-t border-white/5">
                          {config.customer_level && (
                            <span className="px-2 py-0.5 bg-slate-700 text-slate-300 text-xs rounded">
                              客户等级: {config.customer_level}
                            </span>
                          )}
                          {config.project_type && (
                            <span className="px-2 py-0.5 bg-slate-700 text-slate-300 text-xs rounded">
                              项目类型: {config.project_type}
                            </span>
                          )}
                          {config.industry && (
                            <span className="px-2 py-0.5 bg-slate-700 text-slate-300 text-xs rounded">
                              行业: {config.industry}
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  ))
                )}
              </div>
            </motion.div>
          )}
        </motion.div>
      )}

      {/* 审批弹窗 */}
      {approvalModal && selectedAlert && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-slate-900 border border-white/10 rounded-xl p-6 w-full max-w-lg">
            <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-amber-400" />
              毛利率预警审批
            </h3>

            <div className="space-y-4">
              {/* 预警信息 */}
              <div className="bg-slate-800/50 rounded-lg p-4 space-y-2">
                <div className="flex justify-between">
                  <span className="text-slate-400">报价编号</span>
                  <span className="text-white">{selectedAlert.quote?.code || `#${selectedAlert.quote_id}`}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">当前毛利率</span>
                  <span className={`font-mono ${
                    selectedAlert.gross_margin > 20 ? "text-amber-400" : "text-red-400"
                  }`}>
                    {selectedAlert.gross_margin}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">预警级别</span>
                  <AlertBadge level={selectedAlert.alert_level} />
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">毛利差距</span>
                  <span className="text-red-400 font-mono">-{selectedAlert.margin_gap}%</span>
                </div>
              </div>

              {/* 申请理由 */}
              {selectedAlert.justification && (
                <div>
                  <label className="text-xs text-slate-400 mb-1 block">申请理由</label>
                  <div className="bg-slate-800/50 rounded-lg p-3 text-sm text-slate-300">
                    {selectedAlert.justification}
                  </div>
                </div>
              )}

              {/* 审批意见 */}
              <div>
                <label className="text-xs text-slate-400 mb-1 block">审批意见 *</label>
                <textarea
                  className="w-full bg-slate-800 border border-white/10 rounded-lg px-3 py-2 text-sm text-slate-300 resize-none"
                  rows={3}
                  placeholder="请输入审批意见..."
                  value={approvalForm.comment}
                  onChange={(e) => setApprovalForm({ ...approvalForm, comment: e.target.value })}
                />
              </div>

              {/* 有效期 */}
              <div>
                <label className="text-xs text-slate-400 mb-1 block">批准有效期（天）</label>
                <input
                  type="number"
                  className="w-full bg-slate-800 border border-white/10 rounded-lg px-3 py-2 text-sm text-slate-300"
                  value={approvalForm.validDays}
                  onChange={(e) => setApprovalForm({ ...approvalForm, validDays: parseInt(e.target.value) || 30 })}
                />
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={handleReject}
                className="flex-1 py-2.5 bg-red-600 hover:bg-red-500 text-white rounded-lg flex items-center justify-center gap-2"
              >
                <XCircle className="w-4 h-4" />
                驳回
              </button>
              <button
                onClick={handleApprove}
                className="flex-1 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg flex items-center justify-center gap-2"
              >
                <CheckCircle className="w-4 h-4" />
                批准
              </button>
            </div>

            <button
              onClick={() => {
                setApprovalModal(false);
                setSelectedAlert(null);
              }}
              className="w-full mt-3 py-2 text-slate-400 hover:text-white text-sm"
            >
              取消
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
