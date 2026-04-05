/**
 * 绑定报价对话框
 * 用于绑定报价版本到方案版本和成本估算
 */

import { useState, useEffect } from 'react';


import { cn, formatCurrency } from '../../lib/utils';
import { solutionVersionService } from '../../services/solutionVersionService';

export function BindQuoteDialog({
  isOpen,
  onClose,
  quoteVersionId,
  _solutionId,
  availableSolutionVersions = [],
  availableCostEstimations = [],
  onBind,
}) {
  const [selectedSolutionVersion, setSelectedSolutionVersion] = useState(null);
  const [selectedCostEstimation, setSelectedCostEstimation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // 过滤可用的成本估算（必须绑定到选中的方案版本）
  const filteredCostEstimations = selectedSolutionVersion
    ? availableCostEstimations.filter(
        (ce) => ce.solution_version_id === selectedSolutionVersion.id
      )
    : [];

  // 选择方案版本时重置成本估算
  useEffect(() => {
    setSelectedCostEstimation(null);
  }, [selectedSolutionVersion]);

  // 执行绑定
  const handleBind = async () => {
    if (!selectedSolutionVersion || !selectedCostEstimation) {
      setError('请选择方案版本和成本估算');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const result = await solutionVersionService.bindQuoteVersion(
        quoteVersionId,
        selectedSolutionVersion.id,
        selectedCostEstimation.id
      );
      onBind?.(result);
      onClose();
    } catch (err) {
      setError(err.response?.data?.detail || '绑定失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* 遮罩层 */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* 对话框 */}
      <div className="relative w-full max-w-2xl mx-4 bg-slate-800 rounded-lg shadow-xl border border-slate-700">
        {/* 标题栏 */}
        <div className="flex items-center justify-between p-4 border-b border-slate-700">
          <div className="flex items-center gap-2">
            <Link2 className="h-5 w-5 text-blue-400" />
            <h2 className="text-lg font-semibold text-slate-200">
              绑定方案和成本
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-slate-700 rounded-md transition-colors"
          >
            <X className="h-5 w-5 text-slate-400" />
          </button>
        </div>

        {/* 内容区 */}
        <div className="p-6 space-y-6">
          {/* 错误提示 */}
          {error && (
            <div className="flex items-center gap-2 p-3 bg-red-500/10 border border-red-500/20 rounded-md">
              <AlertTriangle className="h-5 w-5 text-red-400" />
              <span className="text-sm text-red-400">{error}</span>
            </div>
          )}

          {/* 步骤1：选择方案版本 */}
          <div>
            <h3 className="flex items-center gap-2 text-sm font-medium text-slate-300 mb-3">
              <Package className="h-4 w-4 text-blue-400" />
              1. 选择方案版本
            </h3>
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {availableSolutionVersions.length === 0 ? (
                <p className="text-sm text-slate-400 p-3 bg-slate-700/50 rounded-md">
                  暂无可用的方案版本
                </p>
              ) : (
                availableSolutionVersions.map((version) => {
                  const isSelected = selectedSolutionVersion?.id === version.id;
                  const isApproved = version.status === 'approved';

                  return (
                    <button
                      key={version.id}
                      onClick={() => setSelectedSolutionVersion(version)}
                      className={cn(
                        'w-full p-3 rounded-md border text-left transition-colors',
                        isSelected
                          ? 'border-blue-500 bg-blue-500/10'
                          : 'border-slate-600 bg-slate-700/50 hover:border-slate-500'
                      )}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="font-mono font-medium text-slate-200">
                            {version.version_no}
                          </span>
                          <span
                            className={cn(
                              'px-2 py-0.5 rounded text-xs',
                              isApproved
                                ? 'bg-green-500/20 text-green-400'
                                : 'bg-slate-500/20 text-slate-400'
                            )}
                          >
                            {isApproved ? '已审批' : version.status}
                          </span>
                        </div>
                        {isSelected && (
                          <CheckCircle className="h-5 w-5 text-blue-400" />
                        )}
                      </div>
                      {version.change_summary && (
                        <p className="text-xs text-slate-400 mt-1 line-clamp-1">
                          {version.change_summary}
                        </p>
                      )}
                    </button>
                  );
                })
              )}
            </div>
          </div>

          {/* 步骤2：选择成本估算 */}
          <div>
            <h3 className="flex items-center gap-2 text-sm font-medium text-slate-300 mb-3">
              <Calculator className="h-4 w-4 text-green-400" />
              2. 选择成本估算
            </h3>
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {!selectedSolutionVersion ? (
                <p className="text-sm text-slate-400 p-3 bg-slate-700/50 rounded-md">
                  请先选择方案版本
                </p>
              ) : filteredCostEstimations.length === 0 ? (
                <p className="text-sm text-slate-400 p-3 bg-slate-700/50 rounded-md">
                  该方案版本暂无关联的成本估算
                </p>
              ) : (
                filteredCostEstimations.map((cost) => {
                  const isSelected = selectedCostEstimation?.id === cost.id;
                  const isApproved = cost.status === 'approved';

                  return (
                    <button
                      key={cost.id}
                      onClick={() => setSelectedCostEstimation(cost)}
                      className={cn(
                        'w-full p-3 rounded-md border text-left transition-colors',
                        isSelected
                          ? 'border-green-500 bg-green-500/10'
                          : 'border-slate-600 bg-slate-700/50 hover:border-slate-500'
                      )}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-slate-200">
                            {cost.version_no || `成本估算 #${cost.id}`}
                          </span>
                          <span
                            className={cn(
                              'px-2 py-0.5 rounded text-xs',
                              isApproved
                                ? 'bg-green-500/20 text-green-400'
                                : 'bg-slate-500/20 text-slate-400'
                            )}
                          >
                            {isApproved ? '已审批' : cost.status}
                          </span>
                        </div>
                        {isSelected && (
                          <CheckCircle className="h-5 w-5 text-green-400" />
                        )}
                      </div>
                      <div className="flex items-center gap-4 mt-2 text-sm">
                        <span className="text-slate-400">
                          总成本: <span className="text-slate-200">{formatCurrency(cost.total_cost)}</span>
                        </span>
                        {cost.confidence_score && (
                          <span className="text-slate-400">
                            置信度: <span className="text-slate-200">{(cost.confidence_score * 100).toFixed(0)}%</span>
                          </span>
                        )}
                      </div>
                    </button>
                  );
                })
              )}
            </div>
          </div>

          {/* 绑定预览 */}
          {selectedSolutionVersion && selectedCostEstimation && (
            <div className="p-4 bg-slate-700/50 rounded-md border border-slate-600">
              <h3 className="flex items-center gap-2 text-sm font-medium text-slate-300 mb-3">
                <FileText className="h-4 w-4 text-purple-400" />
                绑定预览
              </h3>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-slate-400">方案版本</p>
                  <p className="text-slate-200 font-medium">
                    {selectedSolutionVersion.version_no}
                  </p>
                </div>
                <div>
                  <p className="text-slate-400">成本估算</p>
                  <p className="text-slate-200 font-medium">
                    {formatCurrency(selectedCostEstimation.total_cost)}
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* 底部按钮 */}
        <div className="flex items-center justify-end gap-3 p-4 border-t border-slate-700">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-slate-300 hover:text-slate-200 transition-colors"
          >
            取消
          </button>
          <button
            onClick={handleBind}
            disabled={!selectedSolutionVersion || !selectedCostEstimation || loading}
            className={cn(
              'flex items-center gap-2 px-4 py-2 text-sm rounded-md',
              'bg-blue-600 hover:bg-blue-500 disabled:opacity-50',
              'transition-colors'
            )}
          >
            <Link2 className="h-4 w-4" />
            {loading ? '绑定中...' : '确认绑定'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default BindQuoteDialog;
