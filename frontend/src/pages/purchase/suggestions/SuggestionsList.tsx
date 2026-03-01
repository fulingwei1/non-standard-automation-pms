/**
 * 采购建议列表页
 * @page SuggestionsList
 * @description 显示所有采购建议,支持筛选、批准、创建订单等操作
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Filter, CheckCircle, XCircle, Eye, ShoppingCart, RefreshCw } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../../../components/ui/card';
import { Button } from '../../../components/ui/button';
import { Input } from '../../../components/ui/input';
import { Badge } from '../../../components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../../../components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../../../components/ui/table';
import { useToast } from '../../../hooks/use-toast';
import purchaseService from '../../../services/purchase/purchaseService';
import type { PurchaseSuggestion, SuggestionStatus, UrgencyLevel } from '../../../types/purchase';
import ApprovalDialog from './components/ApprovalDialog';

/**
 * 紧急程度配置
 */
const URGENCY_CONFIG = {
  LOW: { color: 'bg-blue-100 text-blue-800', label: '低' },
  NORMAL: { color: 'bg-gray-100 text-gray-800', label: '普通' },
  HIGH: { color: 'bg-yellow-100 text-yellow-800', label: '高' },
  URGENT: { color: 'bg-red-100 text-red-800', label: '紧急' },
};

/**
 * 状态配置
 */
const STATUS_CONFIG = {
  PENDING: { color: 'bg-yellow-100 text-yellow-800', label: '待审批' },
  APPROVED: { color: 'bg-green-100 text-green-800', label: '已批准' },
  REJECTED: { color: 'bg-red-100 text-red-800', label: '已拒绝' },
  ORDERED: { color: 'bg-blue-100 text-blue-800', label: '已下单' },
};

