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
  Briefcase,
  FileText,
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
import { fadeIn, staggerContainer } from '../lib/animations';
import { customerApi } from '../services/api';

export default function CustomerManagement() {
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [searchKeyword, setSearchKeyword] = useState('');
  const [filterIndustry, setFilterIndustry] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [total, setTotal] = useState(0);
  const [industries, setIndustries] = useState([]);

  const [newCustomer, setNewCustomer] = useState({
    customer_code: '',
    customer_name: '',
    customer_short_name: '',
    industry: '',
    contact_person: '',
    contact_phone: '',
    contact_email: '',
    address: '',
    remark: '',
  });

  const [editCustomer, setEditCustomer] = useState(null);

  // 加载客户列表
  const loadCustomers = async () => {
    setLoading(true);
    try {
      const params = {
        page,
        page_size: pageSize,
      };
      if (searchKeyword) {
        params.keyword = searchKeyword;
      }
      if (filterIndustry !== 'all') {
        params.industry = filterIndustry;
      }
      if (filterStatus !== 'all') {
        params.is_active = filterStatus === 'active';
      }

      const response = await customerApi.list(params);
      const data = response.data;
      setCustomers(data.items || []);
      setTotal(data.total || 0);
      
      // 提取行业列表
      const industrySet = new Set();
      (data.items || []).forEach(customer => {
        if (customer.industry) {
          industrySet.add(customer.industry);
        }
      });
      setIndustries(Array.from(industrySet).sort());
    } catch (error) {
      console.error('加载客户列表失败:', error);
      alert('加载客户列表失败: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCustomers();
  }, [page, searchKeyword, filterIndustry, filterStatus]);

  const handleCreateChange = (e) => {
    const { name, value } = e.target;
    setNewCustomer((prev) => ({ ...prev, [name]: value }));
  };

  const handleEditChange = (e) => {
    const { name, value } = e.target;
    setEditCustomer((prev) => ({ ...prev, [name]: value }));
  };

  const handleCreateSubmit = async () => {
    try {
      await customerApi.create(newCustomer);
      setShowCreateDialog(false);
      setNewCustomer({
        customer_code: '',
        customer_name: '',
        customer_short_name: '',
        industry: '',
        contact_person: '',
        contact_phone: '',
        contact_email: '',
        address: '',
        remark: '',
      });
      loadCustomers();
    } catch (error) {
      alert('创建客户失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleEditSubmit = async () => {
    try {
      await customerApi.update(editCustomer.id, editCustomer);
      setShowEditDialog(false);
      setEditCustomer(null);
      loadCustomers();
    } catch (error) {
      alert('更新客户失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('确定要删除此客户吗？')) {
      return;
    }
    try {
      await customerApi.delete(id);
      loadCustomers();
    } catch (error) {
      alert('删除客户失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleViewDetail = async (id) => {
    try {
      const response = await customerApi.get(id);
      setSelectedCustomer(response.data);
      setShowDetailDialog(true);
    } catch (error) {
      alert('获取客户详情失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleEdit = async (id) => {
    try {
      const response = await customerApi.get(id);
      setEditCustomer(response.data);
      setShowEditDialog(true);
    } catch (error) {
      alert('获取客户信息失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="show"
      className="space-y-6"
    >
      <PageHeader
        title="客户管理"
        description="管理系统客户信息，包括创建、编辑、查看等操作。"
        actions={
          <Button onClick={() => setShowCreateDialog(true)}>
            <Plus className="mr-2 h-4 w-4" /> 新增客户
          </Button>
        }
      />

      <motion.div variants={fadeIn}>
        <Card>
          <CardHeader className="flex-row items-center justify-between">
            <CardTitle>客户列表</CardTitle>
            <div className="flex items-center space-x-2">
              <Input
                placeholder="搜索客户名称/编码..."
                value={searchKeyword}
                onChange={(e) => setSearchKeyword(e.target.value)}
                className="max-w-sm"
              />
              <Select value={filterIndustry} onValueChange={setFilterIndustry}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="筛选行业" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">所有行业</SelectItem>
                  {industries.map((industry) => (
                    <SelectItem key={industry} value={industry}>
                      {industry}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select value={filterStatus} onValueChange={setFilterStatus}>
                <SelectTrigger className="w-[150px]">
                  <SelectValue placeholder="筛选状态" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">所有状态</SelectItem>
                  <SelectItem value="active">启用</SelectItem>
                  <SelectItem value="inactive">禁用</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="p-4 text-center text-muted-foreground">加载中...</div>
            ) : (
              <>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-border">
                    <thead>
                      <tr className="bg-muted/50">
                        <th className="px-4 py-2 text-left text-sm font-semibold text-foreground">客户编码</th>
                        <th className="px-4 py-2 text-left text-sm font-semibold text-foreground">客户名称</th>
                        <th className="px-4 py-2 text-left text-sm font-semibold text-foreground">简称</th>
                        <th className="px-4 py-2 text-left text-sm font-semibold text-foreground">行业</th>
                        <th className="px-4 py-2 text-left text-sm font-semibold text-foreground">联系人</th>
                        <th className="px-4 py-2 text-left text-sm font-semibold text-foreground">状态</th>
                        <th className="px-4 py-2 text-left text-sm font-semibold text-foreground">操作</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border">
                      {customers.map((customer) => (
                        <tr key={customer.id}>
                          <td className="px-4 py-2 text-sm text-foreground font-mono">{customer.customer_code}</td>
                          <td className="px-4 py-2 text-sm text-foreground">{customer.customer_name}</td>
                          <td className="px-4 py-2 text-sm text-muted-foreground">{customer.customer_short_name || '-'}</td>
                          <td className="px-4 py-2 text-sm text-muted-foreground">{customer.industry || '-'}</td>
                          <td className="px-4 py-2 text-sm text-muted-foreground">
                            <div>{customer.contact_person || '-'}</div>
                            {customer.contact_phone && (
                              <div className="text-xs text-muted-foreground">{customer.contact_phone}</div>
                            )}
                          </td>
                          <td className="px-4 py-2 text-sm">
                            <Badge variant={customer.is_active ? 'default' : 'secondary'}>
                              {customer.is_active ? '启用' : '禁用'}
                            </Badge>
                          </td>
                          <td className="px-4 py-2 text-sm">
                            <div className="flex items-center space-x-2">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleViewDetail(customer.id)}
                              >
                                <Eye className="h-4 w-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleEdit(customer.id)}
                              >
                                <Edit3 className="h-4 w-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleDelete(customer.id)}
                              >
                                <Trash2 className="h-4 w-4 text-red-500" />
                              </Button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {customers.length === 0 && (
                  <p className="p-4 text-center text-muted-foreground">
                    没有找到符合条件的客户。
                  </p>
                )}
                {total > pageSize && (
                  <div className="mt-4 flex items-center justify-between">
                    <div className="text-sm text-muted-foreground">
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

      {/* Create Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="sm:max-w-[600px]">
          <DialogHeader>
            <DialogTitle>新增客户</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="create-customer-code" className="text-right">客户编码 *</Label>
              <Input
                id="create-customer-code"
                name="customer_code"
                value={newCustomer.customer_code}
                onChange={handleCreateChange}
                className="col-span-3"
                required
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="create-customer-name" className="text-right">客户名称 *</Label>
              <Input
                id="create-customer-name"
                name="customer_name"
                value={newCustomer.customer_name}
                onChange={handleCreateChange}
                className="col-span-3"
                required
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="create-short-name" className="text-right">简称</Label>
              <Input
                id="create-short-name"
                name="customer_short_name"
                value={newCustomer.customer_short_name}
                onChange={handleCreateChange}
                className="col-span-3"
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="create-industry" className="text-right">行业</Label>
              <Input
                id="create-industry"
                name="industry"
                value={newCustomer.industry}
                onChange={handleCreateChange}
                className="col-span-3"
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="create-contact-person" className="text-right">联系人</Label>
              <Input
                id="create-contact-person"
                name="contact_person"
                value={newCustomer.contact_person}
                onChange={handleCreateChange}
                className="col-span-3"
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="create-contact-phone" className="text-right">联系电话</Label>
              <Input
                id="create-contact-phone"
                name="contact_phone"
                value={newCustomer.contact_phone}
                onChange={handleCreateChange}
                className="col-span-3"
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="create-contact-email" className="text-right">邮箱</Label>
              <Input
                id="create-contact-email"
                name="contact_email"
                type="email"
                value={newCustomer.contact_email}
                onChange={handleCreateChange}
                className="col-span-3"
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="create-address" className="text-right">地址</Label>
              <Input
                id="create-address"
                name="address"
                value={newCustomer.address}
                onChange={handleCreateChange}
                className="col-span-3"
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

      {/* Edit Dialog */}
      <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
        <DialogContent className="sm:max-w-[600px]">
          <DialogHeader>
            <DialogTitle>编辑客户</DialogTitle>
          </DialogHeader>
          {editCustomer && (
            <div className="grid gap-4 py-4">
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="edit-customer-name" className="text-right">客户名称</Label>
                <Input
                  id="edit-customer-name"
                  name="customer_name"
                  value={editCustomer.customer_name || ''}
                  onChange={handleEditChange}
                  className="col-span-3"
                />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="edit-short-name" className="text-right">简称</Label>
                <Input
                  id="edit-short-name"
                  name="customer_short_name"
                  value={editCustomer.customer_short_name || ''}
                  onChange={handleEditChange}
                  className="col-span-3"
                />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="edit-industry" className="text-right">行业</Label>
                <Input
                  id="edit-industry"
                  name="industry"
                  value={editCustomer.industry || ''}
                  onChange={handleEditChange}
                  className="col-span-3"
                />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="edit-contact-person" className="text-right">联系人</Label>
                <Input
                  id="edit-contact-person"
                  name="contact_person"
                  value={editCustomer.contact_person || ''}
                  onChange={handleEditChange}
                  className="col-span-3"
                />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="edit-contact-phone" className="text-right">联系电话</Label>
                <Input
                  id="edit-contact-phone"
                  name="contact_phone"
                  value={editCustomer.contact_phone || ''}
                  onChange={handleEditChange}
                  className="col-span-3"
                />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="edit-contact-email" className="text-right">邮箱</Label>
                <Input
                  id="edit-contact-email"
                  name="contact_email"
                  type="email"
                  value={editCustomer.contact_email || ''}
                  onChange={handleEditChange}
                  className="col-span-3"
                />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="edit-address" className="text-right">地址</Label>
                <Input
                  id="edit-address"
                  name="address"
                  value={editCustomer.address || ''}
                  onChange={handleEditChange}
                  className="col-span-3"
                />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="edit-is-active" className="text-right">状态</Label>
                <Select
                  value={editCustomer.is_active ? 'active' : 'inactive'}
                  onValueChange={(value) =>
                    setEditCustomer((prev) => ({ ...prev, is_active: value === 'active' }))
                  }
                >
                  <SelectTrigger className="col-span-3">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="active">启用</SelectItem>
                    <SelectItem value="inactive">禁用</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowEditDialog(false)}>
              取消
            </Button>
            <Button onClick={handleEditSubmit}>保存</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Detail Dialog */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="sm:max-w-[600px]">
          <DialogHeader>
            <DialogTitle>客户详情</DialogTitle>
          </DialogHeader>
          {selectedCustomer && (
            <div className="grid gap-4 py-4 text-sm">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-muted-foreground">客户编码</Label>
                  <p className="font-medium font-mono">{selectedCustomer.customer_code}</p>
                </div>
                <div>
                  <Label className="text-muted-foreground">客户名称</Label>
                  <p className="font-medium">{selectedCustomer.customer_name}</p>
                </div>
                <div>
                  <Label className="text-muted-foreground">简称</Label>
                  <p className="font-medium">{selectedCustomer.customer_short_name || '-'}</p>
                </div>
                <div>
                  <Label className="text-muted-foreground">行业</Label>
                  <p className="font-medium">{selectedCustomer.industry || '-'}</p>
                </div>
                <div>
                  <Label className="text-muted-foreground">联系人</Label>
                  <p className="font-medium">{selectedCustomer.contact_person || '-'}</p>
                </div>
                <div>
                  <Label className="text-muted-foreground">联系电话</Label>
                  <p className="font-medium">{selectedCustomer.contact_phone || '-'}</p>
                </div>
                <div>
                  <Label className="text-muted-foreground">邮箱</Label>
                  <p className="font-medium">{selectedCustomer.contact_email || '-'}</p>
                </div>
                <div>
                  <Label className="text-muted-foreground">状态</Label>
                  <p className="font-medium">
                    <Badge variant={selectedCustomer.is_active ? 'default' : 'secondary'}>
                      {selectedCustomer.is_active ? '启用' : '禁用'}
                    </Badge>
                  </p>
                </div>
                <div className="col-span-2">
                  <Label className="text-muted-foreground">地址</Label>
                  <p className="font-medium">{selectedCustomer.address || '-'}</p>
                </div>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button onClick={() => setShowDetailDialog(false)}>关闭</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </motion.div>
  );
}



