/**
 * 绑定验证状态卡片
 * 显示报价版本与方案、成本的绑定状态和问题列表
 */

import { useState, useEffect } from 'react';
import {
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Link2,
  Info,
} from 'lucide-react';
import { cn, formatDate } from '../../lib/utils';
import { solutionVersionService } from '../../services/solutionVersionService';

// 状态配置
const STATUS_CONFIG = {
  valid: {
    icon: CheckCircle2,
    color: 'text-green-500',
    bgColor: 'bg-green-500/10',
    borderColor: 'border-green-500/20',
    label: '绑定有效',
  },
  outdated: {
    icon: AlertTriangle,
    color: 'text-yellow-500',
    bgColor: 'bg-yellow-500/10',
    borderColor: 'border-yellow-500/20',
    label: '需要更新',
  },
  invalid: {
    icon: XCircle,
    color: 'text-red-500',
    bgColor: 'bg-red-500/10',
    borderColor: 'border-red-500/20',
    label: '绑定无效',
  },
  pending: {
    icon: Link2,
    color: 'text-slate-400',
    bgColor: 'bg-slate-500/10',
    borderColor: 'border-slate-500/20',
    label: '待绑定',
  },
};

// 问题级别配置
const ISSUE_LEVEL_CONFIG = {
  error: {
    icon: XCircle,
    color: 'text-red-400',
    bgColor: 'bg-red-500/10',
  },
  warning: {
    icon: AlertTriangle,
    color: 'text-yellow-400',
    bgColor: 'bg-yellow-500/10',
  },
  info: {
    icon: Info,
    color: 'text-blue-400',
    bgColor: 'bg-blue-500/10',
  },
};

export function BindingValidationCard({
  quoteVersionId,
  initialStatus = 'pending',
  onStatusChange,
  onSyncCost,
  className,
}) {
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [validation, setValidation] = useState(null);
  const [status, setStatus] = useState(initialStatus);

  // 执行验证
  const handleValidate = async () => {
    if (!quoteVersionId) return;

    setLoading(true);
    try {
      const result = await solutionVersionService.validateBinding(quoteVersionId);
      setValidation(result);
      setStatus(result.status);
      onStatusChange?.(result.status, result);
    } catch (error) {
      console.error('验证绑定失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 同步成本
  const handleSyncCost = async () => {
    if (!quoteVersionId) return;

    setSyncing(true);
    try {
      const result = await solutionVersionService.syncCostToQuote(quoteVersionId);
      onSyncCost?.(result);
      // 同步后重新验证
      await handleValidate();
    } catch (error) {
      console.error('同步成本失败:', error);
    } finally {
      setSyncing(false);
    }
  };

  // 初始化时验证
  useEffect(() => {
    if (quoteVersionId && initialStatus !== 'pending') {
      handleValidate();
    }
  }, [quoteVersionId]);

  const statusConfig = STATUS_CONFIG[status] || STATUS_CONFIG.pending;
  const StatusIcon = statusConfig.icon;

  return (
    <div
      className={cn(
        'rounded-lg border p-4',
        statusConfig.bgColor,
        statusConfig.borderColor,
        className
      )}
    >
      {/* 标题栏 */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <StatusIcon className={cn('h-5 w-5', statusConfig.color)} />
          <span className={cn('font-medium', statusConfig.color)}>
            {statusConfig.label}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleValidate}
            disabled={loading || !quoteVersionId}
            className={cn(
              'flex items-center gap-1 px-3 py-1.5 text-sm rounded-md',
              'bg-slate-700 hover:bg-slate-600 disabled:opacity-50',
              'transition-colors'
            )}
          >
            <RefreshCw className={cn('h-4 w-4', loading && 'animate-spin')} />
            验证
          </button>
          {status !== 'pending' && (
            <button
              onClick={handleSyncCost}
              disabled={syncing || !quoteVersionId}
              className={cn(
                'flex items-center gap-1 px-3 py-1.5 text-sm rounded-md',
                'bg-blue-600 hover:bg-blue-500 disabled:opacity-50',
                'transition-colors'
              )}
            >
              <RefreshCw className={cn('h-4 w-4', syncing && 'animate-spin')} />
              同步成本
            </button>
          )}
        </div>
      </div>

      {/* 验证时间 */}
      {validation?.validated_at && (
        <p className="text-xs text-slate-400 mb-3">
          上次验证: {formatDate(validation.validated_at)}
        </p>
      )}

      {/* 问题列表 */}
      {validation?.issues?.length > 0 && (
        <div className="space-y-2">
          <p className="text-sm text-slate-300 font-medium">发现的问题:</p>
          {validation.issues.map((issue, index) => {
            const levelConfig = ISSUE_LEVEL_CONFIG[issue.level] || ISSUE_LEVEL_CONFIG.info;
            const LevelIcon = levelConfig.icon;

            return (
              <div
                key={index}
                className={cn(
                  'flex items-start gap-2 p-2 rounded-md',
                  levelConfig.bgColor
                )}
              >
                <LevelIcon className={cn('h-4 w-4 mt-0.5 shrink-0', levelConfig.color)} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-slate-200">{issue.message}</p>
                  {issue.details && (
                    <p className="text-xs text-slate-400 mt-1">
                      {typeof issue.details === 'string'
                        ? issue.details
                        : JSON.stringify(issue.details)}
                    </p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* 无问题时显示 */}
      {validation && validation.issues?.length === 0 && (
        <div className="flex items-center gap-2 text-green-400">
          <CheckCircle2 className="h-4 w-4" />
          <span className="text-sm">所有绑定验证通过</span>
        </div>
      )}

      {/* 未绑定提示 */}
      {status === 'pending' && !validation && (
        <p className="text-sm text-slate-400">
          报价版本尚未绑定方案和成本，请先完成绑定
        </p>
      )}
    </div>
  );
}

export default BindingValidationCard;