const SuggestionsList: React.FC = () => {
  const navigate = useNavigate();
  const { toast } = useToast();

  // 状态管理
  const [suggestions, setSuggestions] = useState<PurchaseSuggestion[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedSuggestion, setSelectedSuggestion] = useState<PurchaseSuggestion | null>(null);
  const [showApprovalDialog, setShowApprovalDialog] = useState(false);
  
  // 筛选条件
  const [filters, setFilters] = useState({
    status: '' as SuggestionStatus | '' | '__all__',
    urgency_level: '' as UrgencyLevel | '' | '__all__',
    search: '',
  });

  /**
   * 加载采购建议列表
   */
  const loadSuggestions = async () => {
    setLoading(true);
    try {
      const params: any = {};
      if (filters.status && filters.status !== '__all__') params.status = filters.status;
      if (filters.urgency_level && filters.urgency_level !== '__all__') params.urgency_level = filters.urgency_level;
      
      const data = await purchaseService.getSuggestions(params);
      
      // 应用搜索过滤
      let filtered = data;
      if (filters.search) {
        const searchLower = filters.search.toLowerCase();
        filtered = data.filter(
          (item) =>
            item.suggestion_no.toLowerCase().includes(searchLower) ||
            item.material_code.toLowerCase().includes(searchLower) ||
            item.material_name.toLowerCase().includes(searchLower) ||
            item.suggested_supplier_name.toLowerCase().includes(searchLower)
        );
      }
      
      setSuggestions(filtered);
    } catch (error: any) {
      toast({
        title: '加载失败',
        description: error.response?.data?.detail || '无法加载采购建议列表',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSuggestions();
  }, [filters.status, filters.urgency_level]);

  /**
   * 处理搜索
   */
  const handleSearch = () => {
    loadSuggestions();
  };

  /**
   * 批准建议
   */
  const handleApprove = (suggestion: PurchaseSuggestion) => {
    setSelectedSuggestion(suggestion);
    setShowApprovalDialog(true);
  };

  /**
   * 拒绝建议
   */
  const handleReject = async (suggestion: PurchaseSuggestion) => {
    if (!confirm(`确定要拒绝采购建议 ${suggestion.suggestion_no} 吗？`)) {
      return;
    }

    try {
      await purchaseService.approveSuggestion(suggestion.id, {
        approved: false,
        review_note: '拒绝',
      });

      toast({
        title: '操作成功',
        description: '采购建议已拒绝',
      });

      loadSuggestions();
    } catch (error: any) {
      toast({
        title: '操作失败',
        description: error.response?.data?.detail || '无法拒绝采购建议',
        variant: 'destructive',
      });
    }
  };

  /**
   * 查看详情
   */
  const handleViewDetail = (suggestion: PurchaseSuggestion) => {
    navigate(`/purchase/suggestions/${suggestion.id}`);
  };

  /**
   * 创建订单
   */
  const handleCreateOrder = async (suggestion: PurchaseSuggestion) => {
    if (!confirm(`确定要为建议 ${suggestion.suggestion_no} 创建采购订单吗？`)) {
      return;
    }

    try {
      const result = await purchaseService.createOrderFromSuggestion(suggestion.id, {});

      toast({
        title: '创建成功',
        description: `采购订单 ${result.data.order_no} 已创建`,
      });

      loadSuggestions();
    } catch (error: any) {
      toast({
        title: '创建失败',
        description: error.response?.data?.detail || '无法创建采购订单',
        variant: 'destructive',
      });
    }
  };

  /**
   * 格式化金额
   */
  const formatCurrency = (amount: number) => {
    return `¥${amount.toFixed(2)}`;
  };

  return (
    <div className="container mx-auto p-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-2xl font-bold">采购建议列表</CardTitle>
            <Button onClick={loadSuggestions} disabled={loading}>
              <RefreshCw className={`mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
              刷新
            </Button>
          </div>
        </CardHeader>

        <CardContent>
          {/* 筛选栏 */}
          <div className="mb-6 grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="flex gap-2">
              <Input
                placeholder="搜索建议编号、物料..."
                value={filters.search}
                onChange={(e) => setFilters({ ...filters, search: e.target.value })}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              />
              <Button onClick={handleSearch} size="icon">
                <Search className="h-4 w-4" />
              </Button>
            </div>

            <Select
              value={filters.status === '' ? '__all__' : filters.status}
              onValueChange={(value) => setFilters({ ...filters, status: value === '__all__' ? '' : value as SuggestionStatus })}
            >
              <SelectTrigger>
                <SelectValue placeholder="选择状态" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="__all__">全部状态</SelectItem>
                <SelectItem value="PENDING">待审批</SelectItem>
                <SelectItem value="APPROVED">已批准</SelectItem>
                <SelectItem value="REJECTED">已拒绝</SelectItem>
                <SelectItem value="ORDERED">已下单</SelectItem>
              </SelectContent>
            </Select>

            <Select
              value={filters.urgency_level === '' ? '__all__' : filters.urgency_level}
              onValueChange={(value) => setFilters({ ...filters, urgency_level: value === '__all__' ? '' : value as UrgencyLevel })}
            >
              <SelectTrigger>
                <SelectValue placeholder="紧急程度" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="__all__">全部</SelectItem>
                <SelectItem value="LOW">低</SelectItem>
                <SelectItem value="NORMAL">普通</SelectItem>
                <SelectItem value="HIGH">高</SelectItem>
                <SelectItem value="URGENT">紧急</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* 数据表格 */}
          {loading ? (
            <div className="text-center py-12">
              <RefreshCw className="animate-spin h-8 w-8 mx-auto mb-4 text-gray-400" />
              <p className="text-gray-500">加载中...</p>
            </div>
          ) : suggestions.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-500">暂无数据</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>建议编号</TableHead>
                    <TableHead>物料</TableHead>
                    <TableHead className="text-right">数量</TableHead>
                    <TableHead>紧急程度</TableHead>
                    <TableHead>推荐供应商</TableHead>
                    <TableHead className="text-right">预估金额</TableHead>
                    <TableHead className="text-center">AI置信度</TableHead>
                    <TableHead>状态</TableHead>
                    <TableHead className="text-right">操作</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {suggestions.map((suggestion) => (
                    <TableRow key={suggestion.id}>
                      <TableCell className="font-medium">{suggestion.suggestion_no}</TableCell>
                      <TableCell>
                        <div>
                          <div className="font-medium">{suggestion.material_code}</div>
                          <div className="text-sm text-gray-500">{suggestion.material_name}</div>
                        </div>
                      </TableCell>
                      <TableCell className="text-right">
                        {suggestion.suggested_qty} {suggestion.unit}
                      </TableCell>
                      <TableCell>
                        <Badge className={URGENCY_CONFIG[suggestion.urgency_level].color}>
                          {URGENCY_CONFIG[suggestion.urgency_level].label}
                        </Badge>
                      </TableCell>
                      <TableCell>{suggestion.suggested_supplier_name}</TableCell>
                      <TableCell className="text-right">
                        {formatCurrency(suggestion.estimated_total_amount)}
                      </TableCell>
                      <TableCell className="text-center">
                        <span className={`font-medium ${
                          suggestion.ai_confidence >= 80 ? 'text-green-600' :
                          suggestion.ai_confidence >= 60 ? 'text-yellow-600' :
                          'text-red-600'
                        }`}>
                          {suggestion.ai_confidence.toFixed(1)}%
                        </span>
                      </TableCell>
                      <TableCell>
                        <Badge className={STATUS_CONFIG[suggestion.status].color}>
                          {STATUS_CONFIG[suggestion.status].label}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex gap-2 justify-end">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleViewDetail(suggestion)}
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                          
                          {suggestion.status === 'PENDING' && (
                            <>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleApprove(suggestion)}
                              >
                                <CheckCircle className="h-4 w-4 text-green-600" />
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleReject(suggestion)}
                              >
                                <XCircle className="h-4 w-4 text-red-600" />
                              </Button>
                            </>
                          )}
                          
                          {suggestion.status === 'APPROVED' && (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleCreateOrder(suggestion)}
                            >
                              <ShoppingCart className="h-4 w-4 text-blue-600" />
                            </Button>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* 批准对话框 */}
      {selectedSuggestion && (
        <ApprovalDialog
          open={showApprovalDialog}
          suggestion={selectedSuggestion}
          onClose={() => {
            setShowApprovalDialog(false);
            setSelectedSuggestion(null);
          }}
          onSuccess={() => {
            setShowApprovalDialog(false);
            setSelectedSuggestion(null);
            loadSuggestions();
          }}
        />
      )}
    </div>
  );
};

export default SuggestionsList;
