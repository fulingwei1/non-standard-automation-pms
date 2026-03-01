/**
 * 多币种管理
 * - 汇率看板（卡片式显示各币种当前汇率，带涨跌指示）
 * - 快速换算工具（输入金额、选择币种、实时计算）
 * - 汇率历史趋势（简单表格展示）
 * - 项目外币汇总表
 * - 手动更新汇率的表单
 */

import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import {
  TrendingUp,
  TrendingDown,
  Minus,
  RefreshCw,
  DollarSign,
  Euro,
  PoundSterling,
  Wallet,
  History,
  Calculator,
  Edit3,
  Check,
  X,
  Globe,
  ArrowRightLeft,
} from "lucide-react";
import { PageHeader } from "../components/layout";
import { staggerContainer, fadeIn } from "../lib/animations";
import { multiCurrencyApi } from "../services/api/multiCurrency";

// 币种图标映射
const currencyIcons = {
  USD: DollarSign,
  EUR: Euro,
  GBP: PoundSterling,
  JPY: DollarSign,
  CNY: Wallet,
  KRW: Wallet,
  TWD: Wallet,
};

// 币种名称映射
const currencyNames = {
  CNY: "人民币",
  USD: "美元",
  EUR: "欧元",
  JPY: "日元",
  GBP: "英镑",
  KRW: "韩元",
  TWD: "新台币",
};

function CurrencyCard({ currency, rate, change, onEdit }) {
  const Icon = currencyIcons[currency] || Wallet;
  const isPositive = change > 0;
  const isNegative = change < 0;

  return (
    <motion.div
      variants={fadeIn}
      className="bg-surface-1/50 border border-white/5 rounded-xl p-4 hover:border-white/10 transition-colors"
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500/20 to-purple-500/20 flex items-center justify-center">
            <Icon className="w-4 h-4 text-blue-400" />
          </div>
          <div>
            <div className="text-sm font-bold text-white">{currency}</div>
            <div className="text-[10px] text-slate-500">{currencyNames[currency]}</div>
          </div>
        </div>
        {onEdit && (
          <button
            onClick={() => onEdit(currency)}
            className="p-1.5 hover:bg-white/5 rounded-lg transition-colors"
          >
            <Edit3 className="w-3 h-3 text-slate-400" />
          </button>
        )}
      </div>

      <div className="text-2xl font-bold text-white mb-2">
        ¥{rate.toFixed(4)}
        <span className="text-xs text-slate-500 ml-1">/ {currency}</span>
      </div>

      <div className="flex items-center gap-1 text-xs">
        {isPositive ? (
          <TrendingUp className="w-3 h-3 text-emerald-400" />
        ) : isNegative ? (
          <TrendingDown className="w-3 h-3 text-red-400" />
        ) : (
          <Minus className="w-3 h-3 text-slate-500" />
        )}
        <span className={isPositive ? "text-emerald-400" : isNegative ? "text-red-400" : "text-slate-500"}>
          {change >= 0 ? "+" : ""}{change.toFixed(2)}%
        </span>
        <span className="text-slate-600 ml-1">24h</span>
      </div>
    </motion.div>
  );
}

