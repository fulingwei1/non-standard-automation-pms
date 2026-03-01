import React, { useMemo } from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent } from "../ui/card";
import { Input } from "../ui/input";
import { Badge } from "../ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../ui/select";
import { History, FileText } from 'lucide-react';

const fadeIn = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5 } }
};

/**
 * 日志类型配置
 */
const logTypeConfigs = {
  STATUS_CHANGE: { label: '状态变更', color: 'bg-blue-500' },
  APPROVAL: { label: '审批', color: 'bg-green-500' },
  EVALUATION: { label: '评估', color: 'bg-purple-500' },
  OPERATION: { label: '操作', color: 'bg-slate-500' },
  COMMENT: { label: '评论', color: 'bg-amber-500' }
};

/**
 * 日志项组件
 */
const LogItem = ({ log, formatDate }) => {
  const typeConfig = logTypeConfigs[log.log_type] || logTypeConfigs.OPERATION;

  return (
    <div className="relative flex items-start gap-4">
      {/* 时间线节点 */}
      <div className="relative z-10">
        <div className="w-10 h-10 rounded-full bg-blue-500 flex items-center justify-center text-white shadow-lg">
          <History className="w-5 h-5" />
        </div>
      </div>

      {/* 日志卡片 */}
      <Card className="flex-1 shadow-sm hover:shadow-md transition-shadow">
        <CardContent className="pt-4">
          <div className="flex justify-between items-start mb-2">
            <div>
              <div className="font-semibold text-slate-800">
                {log.log_action}
              </div>
              <div className="text-sm text-slate-500">
                {log.created_by_name || `用户${log.created_by || ""}`} · {formatDate(log.created_at)}
              </div>
            </div>
            <Badge className={typeConfig.color}>{typeConfig.label}</Badge>
          </div>
          
          {/* 状态变更 */}
          {log.old_status && log.new_status && (
            <div className="text-sm text-slate-600 mb-2 flex items-center gap-2">
              <span className="text-slate-500">状态变更:</span>
              <span className="px-2 py-0.5 bg-slate-100 rounded font-mono text-xs">
                {log.old_status}
              </span>
              <span className="text-slate-400">→</span>
              <span className="px-2 py-0.5 bg-blue-100 rounded font-mono text-xs">
                {log.new_status}
              </span>
            </div>
          )}
          
          {/* 日志内容 */}
          {log.log_content && (
            <div className="p-3 bg-slate-50 rounded text-sm text-slate-700 border border-slate-100">
              {log.log_content}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

/**
 * 变更日志标签页组件
 * 
 * @param {Object} props
 * @param {Array} props.logs - 日志列表
 * @param {string} props.searchKeyword - 搜索关键词
 * @param {string} props.filterType - 筛选类型
 * @param {Function} props.onSearchChange - 搜索变化回调
 * @param {Function} props.onFilterChange - 筛选变化回调
 * @param {Function} props.formatDate - 日期格式化函数
 */
export const ECNLogsTab = ({
  logs = [],
  searchKeyword = '',
  filterType = 'all',
  onSearchChange,
  onFilterChange,
  formatDate = (date) => new Date(date).toLocaleString()
}) => {
  // 过滤日志
  const filteredLogs = useMemo(() => {
    let result = [...logs];

    // 按类型筛选
    if (filterType && filterType !== 'all') {
      result = (result || []).filter(log => log.log_type === filterType);
    }

    // 按关键词搜索
    if (searchKeyword) {
      const keyword = searchKeyword.toLowerCase();
      result = (result || []).filter(log => 
        log.log_action?.toLowerCase().includes(keyword) ||
        log.log_content?.toLowerCase().includes(keyword) ||
        log.created_by_name?.toLowerCase().includes(keyword)
      );
    }

    return result;
  }, [logs, searchKeyword, filterType]);

  return (
    <motion.div
      variants={fadeIn}
      initial="hidden"
      animate="visible"
      className="space-y-4"
    >
      {/* 日志筛选 */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <Input
                placeholder="搜索日志内容..."
                value={searchKeyword || "unknown"}
                onChange={(e) => onSearchChange?.(e.target.value)}
                className="max-w-sm"
              />
            </div>
            <Select value={filterType || "unknown"} onValueChange={onFilterChange}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="日志类型" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部类型</SelectItem>
                <SelectItem value="STATUS_CHANGE">状态变更</SelectItem>
                <SelectItem value="APPROVAL">审批</SelectItem>
                <SelectItem value="EVALUATION">评估</SelectItem>
                <SelectItem value="OPERATION">操作</SelectItem>
                <SelectItem value="COMMENT">评论</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* 日志列表 */}
      {filteredLogs.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <FileText className="w-12 h-12 text-slate-400 mx-auto mb-4" />
            <p className="text-slate-500 mb-1">
              {logs.length === 0 ? "暂无变更日志" : "没有匹配的日志"}
            </p>
            {searchKeyword || filterType !== 'all' ? (
              <p className="text-sm text-slate-400">
                尝试调整筛选条件或清空搜索
              </p>
            ) : null}
          </CardContent>
        </Card>
      ) : (
        <div className="relative">
          {/* 时间线背景 */}
          <div className="absolute left-5 top-0 bottom-0 w-0.5 bg-slate-200" />

          {/* 日志列表 */}
          <div className="space-y-4">
            {(filteredLogs || []).map((log) => (
              <LogItem key={log.id} log={log} formatDate={formatDate} />
            ))}
          </div>
        </div>
      )}

      {/* 统计信息 */}
      {filteredLogs.length > 0 && (
        <div className="text-center text-sm text-slate-500 pt-4 border-t">
          显示 {filteredLogs.length} 条日志
          {logs.length !== filteredLogs.length && ` (共 ${logs.length} 条)`}
        </div>
      )}
    </motion.div>
  );
};

export default ECNLogsTab;
