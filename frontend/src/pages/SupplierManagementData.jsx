import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  Plus,
  Search,
  Edit3,
  Trash2,
  Eye,
  Building2,
  Phone,
  Mail,
  MapPin,
  Star,
  Award,
  Package,
} from 'lucide-react';
import { PageHeader } from '../components/layout';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '../components/ui/dialog';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { cn } from '../lib/utils';
import { fadeIn, staggerContainer } from '../lib/animations';
import { supplierApi } from '../services/api';

export default function SupplierManagementData() {
  const [suppliers, setSuppliers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [showRatingDialog, setShowRatingDialog] = useState(false);
  const [selectedSupplier, setSelectedSupplier] = useState(null);
  const [searchKeyword, setSearchKeyword] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');
  const [filterLevel, setFilterLevel] = useState('all');
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [total, setTotal] = useState(0);

  const [newSupplier, setNewSupplier] = useState({
    supplier_code: '',
    supplier_name: '',
    supplier_short_name: '',
    supplier_type: 'MATERIAL',
    contact_person: '',
    contact_phone: '',
    contact_email: '',
    address: '',
    bank_name: '',
    bank_account: '',
    tax_number: '',
    payment_terms: '',
    remark: '',
  });

  const [editSupplier, setEditSupplier] = useState(null);
  const [ratingData, setRatingData] = useState({
    quality_rating: 0,
    delivery_rating: 0,
    service_rating: 0,
  });

  // 加载供应商列表
  const loadSuppliers = async () => {
    setLoading(true);
    try {
      const params = {
        page,
        page_size: pageSize,
      };
      if (searchKeyword) {
        params.keyword = searchKeyword;
      }
      if (filterType !== 'all') {
        params.supplier_type = filterType;
      }
      if (filterStatus !== 'all') {
        params.status = filterStatus;
      }
      if (filterLevel !== 'all') {
        params.supplier_level = filterLevel;
      }

      const response = await supplierApi.list(params);
      const data = response.data;
      setSuppliers(data.items || []);
      setTotal(data.total || 0);
    } catch (error) {
      console.error('加载供应商列表失败:', error);
      alert('加载供应商列表失败: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSuppliers();
  }, [page, searchKeyword, filterType, filterStatus, filterLevel]);

  const handleCreateChange = (e) => {
    const { name, value } = e.target;
    setNewSupplier((prev) => ({ ...prev, [name]: value }));
  };

  const handleEditChange = (e) => {
    const { name, value } = e.target;
    setEditSupplier((prev) => ({ ...prev, [name]: value }));
  };

  const handleCreateSubmit = async () => {
    try {
      await supplierApi.create(newSupplier);
      setShowCreateDialog(false);
      setNewSupplier({
        supplier_code: '',
        supplier_name: '',
        supplier_short_name: '',
        supplier_type: 'MATERIAL',
        contact_person: '',
        contact_phone: '',
        contact_email: '',
        address: '',
        bank_name: '',
        bank_account: '',
        tax_number: '',
        payment_terms: '',
        remark: '',
      });
      loadSuppliers();
    } catch (error) {
      alert('创建供应商失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleEditSubmit = async () => {
    try {
      await supplierApi.update(editSupplier.id, editSupplier);
      setShowEditDialog(false);
      setEditSupplier(null);
      loadSuppliers();
    } catch (error) {
      alert('更新供应商失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleRatingSubmit = async () => {
    try {
      const params = {};
      if (ratingData.quality_rating > 0) params.quality_rating = ratingData.quality_rating;
      if (ratingData.delivery_rating > 0) params.delivery_rating = ratingData.delivery_rating;
      if (ratingData.service_rating > 0) params.service_rating = ratingData.service_rating;
      
      await supplierApi.updateRating(selectedSupplier.id, params);
      setShowRatingDialog(false);
      loadSuppliers();
    } catch (error) {
      alert('更新评级失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleViewDetail = async (id) => {
    try {
      const response = await supplierApi.get(id);
      setSelectedSupplier(response.data);
      setShowDetailDialog(true);
    } catch (error) {
      alert('获取供应商详情失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleEdit = async (id) => {
    try {
      const response = await supplierApi.get(id);
      setEditSupplier(response.data);
      setShowEditDialog(true);
    } catch (error) {
      alert('获取供应商信息失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleRating = async (id) => {
    try {
      const response = await supplierApi.get(id);
      setSelectedSupplier(response.data);
      setRatingData({
        quality_rating: parseFloat(response.data.quality_rating) || 0,
        delivery_rating: parseFloat(response.data.delivery_rating) || 0,
        service_rating: parseFloat(response.data.service_rating) || 0,
      });
      setShowRatingDialog(true);
    } catch (error) {
      alert('获取供应商信息失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  const getLevelColor = (level) => {
    switch (level) {
      case 'A': return 'bg-green-500';
      case 'B': return 'bg-blue-500';
      case 'C': return 'bg-yellow-500';
      case 'D': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const isDemoAccount = localStorage.getItem('token')?.startsWith('demo_token_')

  // Mock data for demo accounts
  useEffect(() => {
    if (isDemoAccount && suppliers.length === 0 && !loading) {
      setSuppliers([
        {
          id: 1,
          supplier_code: 'V00015',
          supplier_name: '欧姆龙(上海)代理',
          supplier_short_name: '欧姆龙',
          supplier_type: 'MATERIAL',
          contact_person: '张经理',
          contact_phone: '021-12345678',
          contact_email: 'zhang@omron.com',
          address: '上海市浦东新区',
          overall_rating: 4.8,
          supplier_level: 'A',
          status: 'ACTIVE',
        },
        {
          id: 2,
          supplier_code: 'V00023',
          supplier_name: 'THK(深圳)销售',
          supplier_short_name: 'THK',
          supplier_type: 'MATERIAL',
          contact_person: '李经理',
          contact_phone: '0755-87654321',
          contact_email: 'li@thk.com',
          address: '深圳市南山区',
          overall_rating: 4.6,
          supplier_level: 'A',
          status: 'ACTIVE',
        },
      ])
      setTotal(2)
    }
  }, [isDemoAccount])

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="container mx-auto px-4 py-6 space-y-6">
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      <PageHeader
        title="供应商管理"
        description="管理系统供应商信息，包括创建、编辑、评级等操作。"
        actions={
          <Button onClick={() => setShowCreateDialog(true)}>
            <Plus className="mr-2 h-4 w-4" /> 新增供应商
          </Button>
        }
      />

      <motion.div variants={fadeIn}>
        <Card className="bg-slate-800/50 border-slate-700/50">
          <CardHeader className="flex-row items-center justify-between">
            <CardTitle className="text-slate-200">供应商列表</CardTitle>
            <div className="flex items-center space-x-2">
              <Input
                placeholder="搜索供应商名称/编码..."
                value={searchKeyword}
                onChange={(e) => setSearchKeyword(e.target.value)}
                className="max-w-sm bg-slate-900/50 border-slate-700 text-slate-200"
                icon={Search}
              />
              <Select value={filterType} onValueChange={setFilterType}>
                <SelectTrigger className="w-[150px] bg-slate-900/50 border-slate-700">
                  <SelectValue placeholder="供应商类型" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">所有类型</SelectItem>
                  <SelectItem value="MATERIAL">物料供应商</SelectItem>
                  <SelectItem value="OUTSOURCE">外协供应商</SelectItem>
                  <SelectItem value="BOTH">两者兼有</SelectItem>
                </SelectContent>
              </Select>
              <Select value={filterStatus} onValueChange={setFilterStatus}>
                <SelectTrigger className="w-[150px] bg-slate-900/50 border-slate-700">
                  <SelectValue placeholder="状态" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">所有状态</SelectItem>
                  <SelectItem value="ACTIVE">合作中</SelectItem>
                  <SelectItem value="SUSPENDED">暂停</SelectItem>
                  <SelectItem value="BLACKLIST">黑名单</SelectItem>
                </SelectContent>
              </Select>
              <Select value={filterLevel} onValueChange={setFilterLevel}>
                <SelectTrigger className="w-[120px] bg-slate-900/50 border-slate-700">
                  <SelectValue placeholder="等级" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">所有等级</SelectItem>
                  <SelectItem value="A">A级</SelectItem>
                  <SelectItem value="B">B级</SelectItem>
                  <SelectItem value="C">C级</SelectItem>
                  <SelectItem value="D">D级</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="p-4 text-center text-slate-400">加载中...</div>
            ) : (
              <>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-border">
                    <thead>
                      <tr className="bg-slate-900/50 border-b border-slate-700">
                        <th className="px-4 py-2 text-left text-sm font-semibold text-slate-400">供应商编码</th>
                        <th className="px-4 py-2 text-left text-sm font-semibold text-slate-400">供应商名称</th>
                        <th className="px-4 py-2 text-left text-sm font-semibold text-slate-400">类型</th>
                        <th className="px-4 py-2 text-left text-sm font-semibold text-slate-400">联系人</th>
                        <th className="px-4 py-2 text-left text-sm font-semibold text-slate-400">综合评分</th>
                        <th className="px-4 py-2 text-left text-sm font-semibold text-slate-400">等级</th>
                        <th className="px-4 py-2 text-left text-sm font-semibold text-slate-400">状态</th>
                        <th className="px-4 py-2 text-left text-sm font-semibold text-slate-400">操作</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-700">
                      {suppliers.map((supplier) => (
                        <tr key={supplier.id} className="hover:bg-slate-800/30">
                          <td className="px-4 py-2 text-sm text-slate-200 font-mono">{supplier.supplier_code}</td>
                          <td className="px-4 py-2 text-sm text-slate-200">{supplier.supplier_name}</td>
                          <td className="px-4 py-2 text-sm text-slate-400">{supplier.supplier_type || '-'}</td>
                          <td className="px-4 py-2 text-sm text-slate-300">
                            <div>{supplier.contact_person || '-'}</div>
                            {supplier.contact_phone && (
                              <div className="text-xs text-slate-500">{supplier.contact_phone}</div>
                            )}
                          </td>
                          <td className="px-4 py-2 text-sm">
                            {supplier.overall_rating ? (
                              <div className="flex items-center space-x-1">
                                <Star className="h-4 w-4 text-yellow-500 fill-yellow-500" />
                                <span className="text-slate-200">{parseFloat(supplier.overall_rating).toFixed(1)}</span>
                              </div>
                            ) : (
                              <span className="text-slate-500">-</span>
                            )}
                          </td>
                          <td className="px-4 py-2 text-sm">
                            {supplier.supplier_level && (
                              <Badge className={cn("text-white", getLevelColor(supplier.supplier_level))}>
                                {supplier.supplier_level}级
                              </Badge>
                            )}
                          </td>
                          <td className="px-4 py-2 text-sm">
                            <Badge className={
                              supplier.status === 'ACTIVE' ? 'bg-emerald-500' :
                              supplier.status === 'SUSPENDED' ? 'bg-amber-500' :
                              'bg-red-500'
                            }>
                              {supplier.status === 'ACTIVE' ? '合作中' : supplier.status === 'SUSPENDED' ? '暂停' : '黑名单'}
                            </Badge>
                          </td>
                          <td className="px-4 py-2 text-sm">
                            <div className="flex items-center space-x-2">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleViewDetail(supplier.id)}
                                className="text-slate-400 hover:text-slate-200"
                              >
                                <Eye className="h-4 w-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleEdit(supplier.id)}
                                className="text-slate-400 hover:text-slate-200"
                              >
                                <Edit3 className="h-4 w-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleRating(supplier.id)}
                                title="评级"
                                className="text-slate-400 hover:text-slate-200"
                              >
                                <Award className="h-4 w-4" />
                              </Button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {suppliers.length === 0 && (
                  <p className="p-4 text-center text-slate-400">
                    没有找到符合条件的供应商。
                  </p>
                )}
                {total > pageSize && (
                  <div className="mt-4 flex items-center justify-between">
                    <div className="text-sm text-slate-400">
                      共 {total} 条记录，第 {page} / {Math.ceil(total / pageSize)} 页
                    </div>
                    <div className="flex space-x-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setPage(p => Math.max(1, p - 1))}
                        disabled={page === 1}
                      >
                        上一页
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setPage(p => Math.min(Math.ceil(total / pageSize), p + 1))}
                        disabled={page >= Math.ceil(total / pageSize)}
                      >
                        下一页
                      </Button>
                    </div>
                  </div>
                )}
              </>
            )}
          </CardContent>
        </Card>
      </motion.div>

      {/* Create Dialog - 简化版，只包含关键字段 */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="sm:max-w-[600px] bg-slate-900 border-slate-700">
          <DialogHeader>
            <DialogTitle className="text-slate-200">新增供应商</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="create-supplier-code" className="text-right text-slate-400">供应商编码 *</Label>
              <Input
                id="create-supplier-code"
                name="supplier_code"
                value={newSupplier.supplier_code}
                onChange={handleCreateChange}
                className="col-span-3 bg-slate-800 border-slate-700 text-slate-200"
                required
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="create-supplier-name" className="text-right">供应商名称 *</Label>
              <Input
                id="create-supplier-name"
                name="supplier_name"
                value={newSupplier.supplier_name}
                onChange={handleCreateChange}
                className="col-span-3"
                required
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="create-supplier-type" className="text-right">供应商类型</Label>
              <Select
                value={newSupplier.supplier_type}
                onValueChange={(value) =>
                  setNewSupplier((prev) => ({ ...prev, supplier_type: value }))
                }
              >
                <SelectTrigger className="col-span-3">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="MATERIAL">物料供应商</SelectItem>
                  <SelectItem value="OUTSOURCE">外协供应商</SelectItem>
                  <SelectItem value="BOTH">两者兼有</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="create-contact-person" className="text-right text-slate-400">联系人</Label>
              <Input
                id="create-contact-person"
                name="contact_person"
                value={newSupplier.contact_person}
                onChange={handleCreateChange}
                className="col-span-3 bg-slate-800 border-slate-700 text-slate-200"
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="create-contact-phone" className="text-right text-slate-400">联系电话</Label>
              <Input
                id="create-contact-phone"
                name="contact_phone"
                value={newSupplier.contact_phone}
                onChange={handleCreateChange}
                className="col-span-3 bg-slate-800 border-slate-700 text-slate-200"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
              取消
            </Button>
            <Button onClick={handleCreateSubmit}>保存</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Rating Dialog */}
      <Dialog open={showRatingDialog} onOpenChange={setShowRatingDialog}>
        <DialogContent className="sm:max-w-[500px] bg-slate-900 border-slate-700">
          <DialogHeader>
            <DialogTitle className="text-slate-200">供应商评级 - {selectedSupplier?.supplier_name}</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="quality-rating" className="text-right text-slate-400">质量评分</Label>
              <Input
                id="quality-rating"
                type="number"
                min="0"
                max="5"
                step="0.1"
                value={ratingData.quality_rating}
                onChange={(e) =>
                  setRatingData((prev) => ({
                    ...prev,
                    quality_rating: parseFloat(e.target.value) || 0,
                  }))
                }
                className="col-span-3 bg-slate-800 border-slate-700 text-slate-200"
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="delivery-rating" className="text-right text-slate-400">交期评分</Label>
              <Input
                id="delivery-rating"
                type="number"
                min="0"
                max="5"
                step="0.1"
                value={ratingData.delivery_rating}
                onChange={(e) =>
                  setRatingData((prev) => ({
                    ...prev,
                    delivery_rating: parseFloat(e.target.value) || 0,
                  }))
                }
                className="col-span-3 bg-slate-800 border-slate-700 text-slate-200"
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="service-rating" className="text-right text-slate-400">服务评分</Label>
              <Input
                id="service-rating"
                type="number"
                min="0"
                max="5"
                step="0.1"
                value={ratingData.service_rating}
                onChange={(e) =>
                  setRatingData((prev) => ({
                    ...prev,
                    service_rating: parseFloat(e.target.value) || 0,
                  }))
                }
                className="col-span-3 bg-slate-800 border-slate-700 text-slate-200"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowRatingDialog(false)}>
              取消
            </Button>
            <Button onClick={handleRatingSubmit}>保存</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Detail Dialog - 简化版 */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="sm:max-w-[600px] bg-slate-900 border-slate-700">
          <DialogHeader>
            <DialogTitle className="text-slate-200">供应商详情</DialogTitle>
          </DialogHeader>
          {selectedSupplier && (
            <div className="grid gap-4 py-4 text-sm">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-slate-400">供应商编码</Label>
                  <p className="font-medium font-mono text-slate-200">{selectedSupplier.supplier_code}</p>
                </div>
                <div>
                  <Label className="text-slate-400">供应商名称</Label>
                  <p className="font-medium text-slate-200">{selectedSupplier.supplier_name}</p>
                </div>
                <div>
                  <Label className="text-slate-400">类型</Label>
                  <p className="font-medium text-slate-200">{selectedSupplier.supplier_type || '-'}</p>
                </div>
                <div>
                  <Label className="text-slate-400">等级</Label>
                  <p className="font-medium">
                    {selectedSupplier.supplier_level && (
                      <Badge className={cn("text-white", getLevelColor(selectedSupplier.supplier_level))}>
                        {selectedSupplier.supplier_level}级
                      </Badge>
                    )}
                  </p>
                </div>
                <div>
                  <Label className="text-slate-400">综合评分</Label>
                  <p className="font-medium text-slate-200">
                    {selectedSupplier.overall_rating
                      ? `${parseFloat(selectedSupplier.overall_rating).toFixed(1)} / 5.0`
                      : '-'}
                  </p>
                </div>
                <div>
                  <Label className="text-slate-400">状态</Label>
                  <p className="font-medium">
                    <Badge className={
                      selectedSupplier.status === 'ACTIVE' ? 'bg-emerald-500' :
                      selectedSupplier.status === 'SUSPENDED' ? 'bg-amber-500' :
                      'bg-red-500'
                    }>
                      {selectedSupplier.status === 'ACTIVE' ? '合作中' : selectedSupplier.status === 'SUSPENDED' ? '暂停' : '黑名单'}
                    </Badge>
                  </p>
                </div>
                {selectedSupplier.contact_person && (
                  <div>
                    <Label className="text-slate-400">联系人</Label>
                    <p className="font-medium text-slate-200">{selectedSupplier.contact_person}</p>
                  </div>
                )}
                {selectedSupplier.contact_phone && (
                  <div>
                    <Label className="text-slate-400">联系电话</Label>
                    <p className="font-medium text-slate-200">{selectedSupplier.contact_phone}</p>
                  </div>
                )}
                {selectedSupplier.contact_email && (
                  <div>
                    <Label className="text-slate-400">邮箱</Label>
                    <p className="font-medium text-slate-200">{selectedSupplier.contact_email}</p>
                  </div>
                )}
                {selectedSupplier.address && (
                  <div>
                    <Label className="text-slate-400">地址</Label>
                    <p className="font-medium text-slate-200">{selectedSupplier.address}</p>
                  </div>
                )}
              </div>
            </div>
          )}
          <DialogFooter>
            <Button onClick={() => setShowDetailDialog(false)} className="bg-slate-800 hover:bg-slate-700 text-slate-200">关闭</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      </motion.div>
      </div>
    </div>
  );
}