function ConverterCard({ rates: _rates }) {
  const [fromCurrency, setFromCurrency] = useState("USD");
  const [toCurrency, setToCurrency] = useState("CNY");
  const [amount, setAmount] = useState(1000);
  const [result, setResult] = useState(null);
  const [_converting, setConverting] = useState(false);

  const handleConvert = useCallback(async () => {
    try {
      setConverting(true);
      const res = await multiCurrencyApi.convert({
        from_currency: fromCurrency,
        to_currency: toCurrency,
        amount: amount,
      });
      setResult(res.data || res);
    } catch (err) {
      console.error("Conversion failed:", err);
    } finally {
      setConverting(false);
    }
  }, [fromCurrency, toCurrency, amount]);

  // 自动换算
  useEffect(() => {
    const timer = setTimeout(() => {
      if (amount > 0) {
        handleConvert();
      }
    }, 500);
    return () => clearTimeout(timer);
  }, [amount, fromCurrency, toCurrency, handleConvert]);

  return (
    <motion.div variants={fadeIn} className="bg-surface-1/50 border border-white/5 rounded-xl p-5">
      <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
        <ArrowRightLeft className="w-4 h-4 text-purple-400" /> 快速换算
      </h3>

      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-xs text-slate-400 mb-1 block">从</label>
            <select
              className="w-full bg-slate-800 border border-white/10 rounded-lg px-3 py-2 text-sm text-slate-300"
              value={fromCurrency || "unknown"}
              onChange={(e) => setFromCurrency(e.target.value)}
            >
              {Object.keys(currencyNames).map((c) => (
                <option key={c} value={c || "unknown"}>{currencyNames[c]} ({c})</option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-xs text-slate-400 mb-1 block">到</label>
            <select
              className="w-full bg-slate-800 border border-white/10 rounded-lg px-3 py-2 text-sm text-slate-300"
              value={toCurrency || "unknown"}
              onChange={(e) => setToCurrency(e.target.value)}
            >
              {Object.keys(currencyNames).map((c) => (
                <option key={c} value={c || "unknown"}>{currencyNames[c]} ({c})</option>
              ))}
            </select>
          </div>
        </div>

        <div>
          <label className="text-xs text-slate-400 mb-1 block">金额</label>
          <input
            type="number"
            className="w-full bg-slate-800 border border-white/10 rounded-lg px-3 py-2 text-sm text-slate-300"
            value={amount || "unknown"}
            onChange={(e) => setAmount(parseFloat(e.target.value) || 0)}
          />
        </div>

        {result && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-gradient-to-r from-purple-500/10 to-blue-500/10 border border-purple-500/20 rounded-lg p-4"
          >
            <div className="text-center">
              <div className="text-xs text-slate-400 mb-1">换算结果</div>
              <div className="text-2xl font-bold text-white">
                {result.to_currency === "CNY" ? "¥" : result.to_currency}{" "}
                {result.converted_amount.toLocaleString()}
              </div>
              <div className="text-xs text-slate-500 mt-1">
                汇率：1 {result.from_currency} = {result.rate.toFixed(6)} {result.to_currency}
              </div>
            </div>
          </motion.div>
        )}
      </div>
    </motion.div>
  );
}

function HistoryTable({ history, loading }) {
  if (loading) {
    return <div className="text-center text-slate-500 py-8">加载中...</div>;
  }

  return (
    <motion.div variants={fadeIn} className="bg-surface-1/50 border border-white/5 rounded-xl p-5">
      <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
        <History className="w-4 h-4 text-amber-400" /> 汇率历史
      </h3>

      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-white/10">
              <th className="text-left text-slate-400 py-2 px-2">币种</th>
              <th className="text-right text-slate-400 py-2 px-2">汇率</th>
              <th className="text-left text-slate-400 py-2 px-2">时间</th>
              <th className="text-left text-slate-400 py-2 px-2">备注</th>
            </tr>
          </thead>
          <tbody>
            {history.length === 0 ? (
              <tr>
                <td colSpan={4} className="text-center text-slate-500 py-8">暂无历史记录</td>
              </tr>
            ) : (
              history.map((record, idx) => (
                <tr key={idx} className="border-b border-white/5 hover:bg-white/[0.02]">
                  <td className="py-2 px-2">
                    <span className="font-medium text-slate-300">{record.currency}</span>
                  </td>
                  <td className="py-2 px-2 text-right text-slate-300 font-mono">
                    ¥{record.rate.toFixed(4)}
                  </td>
                  <td className="py-2 px-2 text-slate-500">
                    {new Date(record.recorded_at).toLocaleString("zh-CN")}
                  </td>
                  <td className="py-2 px-2 text-slate-500 truncate max-w-[200px]">
                    {record.note || "-"}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </motion.div>
  );
}

function UpdateRateForm({ currency, currentRate, onClose, onSuccess }) {
  const [rate, setRate] = useState(currentRate);
  const [note, setNote] = useState("");
  const [updating, setUpdating] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      setUpdating(true);
      await multiCurrencyApi.updateRate({
        currency,
        rate: parseFloat(rate),
        note: note || undefined,
      });
      onSuccess();
    } catch (err) {
      console.error("Update failed:", err);
      alert("更新失败：" + (err.response?.data?.detail || err.message));
    } finally {
      setUpdating(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50"
      onClick={onClose}
    >
      <div
        className="bg-surface-1 border border-white/10 rounded-xl p-6 w-full max-w-md"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className="text-lg font-bold text-white mb-4">
          更新 {currency} 汇率
        </h3>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-xs text-slate-400 mb-1 block">当前汇率</label>
            <div className="text-2xl font-bold text-slate-500">¥{currentRate.toFixed(4)}</div>
          </div>

          <div>
            <label className="text-xs text-slate-400 mb-1 block">新汇率</label>
            <input
              type="number"
              step="0.0001"
              className="w-full bg-slate-800 border border-white/10 rounded-lg px-3 py-2 text-sm text-slate-300"
              value={rate || "unknown"}
              onChange={(e) => setRate(e.target.value)}
              autoFocus
            />
          </div>

          <div>
            <label className="text-xs text-slate-400 mb-1 block">备注（可选）</label>
            <input
              type="text"
              className="w-full bg-slate-800 border border-white/10 rounded-lg px-3 py-2 text-sm text-slate-300"
              value={note || "unknown"}
              onChange={(e) => setNote(e.target.value)}
              placeholder="例如：央行公布新汇率"
            />
          </div>

          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 py-2.5 bg-slate-700 hover:bg-slate-600 text-white text-sm font-medium rounded-lg transition-colors flex items-center justify-center gap-2"
            >
              <X className="w-4 h-4" /> 取消
            </button>
            <button
              type="submit"
              disabled={updating}
              className="flex-1 py-2.5 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 text-white text-sm font-medium rounded-lg transition-colors flex items-center justify-center gap-2"
            >
              <Check className="w-4 h-4" /> {updating ? "更新中..." : "确认更新"}
            </button>
          </div>
        </form>
      </div>
    </motion.div>
  );
}

function ProjectSummaryTable({ projects }) {
  if (!projects || projects.length === 0) {
    return null;
  }

  return (
    <motion.div variants={fadeIn} className="bg-surface-1/50 border border-white/5 rounded-xl p-5">
      <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
        <Globe className="w-4 h-4 text-emerald-400" /> 项目外币汇总（示例）
      </h3>

      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-white/10">
              <th className="text-left text-slate-400 py-2 px-2">项目</th>
              <th className="text-right text-slate-400 py-2 px-2">原币</th>
              <th className="text-right text-slate-400 py-2 px-2">原币金额</th>
              <th className="text-right text-slate-400 py-2 px-2">汇率</th>
              <th className="text-right text-slate-400 py-2 px-2">折合人民币</th>
              <th className="text-right text-slate-400 py-2 px-2">汇兑损益</th>
            </tr>
          </thead>
          <tbody>
            {projects.map((p) => (
              <tr key={p.project_id} className="border-b border-white/5 hover:bg-white/[0.02]">
                <td className="py-2 px-2">
                  <div className="text-slate-300">{p.project_name}</div>
                  <div className="text-slate-500 text-[10px]">{p.project_code}</div>
                </td>
                <td className="py-2 px-2 text-right">
                  <span className="text-slate-400">{p.original_currency}</span>
                </td>
                <td className="py-2 px-2 text-right text-slate-300">
                  {p.original_currency} {p.original_amount.toLocaleString()}
                </td>
                <td className="py-2 px-2 text-right text-slate-500 font-mono">
                  {p.rate_to_cny.toFixed(4)}
                </td>
                <td className="py-2 px-2 text-right text-emerald-400 font-mono">
                  ¥{p.amount_cny.toLocaleString()}
                </td>
                <td className={`py-2 px-2 text-right font-mono ${
                  p.fx_gain_loss > 0 ? "text-emerald-400" :
                  p.fx_gain_loss < 0 ? "text-red-400" : "text-slate-500"
                }`}>
                  {p.fx_gain_loss ? (p.fx_gain_loss > 0 ? "+" : "") + p.fx_gain_loss.toLocaleString() : "-"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </motion.div>
  );
}

export default function MultiCurrency() {
  const [rates, setRates] = useState([]);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editingCurrency, setEditingCurrency] = useState(null);

  const loadRates = useCallback(async () => {
    try {
      const res = await multiCurrencyApi.getRates();
      setRates(res.data || res);
    } catch (err) {
      console.error("Failed to load rates:", err);
    }
  }, []);

  const loadHistory = useCallback(async () => {
    try {
      const res = await multiCurrencyApi.getHistory({ limit: 20 });
      setHistory(res.data || res);
    } catch (err) {
      console.error("Failed to load history:", err);
    }
  }, []);

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        await Promise.all([loadRates(), loadHistory()]);
      } catch (err) {
        console.error("Failed to load data:", err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [loadRates, loadHistory]);

  const handleEditSuccess = () => {
    setEditingCurrency(null);
    loadRates();
    loadHistory();
  };

  // 示例项目数据（实际应从 API 获取）
  const sampleProjects = [
    {
      project_id: 1,
      project_name: "某海外自动化产线项目",
      project_code: "PRJ-2026-001",
      original_currency: "USD",
      original_amount: 500000,
      rate_to_cny: 7.24,
      amount_cny: 3620000,
      fx_gain_loss: null,
    },
    {
      project_id: 2,
      project_name: "欧洲客户检测设备",
      project_code: "PRJ-2026-002",
      original_currency: "EUR",
      original_amount: 300000,
      rate_to_cny: 7.85,
      amount_cny: 2355000,
      fx_gain_loss: null,
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="多币种管理"
        subtitle="汇率看板 · 快速换算 · 历史记录"
        onRefresh={() => { loadRates(); loadHistory(); }}
      />

      {loading ? (
        <div className="text-center text-slate-500 py-12">加载中...</div>
      ) : (
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="space-y-6"
        >
          {/* 汇率看板 */}
          <motion.div variants={fadeIn} className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
            {rates.map((r) => (
              <CurrencyCard
                key={r.currency}
                currency={r.currency}
                rate={r.rate}
                change={r.change_24h || 0}
                onEdit={setEditingCurrency}
              />
            ))}
          </motion.div>

          {/* 两列布局：换算工具 + 更新表单提示 */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <ConverterCard rates={rates} />

            {/* 快速操作提示 */}
            <motion.div variants={fadeIn} className="bg-surface-1/50 border border-white/5 rounded-xl p-5">
              <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
                <RefreshCw className="w-4 h-4 text-blue-400" /> 快速操作
              </h3>
              <div className="space-y-3">
                <div className="flex items-start gap-3 p-3 bg-white/[0.02] rounded-lg">
                  <Edit3 className="w-4 h-4 text-blue-400 mt-0.5" />
                  <div>
                    <div className="text-xs text-slate-300">手动更新汇率</div>
                    <div className="text-[10px] text-slate-500">点击任意币种卡片右上角的编辑按钮</div>
                  </div>
                </div>
                <div className="flex items-start gap-3 p-3 bg-white/[0.02] rounded-lg">
                  <Calculator className="w-4 h-4 text-purple-400 mt-0.5" />
                  <div>
                    <div className="text-xs text-slate-300">实时换算</div>
                    <div className="text-[10px] text-slate-500">使用左侧换算工具，支持任意币种互转</div>
                  </div>
                </div>
                <div className="flex items-start gap-3 p-3 bg-white/[0.02] rounded-lg">
                  <History className="w-4 h-4 text-amber-400 mt-0.5" />
                  <div>
                    <div className="text-xs text-slate-300">查看历史</div>
                    <div className="text-[10px] text-slate-500">下方表格展示最近 20 条汇率变更记录</div>
                  </div>
                </div>
              </div>
            </motion.div>
          </div>

          {/* 项目外币汇总 */}
          <ProjectSummaryTable projects={sampleProjects} />

          {/* 汇率历史 */}
          <HistoryTable history={history} loading={loading} />
        </motion.div>
      )}

      {/* 编辑汇率弹窗 */}
      {editingCurrency && (
        <UpdateRateForm
          currency={editingCurrency}
          currentRate={rates.find((r) => r.currency === editingCurrency)?.rate || 0}
          onClose={() => setEditingCurrency(null)}
          onSuccess={handleEditSuccess}
        />
      )}
    </div>
  );
}
