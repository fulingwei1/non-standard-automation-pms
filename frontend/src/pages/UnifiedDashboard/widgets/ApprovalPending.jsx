/**
 * 待审批组件 (Approval Pending)
 *
 * 显示待处理的审批事项
 */

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  ClipboardCheck,
  Clock,
  ChevronRight,
  FileText,
  DollarSign,
  Users,
  Package,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../../../components/ui/card';
import { Badge } from '../../../components/ui/badge';
import { Button } from '../../../components/ui/button';
import api from '../../../services/api';
import { cn } from '../../../lib/utils';

// 审批类型图标映射
const typeIcons = {
  leave: Users,
  expense: DollarSign,
  purchase: Package,
  contract: FileText,
  project: FileText,
  default: FileText,
};

// 默认审批数据
const defaultApprovals = [
  {
    id: 1,
    type: 'leave',
    title: '张三的请假申请',
    applicant: '张三',
    submitTime: '2小时前',
    urgent: true,
  },
  {
    id: 2,
    type: 'expense',
    title: '出差报销申请 ¥3,500',
    applicant: '李四',
    submitTime: '4小时前',
    urgent: false,
  },
  {
    id: 3,
    type: 'purchase',
    title: '采购订单审批 PO250101',
    applicant: '王五',
    submitTime: '昨天',
    urgent: false,
  },
  {
    id: 4,
    type: 'contract',
    title: '合同审批 - 华为项目',
    applicant: '赵六',
    submitTime: '昨天',
    urgent: true,
  },
];

/**
 * 单个审批项
 */
function ApprovalItem({ approval, index, onClick }) {
  const Icon = typeIcons[approval.type] || typeIcons.default;

  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.05 }}
      onClick={() => onClick?.(approval)}
      className={cn(
        'flex items-start gap-3 p-3 rounded-lg cursor-pointer transition-colors',
        'hover:bg-white/5',
        approval.urgent && 'bg-orange-500/10'
      )}
    >
      {/* 类型图标 */}
      <div className="p-2 rounded-md bg-white/5">
        <Icon className="h-4 w-4 text-slate-400" />
      </div>

      {/* 审批内容 */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <p className="text-sm font-medium truncate">{approval.title}</p>
          {approval.urgent && (
            <Badge variant="destructive" className="text-xs px-1.5 py-0 h-4">
              紧急
            </Badge>
          )}
        </div>
        <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
          <span>申请人：{approval.applicant}</span>
          <span>·</span>
          <span>{approval.submitTime}</span>
        </div>
      </div>

      <ChevronRight className="h-4 w-4 text-slate-500 mt-1" />
    </motion.div>
  );
}

/**
 * 待审批主组件
 */
export default function ApprovalPending({ limit = 5, data }) {
  const navigate = useNavigate();
  const [approvals, setApprovals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [totalCount, setTotalCount] = useState(0);

  useEffect(() => {
    const loadApprovals = async () => {
      setLoading(true);
      try {
        if (data?.approvals) {
          setApprovals(data.approvals.slice(0, limit));
          setTotalCount(data.total || data.approvals?.length);
          return;
        }

        try {
           const response = await api.get('/approvals/pending/mine');
          if (response.data?.items) {
            setApprovals(response.data.items.slice(0, limit));
            setTotalCount(response.data.total || response.data.items?.length);
            return;
          }
        } catch {
          // API 不可用
        }

        setApprovals(defaultApprovals.slice(0, limit));
        setTotalCount(defaultApprovals.length);
      } finally {
        setLoading(false);
      }
    };

    loadApprovals();
  }, [limit, data]);

  const handleApprovalClick = (approval) => {
    navigate(`/approvals/${approval.id}`);
  };

  const handleViewAll = () => {
    navigate('/approvals');
  };

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <ClipboardCheck className="h-4 w-4" />
            待审批
            {totalCount > 0 && (
              <Badge variant="secondary" className="text-xs px-1.5 py-0 h-5">
                {totalCount}
              </Badge>
            )}
          </CardTitle>
          <Button variant="ghost" size="sm" onClick={handleViewAll}>
            查看全部
            <ChevronRight className="h-4 w-4 ml-1" />
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="space-y-2">
            {[...Array(limit)].map((_, i) => (
              <div key={i} className="h-14 bg-white/5 rounded-lg animate-pulse" />
            ))}
          </div>
        ) : approvals.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
            <ClipboardCheck className="h-8 w-8 mb-2" />
            <p className="text-sm">暂无待审批事项</p>
          </div>
        ) : (
          <div className="space-y-1">
            {(approvals || []).map((approval, index) => (
              <ApprovalItem
                key={approval.id}
                approval={approval}
                index={index}
                onClick={handleApprovalClick}
              />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
