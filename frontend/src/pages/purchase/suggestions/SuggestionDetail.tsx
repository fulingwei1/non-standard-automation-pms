/**
 * 采购建议详情页
 * @page SuggestionDetail
 * @description 显示采购建议详情，包含 AI 推荐供应商信息
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, CheckCircle, XCircle, ShoppingCart } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../../../components/ui/card';
import { Button } from '../../../components/ui/button';
import { Badge } from '../../../components/ui/badge';
import { useToast } from '../../../hooks/use-toast';
import purchaseService from '../../../services/purchase/purchaseService';
import type { PurchaseSuggestion } from '../../../types/purchase';
import SupplierRecommendation from './components/SupplierRecommendation';
import ApprovalDialog from './components/ApprovalDialog';

const SuggestionDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();

  const [suggestion, setSuggestion] = useState<PurchaseSuggestion | null>(null);
  const [loading, setLoading] = useState(true);
  const [showApprovalDialog, setShowApprovalDialog] = useState(false);

  /**
   * 加载建议详情
   */
  const loadSuggestion = async () => {
    if (!id) return;
    
    setLoading(true);
    try {
      const data = await purchaseService.getSuggestionById(parseInt(id));
      setSuggestion(data);
    } catch (error: any) {
      toast({
        title: '加载失败',
        description: error.response?.data?.detail || '无法加载采购建议详情',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSuggestion();
  }, [id]);

  /**
   * 创建订单
   */
  const handleCreateOrder = async () => {
    if (!suggestion) return;

    if (!confirm(`确定要为建议 ${suggestion.suggestion_no} 创建采购订单吗？`)) {
      return;
    }

    try {
      const result = await purchaseService.createOrderFromSuggestion(suggestion.id, {});

      toast({
        title: '创建成功',
        description: `采购订单 ${result.data.order_no} 已创建`,
      });

      navigate('/purchase/orders');
    } catch (error: any) {
      toast({
        title: '创建失败',
        description: error.response?.data?.detail || '无法创建采购订单',
        variant: 'destructive',
      });
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="text-center py-12">
          <p className="text-gray-500">加载中...</p>
        </div>
      </div>
    );
  }

  if (!suggestion) {
    return (
      <div className="container mx-auto p-6">
        <div className="text-center py-12">
          <p className="text-gray-500">未找到采购建议</p>
          <Button className="mt-4" onClick={() => navigate('/purchase/suggestions')}>
            返回列表
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* 头部 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" onClick={() => navigate('/purchase/suggestions')}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            返回
          </Button>
          <h1 className="text-3xl font-bold">{suggestion.suggestion_no}</h1>
          <Badge
            className={
              suggestion.status === 'PENDING' ? 'bg-yellow-100 text-yellow-800' :
              suggestion.status === 'APPROVED' ? 'bg-green-100 text-green-800' :
              suggestion.status === 'REJECTED' ? 'bg-red-100 text-red-800' :
              'bg-blue-100 text-blue-800'
            }
          >
            {suggestion.status === 'PENDING' ? '待审批' :
             suggestion.status === 'APPROVED' ? '已批准' :
             suggestion.status === 'REJECTED' ? '已拒绝' : '已下单'}
          </Badge>
        </div>

        <div className="flex gap-2">
          {suggestion.status === 'PENDING' && (
            <>
              <Button onClick={() => setShowApprovalDialog(true)}>
                <CheckCircle className="h-4 w-4 mr-2" />
                批准
              </Button>
            </>
          )}
          {suggestion.status === 'APPROVED' && (
            <Button onClick={handleCreateOrder}>
              <ShoppingCart className="h-4 w-4 mr-2" />
              创建订单
            </Button>
          )}
        </div>
      </div>

      {/* 基本信息 */}
      <Card>
        <CardHeader>
          <CardTitle>基本信息</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <div>
              <p className="text-sm text-gray-500">物料编码</p>
              <p className="font-medium">{suggestion.material_code}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">物料名称</p>
              <p className="font-medium">{suggestion.material_name}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">规格</p>
              <p className="font-medium">{suggestion.specification}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">建议采购数量</p>
              <p className="font-medium text-blue-600">
                {suggestion.suggested_qty} {suggestion.unit}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500">当前库存</p>
              <p className="font-medium">{suggestion.current_stock} {suggestion.unit}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">安全库存</p>
              <p className="font-medium">{suggestion.safety_stock} {suggestion.unit}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">紧急程度</p>
              <Badge
                className={
                  suggestion.urgency_level === 'URGENT' ? 'bg-red-100 text-red-800' :
                  suggestion.urgency_level === 'HIGH' ? 'bg-yellow-100 text-yellow-800' :
                  suggestion.urgency_level === 'NORMAL' ? 'bg-gray-100 text-gray-800' :
                  'bg-blue-100 text-blue-800'
                }
              >
                {suggestion.urgency_level === 'URGENT' ? '紧急' :
                 suggestion.urgency_level === 'HIGH' ? '高' :
                 suggestion.urgency_level === 'NORMAL' ? '普通' : '低'}
              </Badge>
            </div>
            <div>
              <p className="text-sm text-gray-500">来源类型</p>
              <p className="font-medium">
                {suggestion.source_type === 'SHORTAGE' ? '缺料' :
                 suggestion.source_type === 'SAFETY_STOCK' ? '安全库存' :
                 suggestion.source_type === 'FORECAST' ? '预测' : '手动'}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500">创建时间</p>
              <p className="font-medium">
                {new Date(suggestion.created_at).toLocaleString('zh-CN')}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 预估成本 */}
      <Card>
        <CardHeader>
          <CardTitle>预估成本</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <p className="text-sm text-gray-500">预估单价</p>
              <p className="text-2xl font-bold">¥{suggestion.estimated_unit_price.toFixed(2)}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">采购数量</p>
              <p className="text-2xl font-bold">{suggestion.suggested_qty} {suggestion.unit}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">预估总额</p>
              <p className="text-2xl font-bold text-blue-600">
                ¥{suggestion.estimated_total_amount.toFixed(2)}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* AI 推荐供应商 */}
      <SupplierRecommendation suggestion={suggestion} />

      {/* 批准对话框 */}
      <ApprovalDialog
        open={showApprovalDialog}
        suggestion={suggestion}
        onClose={() => setShowApprovalDialog(false)}
        onSuccess={() => {
          setShowApprovalDialog(false);
          loadSuggestion();
        }}
      />
    </div>
  );
};

export default SuggestionDetail;
