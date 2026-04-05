/**
 * 方案版本历史列表
 * 显示方案的版本历史，支持查看、对比、审批操作
 */

import { useState, useEffect } from 'react';
import {
  CheckCircle,
  Clock,
  XCircle,
  FileEdit,
} from 'lucide-react';
import { cn, formatDate } from '../../lib/utils';
import { solutionVersionService } from '../../services/solutionVersionService';

// 状态配置
const VERSION_STATUS_CONFIG = {
  draft: {
    icon: FileEdit,
    color: 'text-slate-400',
    bgColor: 'bg-slate-500/20',
    label: '草稿',
  },
  pending_review: {
    icon: Clock,
    color: 'text-yellow-400',
    bgColor: 'bg-yellow-500/20',
    label: '待审核',
  },
  approved: {
    icon: CheckCircle,
    color: 'text-green-400',
    bgColor: 'bg-green-500/20',
    label: '已审批',
  },
  rejected: {
    icon: XCircle,
    color: 'text-red-400',
    bgColor: 'bg-red-500/20',
    label: '已驳回',
  },
};

export function SolutionVersionHistory({
  solutionId,
  currentVersionId,
  onVersionSelect,
  onCompare,
  onSubmitReview,
  onApprove,
  className,
}) {
  const [versions, setVersions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState(true);
  const [selectedForCompare, setSelectedForCompare] = useState([]);

  // 加载版本历史
  const loadVersionHistory = async () => {
    if (!solutionId) return;

    setLoading(true);
    try {
      const data = await solutionVersionService.getVersionHistory(solutionId);
      setVersions(data || []);
    } catch (error) {
      console.error('加载版本历史失败:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadVersionHistory();
  }, [solutionId]);

  // 切换选中对比
  const toggleCompareSelection = (versionId) => {
    setSelectedForCompare((prev) => {
      if (prev.includes(versionId)) {
        return prev.filter((id) => id !== versionId);
      }
      if (prev.length >= 2) {
        return [prev[1], versionId];
      }
      return [...prev, versionId];
    });
  };

  // 执行对比
  const handleCompare = () => {
    if (selectedForCompare.length === 2) {
      onCompare?.(selectedForCompare[0], selectedForCompare[1]);
    }
  };

  // 提交审核
  const handleSubmitReview = async (versionId) => {
    try {
      await solutionVersionService.submitForReview(versionId);
      loadVersionHistory();
      onSubmitReview?.(versionId);
    } catch (error) {
      console.error('提交审核失败:', error);
    }
  };

  return (
    <div className={cn('rounded-lg border border-slate-700 bg-slate-800/50', className)}>
      {/* 标题栏 */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center justify-between w-full p-4 text-left"
      >
        <div className="flex items-center gap-2">
          <History className="h-5 w-5 text-blue-400" />
          <span className="font-medium text-slate-200">版本历史</span>
          <span className="text-sm text-slate-400">({versions.length} 个版本)</span>
        </div>
        {expanded ? (
          <ChevronUp className="h-5 w-5 text-slate-400" />
        ) : (
          <ChevronDown className="h-5 w-5 text-slate-400" />
        )}
      </button>

      {/* 版本列表 */}
      {expanded && (
        <div className="border-t border-slate-700">
          {/* 对比工具栏 */}
          {selectedForCompare.length > 0 && (
            <div className="flex items-center justify-between p-3 bg-slate-700/50 border-b border-slate-700">
              <span className="text-sm text-slate-300">
                已选择 {selectedForCompare.length} 个版本
              </span>
              <button
                onClick={handleCompare}
                disabled={selectedForCompare.length !== 2}
                className={cn(
                  'flex items-center gap-1 px-3 py-1.5 text-sm rounded-md',
                  'bg-blue-600 hover:bg-blue-500 disabled:opacity-50',
                  'transition-colors'
                )}
              >
                <GitCompare className="h-4 w-4" />
                对比版本
              </button>
            </div>
          )}

          {loading ? (
            <div className="p-8 text-center text-slate-400">加载中...</div>
          ) : versions.length === 0 ? (
            <div className="p-8 text-center text-slate-400">暂无版本历史</div>
          ) : (
            <div className="divide-y divide-slate-700">
              {versions.map((version) => {
                const statusConfig =
                  VERSION_STATUS_CONFIG[version.status] || VERSION_STATUS_CONFIG.draft;
                const StatusIcon = statusConfig.icon;
                const isCurrent = version.id === currentVersionId;
                const isSelected = selectedForCompare.includes(version.id);

                return (
                  <div
                    key={version.id}
                    className={cn(
                      'p-4 hover:bg-slate-700/30 transition-colors',
                      isCurrent && 'bg-blue-500/10 border-l-2 border-blue-500'
                    )}
                  >
                    <div className="flex items-start justify-between">
                      {/* 版本信息 */}
                      <div className="flex items-start gap-3">
                        {/* 选择框 */}
                        <button
                          onClick={() => toggleCompareSelection(version.id)}
                          className={cn(
                            'w-5 h-5 rounded border mt-0.5 flex items-center justify-center',
                            isSelected
                              ? 'bg-blue-500 border-blue-500'
                              : 'border-slate-500 hover:border-slate-400'
                          )}
                        >
                          {isSelected && <CheckCircle className="h-3 w-3 text-white" />}
                        </button>

                        <div>
                          {/* 版本号和状态 */}
                          <div className="flex items-center gap-2">
                            <span className="font-mono font-medium text-slate-200">
                              {version.version_no}
                            </span>
                            <span
                              className={cn(
                                'inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs',
                                statusConfig.bgColor,
                                statusConfig.color
                              )}
                            >
                              <StatusIcon className="h-3 w-3" />
                              {statusConfig.label}
                            </span>
                            {isCurrent && (
                              <span className="px-2 py-0.5 rounded text-xs bg-blue-500/20 text-blue-400">
                                当前版本
                              </span>
                            )}
                          </div>

                          {/* 变更摘要 */}
                          {version.change_summary && (
                            <p className="text-sm text-slate-400 mt-1 line-clamp-2">
                              {version.change_summary}
                            </p>
                          )}

                          {/* 时间信息 */}
                          <p className="text-xs text-slate-500 mt-2">
                            创建于 {formatDate(version.created_at)}
                          </p>
                        </div>
                      </div>

                      {/* 操作按钮 */}
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => onVersionSelect?.(version)}
                          className="p-2 hover:bg-slate-600 rounded-md transition-colors"
                          title="查看详情"
                        >
                          <Eye className="h-4 w-4 text-slate-400" />
                        </button>

                        {version.status === 'draft' && (
                          <button
                            onClick={() => handleSubmitReview(version.id)}
                            className="p-2 hover:bg-slate-600 rounded-md transition-colors"
                            title="提交审核"
                          >
                            <Send className="h-4 w-4 text-blue-400" />
                          </button>
                        )}

                        {version.status === 'pending_review' && onApprove && (
                          <button
                            onClick={() => onApprove(version.id)}
                            className="p-2 hover:bg-slate-600 rounded-md transition-colors"
                            title="审批"
                          >
                            <CheckCircle className="h-4 w-4 text-green-400" />
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default SolutionVersionHistory;
