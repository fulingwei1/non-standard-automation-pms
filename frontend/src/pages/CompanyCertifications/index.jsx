import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Plus, Edit, Trash2, FileText, Calendar, Award } from 'lucide-react';
import { api } from '@/lib/api';

export default function CompanyCertifications() {
  const [certifications, setCertifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingCert, setEditingCert] = useState(null);
  const [formData, setFormData] = useState({
    cert_name: '',
    cert_type: '',
    cert_number: '',
    issuing_authority: '',
    issue_date: '',
    expiry_date: '',
    status: '有效',
    description: '',
    scope: ''
  });

  useEffect(() => {
    loadCertifications();
  }, []);

  const loadCertifications = async () => {
    try {
      const response = await api.get('/company-certifications');
      setCertifications(response.data);
    } catch (error) {
      console.error('加载资质证书失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingCert) {
        await api.put(`/company-certifications/${editingCert.id}`, formData);
      } else {
        await api.post('/company-certifications', formData);
      }
      setDialogOpen(false);
      resetForm();
      loadCertifications();
    } catch (error) {
      console.error('保存资质证书失败:', error);
    }
  };

  const handleEdit = (cert) => {
    setEditingCert(cert);
    setFormData({
      cert_name: cert.cert_name,
      cert_type: cert.cert_type,
      cert_number: cert.cert_number || '',
      issuing_authority: cert.issuing_authority || '',
      issue_date: cert.issue_date || '',
      expiry_date: cert.expiry_date || '',
      status: cert.status,
      description: cert.description || '',
      scope: cert.scope || ''
    });
    setDialogOpen(true);
  };

  const handleDelete = async (id) => {
    if (!confirm('确定要删除这个资质证书吗？')) return;
    try {
      await api.delete(`/company-certifications/${id}`);
      loadCertifications();
    } catch (error) {
      console.error('删除资质证书失败:', error);
    }
  };

  const resetForm = () => {
    setEditingCert(null);
    setFormData({
      cert_name: '',
      cert_type: '',
      cert_number: '',
      issuing_authority: '',
      issue_date: '',
      expiry_date: '',
      status: '有效',
      description: '',
      scope: ''
    });
  };

  const getStatusColor = (status) => {
    switch (status) {
      case '有效': return 'bg-green-100 text-green-800';
      case '即将到期': return 'bg-yellow-100 text-yellow-800';
      case '已过期': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-64">加载中...</div>;
  }

  return (
    <div className="container mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">公司资质证书管理</h1>
        <Dialog open={dialogOpen} onOpenChange={(open) => {
          setDialogOpen(open);
          if (!open) resetForm();
        }}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              添加证书
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>{editingCert ? '编辑证书' : '添加证书'}</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>证书名称 *</Label>
                  <Input
                    value={formData.cert_name}
                    onChange={(e) => setFormData({...formData, cert_name: e.target.value})}
                    required
                  />
                </div>
                <div>
                  <Label>证书类型 *</Label>
                  <Input
                    value={formData.cert_type}
                    onChange={(e) => setFormData({...formData, cert_type: e.target.value})}
                    required
                  />
                </div>
                <div>
                  <Label>证书编号</Label>
                  <Input
                    value={formData.cert_number}
                    onChange={(e) => setFormData({...formData, cert_number: e.target.value})}
                  />
                </div>
                <div>
                  <Label>发证机构</Label>
                  <Input
                    value={formData.issuing_authority}
                    onChange={(e) => setFormData({...formData, issuing_authority: e.target.value})}
                  />
                </div>
                <div>
                  <Label>发证日期</Label>
                  <Input
                    type="date"
                    value={formData.issue_date}
                    onChange={(e) => setFormData({...formData, issue_date: e.target.value})}
                  />
                </div>
                <div>
                  <Label>到期日期</Label>
                  <Input
                    type="date"
                    value={formData.expiry_date}
                    onChange={(e) => setFormData({...formData, expiry_date: e.target.value})}
                  />
                </div>
                <div>
                  <Label>证书状态</Label>
                  <select
                    value={formData.status}
                    onChange={(e) => setFormData({...formData, status: e.target.value})}
                    className="w-full h-10 px-3 border rounded-md"
                  >
                    <option value="有效">有效</option>
                    <option value="即将到期">即将到期</option>
                    <option value="已过期">已过期</option>
                  </select>
                </div>
              </div>
              <div>
                <Label>证书描述</Label>
                <Input
                  value={formData.description}
                  onChange={(e) => setFormData({...formData, description: e.target.value})}
                />
              </div>
              <div>
                <Label>认证范围</Label>
                <Input
                  value={formData.scope}
                  onChange={(e) => setFormData({...formData, scope: e.target.value})}
                />
              </div>
              <div className="flex justify-end gap-2">
                <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                  取消
                </Button>
                <Button type="submit">
                  {editingCert ? '保存' : '添加'}
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {certifications.map((cert) => (
          <Card key={cert.id}>
            <CardHeader>
              <div className="flex justify-between items-start">
                <CardTitle className="text-lg">{cert.cert_name}</CardTitle>
                <Badge className={getStatusColor(cert.status)}>
                  {cert.status}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center text-sm text-gray-600">
                <Award className="mr-2 h-4 w-4" />
                {cert.cert_type}
              </div>
              {cert.cert_number && (
                <div className="flex items-center text-sm text-gray-600">
                  <FileText className="mr-2 h-4 w-4" />
                  编号：{cert.cert_number}
                </div>
              )}
              {cert.issuing_authority && (
                <div className="text-sm text-gray-600">
                  发证机构：{cert.issuing_authority}
                </div>
              )}
              <div className="flex items-center text-sm text-gray-600">
                <Calendar className="mr-2 h-4 w-4" />
                {cert.issue_date && <span>发证：{cert.issue_date}</span>}
                {cert.expiry_date && <span className="ml-2">到期：{cert.expiry_date}</span>}
              </div>
              {cert.description && (
                <div className="text-sm text-gray-600">
                  {cert.description}
                </div>
              )}
              {cert.scope && (
                <div className="text-sm text-gray-500">
                  范围：{cert.scope}
                </div>
              )}
              <div className="flex gap-2 pt-2">
                <Button size="sm" variant="outline" onClick={() => handleEdit(cert)}>
                  <Edit className="h-4 w-4" />
                </Button>
                <Button size="sm" variant="outline" onClick={() => handleDelete(cert.id)}>
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
