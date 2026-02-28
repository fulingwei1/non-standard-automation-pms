/**
 * Quote List Manager Component
 * 报价列表管理组件 - 支持列表和卡片视图
 */

import { useMemo, useCallback } from "react";
import { motion } from "framer-motion";
import {
  Search,
  Plus,
  Eye,
  Edit,
  Copy,
  User,
  AlertTriangle,
  XCircle,
  Download,
  Upload } from
"lucide-react";
import { Card, CardContent } from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Badge } from "../../components/ui/badge";
import { Input } from "../../components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../../components/ui/select";
import { cn } from "../../lib/utils";
import {
  quoteStatusConfig,
  getQuoteStatusConfig,
  getQuotePriorityConfig,
  getQuoteTypeConfig,
  isQuoteExpired,
  isQuoteExpiringSoon,
  formatQuoteNumber,
  formatCurrency,
  QUOTE_SORT_OPTIONS } from
"@/lib/constants/quote";

export const QuoteListManager = ({
  quotes = [],
  opportunities: _opportunities = [],
  customers: _customers = [],
  viewMode = "list",
  searchTerm = "",
  onSearchChange = null,
  filters = {},
  onFilterChange = null,
  sortBy = "created_desc",
  onSortChange = null,
  selectedQuotes = [],
  onSelectionChange = null,
  onQuoteView = null,
  onQuoteEdit = null,
  onQuoteCreate = null,
  onQuoteCopy = null,
  onQuoteSend: _onQuoteSend = null,
  onQuoteApprove: _onQuoteApprove = null,
  onQuoteReject: _onQuoteReject = null,
  onExport = null,
  onImport = null,
  loading = false,
  className = ""
}) => {
  // 确保 quotes 是数组
  const safeQuotes = Array.isArray(quotes) ? quotes : [];

  // 过滤后的 quotes
  const filteredQuotes = useMemo(() => {
    return safeQuotes.filter((quote) => {
      // 搜索过滤
      if (searchTerm) {
        const searchLower = searchTerm.toLowerCase();
        const matchesSearch =
        quote.title?.toLowerCase().includes(searchLower) ||
        quote.id?.toLowerCase().includes(searchLower) ||
        quote.customer_name?.toLowerCase().includes(searchLower) ||
        quote.opportunity_title?.toLowerCase().includes(searchLower);
        if (!matchesSearch) {return false;}
      }

      // 状态过滤
      if (filters.status && filters.status !== 'all' && quote.status !== filters.status) {
        return false;
      }

      // 类型过滤
      if (filters.type && filters.type !== 'all' && quote.type !== filters.type) {
        return false;
      }

      // 优先级过滤
      if (filters.priority && filters.priority !== 'all' && quote.priority !== filters.priority) {
        return false;
      }

      // 客户过滤
      if (filters.customer_id && filters.customer_id !== 'all' && quote.customer_id !== filters.customer_id) {
        return false;
      }

      // 商机过滤
      if (filters.opportunity_id && filters.opportunity_id !== 'all' && quote.opportunity_id !== filters.opportunity_id) {
        return false;
      }

      // 金额范围过滤
      if (filters.min_amount && (!quote.version?.total_price || parseFloat(quote.version.total_price) < parseFloat(filters.min_amount))) {
        return false;
      }
      if (filters.max_amount && (!quote.version?.total_price || parseFloat(quote.version.total_price) > parseFloat(filters.max_amount))) {
        return false;
      }

      // 日期范围过滤
      if (filters.start_date && new Date(quote.created_at) < new Date(filters.start_date)) {
        return false;
      }
      if (filters.end_date && new Date(quote.created_at) > new Date(filters.end_date)) {
        return false;
      }

      return true;
    });
  }, [safeQuotes, searchTerm, filters]);

  // 排序后的 quotes
  const sortedQuotes = useMemo(() => {
    const sorted = [...filteredQuotes];

    switch (sortBy) {
      case 'created_desc':
        return sorted.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
      case 'created_asc':
        return sorted.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
      case 'updated_desc':
        return sorted.sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at));
      case 'updated_asc':
        return sorted.sort((a, b) => new Date(a.updated_at) - new Date(b.updated_at));
      case 'amount_desc':
        return sorted.sort((a, b) => {
          const amountA = parseFloat(a.version?.total_price) || 0;
          const amountB = parseFloat(b.version?.total_price) || 0;
          return amountB - amountA;
        });
      case 'amount_asc':
        return sorted.sort((a, b) => {
          const amountA = parseFloat(a.version?.total_price) || 0;
          const amountB = parseFloat(b.version?.total_price) || 0;
          return amountA - amountB;
        });
      case 'valid_until_asc':
        return sorted.sort((a, b) => {
          if (!a.valid_until) {return 1;}
          if (!b.valid_until) {return -1;}
          return new Date(a.valid_until) - new Date(b.valid_until);
        });
      case 'valid_until_desc':
        return sorted.sort((a, b) => {
          if (!a.valid_until) {return -1;}
          if (!b.valid_until) {return 1;}
          return new Date(b.valid_until) - new Date(a.valid_until);
        });
      case 'title_asc':
        return sorted.sort((a, b) => (a.title || '').localeCompare(b.title || ''));
      case 'title_desc':
        return sorted.sort((a, b) => (b.title || '').localeCompare(a.title || ''));
      default:
        return sorted;
    }
  }, [filteredQuotes, sortBy]);

  // 处理选择
  const handleSelectionChange = useCallback((quoteId, selected) => {
    if (!onSelectionChange) {return;}

    let newSelection;
    if (selected) {
      newSelection = [...selectedQuotes, quoteId];
    } else {
      newSelection = selectedQuotes.filter((id) => id !== quoteId);
    }
    onSelectionChange(newSelection);
  }, [selectedQuotes, onSelectionChange]);

  // 处理全选
  const handleSelectAll = useCallback((selected) => {
    if (!onSelectionChange) {return;}
    onSelectionChange(selected ? sortedQuotes.map((quote) => quote.id) : []);
  }, [sortedQuotes, onSelectionChange]);

  // 渲染状态徽章
  const renderStatusBadge = (status) => {
    const config = getQuoteStatusConfig(status);
    return (
      <Badge variant="outline" className={config.color}>
        <config.icon className="w-3 h-3 mr-1" />
        {config.label}
      </Badge>);

  };

  // 渲染优先级徽章
  const renderPriorityBadge = (priority) => {
    const config = getQuotePriorityConfig(priority);
    return (
      <Badge variant="outline" className={config.color}>
        {config.label}
      </Badge>);

  };

  // 渲染类型徽章
  const renderTypeBadge = (type) => {
    const config = getQuoteTypeConfig(type);
    return (
      <Badge variant="outline" className={config.color}>
        {config.label}
      </Badge>);

  };

  // 渲染警告指示器
  const renderWarnings = (quote) => {
    const warnings = [];

    if (isQuoteExpired(quote)) {
      warnings.push({ icon: XCircle, color: "text-red-400", tooltip: "已过期" });
    }

    if (isQuoteExpiringSoon(quote)) {
      warnings.push({ icon: AlertTriangle, color: "text-amber-400", tooltip: "即将过期" });
    }

    return warnings;
  };

  // 渲染报价卡片（卡片视图）
  const renderQuoteCard = (quote, index) => {
    const warnings = renderWarnings(quote);
    const isSelected = selectedQuotes.includes(quote.id);
    const _statusConfig = getQuoteStatusConfig(quote.status);

    return (
      <motion.div
        key={quote.id}
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: index * 0.05 }}
        whileHover={{ scale: 1.02 }}
        className={cn(
          "bg-slate-800/60 border border-slate-700/60 rounded-lg p-4 cursor-pointer hover:border-slate-600/60 transition-all",
          isSelected && "bg-slate-800/80 border-blue-500/60"
        )}
        onClick={() => onQuoteView?.(quote)}>

        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={isSelected}
              onChange={(e) => {
                e.stopPropagation();
                handleSelectionChange(quote.id, e.target.checked);
              }}
              className="rounded border-slate-600 bg-slate-700 text-blue-500 focus:ring-blue-500" />

            <div className="flex items-center gap-1">
              {warnings.map((warning, idx) => {
                const Icon = warning.icon;
                return (
                  <Icon
                    key={idx}
                    className={cn("w-4 h-4", warning.color)}
                    title={warning.tooltip} />);


              })}
            </div>
          </div>
          <div className="flex items-center gap-2">
            {renderStatusBadge(quote.status)}
          </div>
        </div>
        
        <div className="space-y-2">
          <div>
            <h4 className="text-sm font-medium text-white mb-1">
              {quote.title}
            </h4>
            <p className="text-xs text-slate-400">
              {formatQuoteNumber(quote.id)}
            </p>
          </div>
          
          <div className="flex items-center gap-2">
            {renderTypeBadge(quote.type)}
            {renderPriorityBadge(quote.priority)}
          </div>
          
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div>
              <span className="text-slate-500">客户:</span>
              <span className="text-white ml-1">{quote.customer_name || '-'}</span>
            </div>
            <div>
              <span className="text-slate-500">金额:</span>
              <span className="text-emerald-400 ml-1">
                {formatCurrency(quote.version?.total_price || 0)}
              </span>
            </div>
            <div>
              <span className="text-slate-500">创建:</span>
              <span className="text-white ml-1">
                {quote.created_at ? new Date(quote.created_at).toLocaleDateString() : '-'}
              </span>
            </div>
            <div>
              <span className="text-slate-500">有效期:</span>
              <span className="text-white ml-1">
                {quote.valid_until ? new Date(quote.valid_until).toLocaleDateString() : '-'}
              </span>
            </div>
          </div>
        </div>
        
        <div className="flex justify-between items-center mt-3 pt-3 border-t border-slate-700/40">
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <User className="w-3 h-3" />
            <span>{quote.created_by_name || '未知'}</span>
          </div>
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                onQuoteView?.(quote);
              }}
              className="h-6 w-6 p-0 text-slate-400 hover:text-white">

              <Eye className="w-3 h-3" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                onQuoteEdit?.(quote);
              }}
              className="h-6 w-6 p-0 text-slate-400 hover:text-white">

              <Edit className="w-3 h-3" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                onQuoteCopy?.(quote);
              }}
              className="h-6 w-6 p-0 text-slate-400 hover:text-white">

              <Copy className="w-3 h-3" />
            </Button>
          </div>
        </div>
      </motion.div>);

  };

  // 渲染表格行（列表视图）
  const renderTableRow = (quote, index) => {
    const isSelected = selectedQuotes.includes(quote.id);
    const warnings = renderWarnings(quote);

    return (
      <motion.tr
        key={quote.id}
        initial={{ opacity: 0, x: -10 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: index * 0.02 }}
        className={cn(
          "border-b border-slate-700/40 hover:bg-slate-800/40 transition-colors",
          isSelected && "bg-slate-800/60"
        )}>

        <td className="px-3 py-3">
          <input
            type="checkbox"
            checked={isSelected}
            onChange={(e) => handleSelectionChange(quote.id, e.target.checked)}
            className="rounded border-slate-600 bg-slate-700 text-blue-500 focus:ring-blue-500" />

        </td>
        
        <td className="px-3 py-3">
          <div className="flex items-center gap-2">
            <span className="text-sm text-white font-mono">
              {formatQuoteNumber(quote.id)}
            </span>
            <div className="flex items-center gap-1">
              {warnings.map((warning, idx) => {
                const Icon = warning.icon;
                return (
                  <Icon
                    key={idx}
                    className={cn("w-4 h-4", warning.color)}
                    title={warning.tooltip} />);


              })}
            </div>
          </div>
        </td>
        
        <td className="px-3 py-3">
          <div className="max-w-xs">
            <p className="text-sm text-white font-medium line-clamp-1">
              {quote.title}
            </p>
          </div>
        </td>
        
        <td className="px-3 py-3">
          {renderStatusBadge(quote.status)}
        </td>
        
        <td className="px-3 py-3">
          {renderTypeBadge(quote.type)}
        </td>
        
        <td className="px-3 py-3">
          {renderPriorityBadge(quote.priority)}
        </td>
        
        <td className="px-3 py-3">
          <div className="text-sm text-emerald-400 font-medium">
            {formatCurrency(quote.version?.total_price || 0)}
          </div>
        </td>
        
        <td className="px-3 py-3">
          <div className="max-w-xs">
            <p className="text-sm text-white line-clamp-1">
              {quote.customer_name || '-'}
            </p>
          </div>
        </td>
        
        <td className="px-3 py-3">
          <div className="text-sm text-white">
            {quote.valid_until ? new Date(quote.valid_until).toLocaleDateString() : '-'}
          </div>
        </td>
        
        <td className="px-3 py-3">
          <div className="text-sm text-white">
            {quote.created_at ? new Date(quote.created_at).toLocaleDateString() : '-'}
          </div>
        </td>
        
        <td className="px-3 py-3">
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                onQuoteView?.(quote);
              }}
              className="h-8 w-8 p-0 text-slate-400 hover:text-white">

              <Eye className="w-4 h-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                onQuoteEdit?.(quote);
              }}
              className="h-8 w-8 p-0 text-slate-400 hover:text-white">

              <Edit className="w-4 h-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                onQuoteCopy?.(quote);
              }}
              className="h-8 w-8 p-0 text-slate-400 hover:text-white">

              <Copy className="w-4 h-4" />
            </Button>
          </div>
        </td>
      </motion.tr>);

  };

  return (
    <div className={cn("space-y-4", className)}>
      {/* 搜索和筛选栏 */}
      <Card className="border border-slate-700/70 bg-slate-900/40">
        <CardContent className="p-4">
          <div className="flex flex-col lg:flex-row gap-4">
            {/* 搜索框 */}
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-400" />
              <Input
                placeholder="搜索报价编号、标题、客户..."
                value={searchTerm}
                onChange={(e) => onSearchChange?.(e.target.value)}
                className="pl-10 bg-slate-800/60 border-slate-700 text-white" />

            </div>
            
            {/* 筛选选项 */}
            <div className="flex flex-wrap gap-2">
              <Select
                value={filters.status || "all"}
                onValueChange={(value) => onFilterChange?.({ ...filters, status: value })}>

                <SelectTrigger className="w-32 bg-slate-800/60 border-slate-700 text-white">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部状态</SelectItem>
                  {Object.entries(quoteStatusConfig).map(([key, config]) =>
                  <SelectItem key={key} value={key}>{config.label}</SelectItem>
                  )}
                </SelectContent>
              </Select>

              <Select
                value={filters.type || "all"}
                onValueChange={(value) => onFilterChange?.({ ...filters, type: value })}>

                <SelectTrigger className="w-32 bg-slate-800/60 border-slate-700 text-white">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部类型</SelectItem>
                  <SelectItem value="STANDARD">标准报价</SelectItem>
                  <SelectItem value="CUSTOM">定制报价</SelectItem>
                  <SelectItem value="SERVICE">服务报价</SelectItem>
                  <SelectItem value="PROJECT">项目报价</SelectItem>
                </SelectContent>
              </Select>

              <Select
                value={filters.priority || "all"}
                onValueChange={(value) => onFilterChange?.({ ...filters, priority: value })}>

                <SelectTrigger className="w-32 bg-slate-800/60 border-slate-700 text-white">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部优先级</SelectItem>
                  <SelectItem value="URGENT">紧急</SelectItem>
                  <SelectItem value="HIGH">高</SelectItem>
                  <SelectItem value="MEDIUM">中</SelectItem>
                  <SelectItem value="LOW">低</SelectItem>
                </SelectContent>
              </Select>

              <Select
                value={sortBy}
                onValueChange={onSortChange}>

                <SelectTrigger className="w-40 bg-slate-800/60 border-slate-700 text-white">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {QUOTE_SORT_OPTIONS.map((option) =>
                  <SelectItem key={option.value} value={option.value}>
                      {option.label}
                  </SelectItem>
                  )}
                </SelectContent>
              </Select>
            </div>

            {/* 操作按钮 */}
            <div className="flex gap-2">
              {onImport &&
              <Button variant="outline" size="sm" onClick={onImport}>
                  <Upload className="w-4 h-4 mr-2" />
                  导入
              </Button>
              }
              {onExport &&
              <Button variant="outline" size="sm" onClick={onExport}>
                  <Download className="w-4 h-4 mr-2" />
                  导出
              </Button>
              }
              {onQuoteCreate &&
              <Button onClick={onQuoteCreate} className="bg-blue-600 hover:bg-blue-700">
                  <Plus className="w-4 h-4 mr-2" />
                  新建报价
              </Button>
              }
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 列表视图 */}
      {viewMode === 'list' &&
      <Card className="border border-slate-700/70 bg-slate-900/40">
          <CardContent className="p-0">
            {loading ?
          <div className="text-center py-8 text-slate-400">加载中...</div> :
          sortedQuotes.length === 0 ?
          <div className="text-center py-8 text-slate-400">暂无报价数据</div> :

          <div className="overflow-x-auto">
                <table className="min-w-full">
                  <thead>
                    <tr className="border-b border-slate-700/60">
                      <th className="px-3 py-3 text-left">
                        <input
                      type="checkbox"
                      checked={selectedQuotes.length === sortedQuotes.length}
                      onChange={(e) => handleSelectAll(e.target.checked)}
                      className="rounded border-slate-600 bg-slate-700 text-blue-500 focus:ring-blue-500" />

                      </th>
                      <th className="px-3 py-3 text-left text-xs font-semibold text-slate-400">编号</th>
                      <th className="px-3 py-3 text-left text-xs font-semibold text-slate-400">标题</th>
                      <th className="px-3 py-3 text-left text-xs font-semibold text-slate-400">状态</th>
                      <th className="px-3 py-3 text-left text-xs font-semibold text-slate-400">类型</th>
                      <th className="px-3 py-3 text-left text-xs font-semibold text-slate-400">优先级</th>
                      <th className="px-3 py-3 text-left text-xs font-semibold text-slate-400">金额</th>
                      <th className="px-3 py-3 text-left text-xs font-semibold text-slate-400">客户</th>
                      <th className="px-3 py-3 text-left text-xs font-semibold text-slate-400">有效期</th>
                      <th className="px-3 py-3 text-left text-xs font-semibold text-slate-400">创建时间</th>
                      <th className="px-3 py-3 text-left text-xs font-semibold text-slate-400">操作</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sortedQuotes.map((quote, index) => renderTableRow(quote, index))}
                  </tbody>
                </table>
          </div>
          }
          </CardContent>
      </Card>
      }

      {/* 卡片视图 */}
      {viewMode === 'card' &&
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {loading ?
        <div className="col-span-full text-center py-8 text-slate-400">加载中...</div> :
        sortedQuotes.length === 0 ?
        <div className="col-span-full text-center py-8 text-slate-400">暂无报价数据</div> :

        sortedQuotes.map((quote, index) => renderQuoteCard(quote, index))
        }
      </div>
      }
    </div>);

};

export default QuoteListManager;