/**
 * Service Record Management (重构版)
 * 现场服务记录管理 - 客服工程师高级功能
 *
 * 功能：
 * 1. 现场服务记录创建、编辑、查看
 * 2. 服务类型管理（安装调试、操作培训、定期维护、故障维修）
 * 3. 服务地点、时间、人员记录
 * 4. 服务内容详细记录
 * 5. 服务照片上传（可选）
 * 6. 服务报告生成
 * 7. 客户签字确认
 * 8. 服务记录搜索和筛选
 */

import { useState, useMemo, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Plus,
  Search,
  Eye,
  Edit,
  FileText,
  Calendar,
  MapPin,
  User,
  Clock,
  Camera,
  Download,
  RefreshCw,
  Wrench,
  Users,
  AlertTriangle,
  Star,
  Upload,
  FileCheck,
  X } from
"lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent } from
"../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter } from
"../components/ui/dialog";
import { Textarea } from "../components/ui/textarea";
import { LoadingCard, ErrorMessage, EmptyState } from "../components/common";
import { toast } from "../components/ui/toast";
import { fadeIn, staggerContainer } from "../lib/animations";
import { serviceApi } from "../services/api";

// 导入重构后的组件
import {
  ServiceRecordOverview,
  SERVICE_STATUS,
  SERVICE_TYPES,
  getServiceStatusConfig,
  getServiceTypeConfig,
  calculateServiceDuration } from
"../components/service-record";

export default function ServiceRecord() {
  const navigate = useNavigate();
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState("ALL");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [dateFilter, setDateFilter] = useState({ start: "", end: "" });
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [selectedRecord, setSelectedRecord] = useState(null);
  const [stats, setStats] = useState({
    total: 0,
    inProgress: 0,
    completed: 0,
    thisMonth: 0,
    totalHours: 0
  });

  // 表单数据状态
  const [formData, setFormData] = useState({
    service_type: "CONSULTATION",
    project_name: "",
    customer_name: "",
    service_location: "",
    service_date: "",
    service_start_time: "",
    service_end_time: "",
    service_engineer: "",
    customer_contact: "",
    customer_phone: "",
    service_content: "",
    service_result: "",
    photos: []
  });

  // 筛选和搜索
  const filteredRecords = useMemo(() => {
    let result = records;

    // 搜索筛选
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      result = result.filter(
        (record) =>
        (record.record_no || "").toLowerCase().includes(query) ||
        (record.project_name || "").toLowerCase().includes(query) ||
        (record.customer_name || "").toLowerCase().includes(query) ||
        (record.service_location || "").toLowerCase().includes(query) ||
        (record.service_engineer || "").toLowerCase().includes(query)
      );
    }

    // 类型筛选
    if (typeFilter !== "ALL") {
      result = result.filter((record) => record.service_type === typeFilter);
    }

    // 状态筛选
    if (statusFilter !== "ALL") {
      result = result.filter((record) => record.status === statusFilter);
    }

    // 日期筛选
    if (dateFilter.start) {
      const startDate = new Date(dateFilter.start);
      result = result.filter((record) => {
        const recordDate = new Date(record.service_date);
        return recordDate >= startDate;
      });
    }

    if (dateFilter.end) {
      const endDate = new Date(dateFilter.end);
      result = result.filter((record) => {
        const recordDate = new Date(record.service_date);
        return recordDate <= endDate;
      });
    }

    return result;
  }, [records, searchQuery, typeFilter, statusFilter, dateFilter]);

  // 加载服务记录
  const loadRecords = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const params = {
        page: 1,
        page_size: 1000
      };
      const response = await serviceApi.records.list(params);
      const recordsData = response.data?.items || response.data || [];

      // 转换后端数据为前端格式
      const transformedRecords = recordsData.map((record) => ({
        id: record.id,
        record_no: record.record_no || "",
        service_type: record.service_type || "",
        project_code: record.project_code || "",
        project_name: record.project_name || "",
        machine_no: record.machine_no || "",
        customer_name: record.customer_name || "",
        service_location: record.service_location || "",
        service_date: record.service_date || "",
        service_start_time: record.service_start_time || "",
        service_end_time: record.service_end_time || "",
        service_duration: record.service_duration || 0,
        service_engineer: record.service_engineer || "",
        service_engineer_phone: record.service_engineer_phone || "",
        customer_contact: record.customer_contact || "",
        customer_phone: record.customer_phone || "",
        service_content: record.service_content || "",
        service_result: record.service_result || "",
        issues_found: record.issues_found || "",
        solutions: record.solutions || "",
        customer_satisfaction: record.customer_satisfaction || null,
        customer_feedback: record.customer_feedback || "",
        customer_signature: record.customer_signature || false,
        signature_time: record.signature_time || "",
        photos: record.photos || [],
        status: record.status || "进行中",
        created_at: record.created_at || ""
      }));

      setRecords(transformedRecords);
    } catch (err) {
      console.error("Failed to load records:", err);
      setError(err.response?.data?.detail || err.message || "加载服务记录失败");
      setRecords([]);
    } finally {
      setLoading(false);
    }
  }, []);

  // 加载统计数据
  const loadStatistics = useCallback(async () => {
    try {
      const now = new Date();
      const thisMonthStart = new Date(now.getFullYear(), now.getMonth(), 1);

      setStats({
        total: records.length,
        inProgress: records.filter(
          (r) => r.status === "进行中" || r.status === "IN_PROGRESS"
        ).length,
        completed: records.filter(
          (r) => r.status === "已完成" || r.status === "COMPLETED"
        ).length,
        thisMonth: records.filter((r) => {
          if (!r.service_date) {return false;}
          const recordDate = new Date(r.service_date);
          return recordDate >= thisMonthStart;
        }).length,
        totalHours: records.reduce(
          (sum, r) => sum + (r.service_duration || 0),
          0
        )
      });
    } catch (err) {
      console.error("Failed to load statistics:", err);
    }
  }, [records]);

  // 初始化加载
  useEffect(() => {
    loadRecords();
  }, []);

  useEffect(() => {
    if (records.length > 0 || !loading) {
      loadStatistics();
    }
  }, [records, loading, loadStatistics]);

  // 创建服务记录
  const handleCreateRecord = async () => {
    try {
      const serviceData = {
        ...formData,
        service_duration: calculateServiceDuration(formData.service_start_time, formData.service_end_time)
      };

      await serviceApi.records.create(serviceData);

      setShowCreateDialog(false);
      resetForm();
      await loadRecords();
      toast.success("服务记录创建成功");
    } catch (error) {
      console.error("Failed to create record:", error);
      toast.error("创建失败: " + (error.response?.data?.detail || error.message));
    }
  };

  // 重置表单
  const resetForm = () => {
    setFormData({
      service_type: "CONSULTATION",
      project_name: "",
      customer_name: "",
      service_location: "",
      service_date: "",
      service_start_time: "",
      service_end_time: "",
      service_engineer: "",
      customer_contact: "",
      customer_phone: "",
      service_content: "",
      service_result: "",
      photos: []
    });
  };

  // 查看详情
  const handleViewDetail = (record) => {
    setSelectedRecord(record);
    setShowDetailDialog(true);
  };

  // 快速操作处理
  const handleQuickAction = (action) => {
    switch (action) {
      case 'createService':
        setShowCreateDialog(true);
        break;
      case 'todaySchedule':
        // 跳转到今日安排视图
        {
          const today = new Date().toISOString().split('T')[0];
          setDateFilter({ start: today, end: today });
        }
        break;
      case 'pendingReports':
        // 筛选待审核的报告
        setStatusFilter('PENDING_REVIEW');
        break;
      case 'customerFeedback':
        // 筛选有反馈的记录
        setRecords(records.filter((r) => r.customer_feedback));
        break;
    }
  };

  // 照片上传处理
  const handlePhotoUpload = (e) => {
    const files = Array.from(e.target.files);
    const newPhotos = files.map((file) => ({
      file,
      url: URL.createObjectURL(file),
      name: file.name
    }));
    setFormData((prev) => ({
      ...prev,
      photos: [...prev.photos, ...newPhotos]
    }));
  };

  const removePhoto = (index) => {
    setFormData((prev) => ({
      ...prev,
      photos: prev.photos.filter((_, i) => i !== index)
    }));
  };

  // 获取服务类型图标
  const getServiceTypeIcon = (type) => {
    const typeConfig = getServiceTypeConfig(type);
    const iconMap = {
      'Wrench': Wrench,
      'Users': Users,
      'RefreshCw': RefreshCw,
      'AlertTriangle': AlertTriangle,
      'TrendingUp': Star,
      'FileText': FileText
    };
    return iconMap[typeConfig.icon] || FileText;
  };

  if (loading && records.length === 0) {
    return (
      <LoadingCard message="加载服务记录中..." />);

  }

  if (error) {
    return (
      <ErrorMessage
        message={error}
        onRetry={loadRecords} />);


  }

  return (
    <div className="min-h-screen bg-slate-900 text-white">
      <PageHeader
        title="服务记录管理"
        subtitle="现场服务记录管理 - 客服工程师高级功能"
        breadcrumbs={[
        { label: "服务管理", href: "/service" },
        { label: "服务记录" }]
        }
        actions={[
        {
          label: "新建记录",
          icon: Plus,
          onClick: () => setShowCreateDialog(true),
          variant: "default"
        }]
        } />


      <div className="container mx-auto px-4 py-6 space-y-6">
        {/* 服务概览 */}
        <ServiceRecordOverview
          records={records}
          stats={stats}
          onQuickAction={handleQuickAction} />


        {/* 筛选和搜索 */}
        <motion.div variants={fadeIn} initial="hidden" animate="visible">
          <Card>
            <CardContent className="p-4">
              <div className="flex flex-col md:flex-row gap-4">
                <div className="flex-1">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <Input
                      placeholder="搜索记录号、项目名称、客户名称、服务地点..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="pl-10 bg-slate-800/50 border-slate-700" />

                  </div>
                </div>
                <div className="flex gap-2">
                  <select
                    value={typeFilter}
                    onChange={(e) => setTypeFilter(e.target.value)}
                    className="px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-sm text-white">

                    <option value="ALL">全部类型</option>
                    {Object.values(SERVICE_TYPES).map((type) =>
                    <option key={type.label} value={type.label}>
                        {type.label}
                    </option>
                    )}
                  </select>
                  <select
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value)}
                    className="px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-sm text-white">

                    <option value="ALL">全部状态</option>
                    {Object.values(SERVICE_STATUS).map((status) =>
                    <option key={status.label} value={status.label}>
                        {status.label}
                    </option>
                    )}
                  </select>
                  <Input
                    type="date"
                    value={dateFilter.start}
                    onChange={(e) => setDateFilter((prev) => ({ ...prev, start: e.target.value }))}
                    className="w-40" />

                  <Input
                    type="date"
                    value={dateFilter.end}
                    onChange={(e) => setDateFilter((prev) => ({ ...prev, end: e.target.value }))}
                    className="w-40" />

                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* 服务记录列表 */}
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="space-y-4">

          {filteredRecords.length === 0 ?
          <Card>
              <CardContent className="p-8">
                <EmptyState
                icon={FileText}
                title="暂无服务记录"
                description={searchQuery || typeFilter !== "ALL" || statusFilter !== "ALL" ? "没有找到匹配的记录" : "还没有创建服务记录"}
                action={
                <Button
                  onClick={() => setShowCreateDialog(true)}
                  className="mt-4">

                      <Plus className="h-4 w-4 mr-2" />
                      创建第一个服务记录
                </Button>
                } />

              </CardContent>
          </Card> :

          filteredRecords.map((record, index) => {
            const statusConfig = getServiceStatusConfig(record.status);
            const typeConfig = getServiceTypeConfig(record.service_type);
            const TypeIcon = getServiceTypeIcon(record.service_type);

            return (
              <motion.div
                key={record.id}
                variants={fadeIn}
                custom={index}>

                  <Card className="bg-slate-800/50 border-slate-700 hover:bg-slate-800/70 transition-colors">
                    <CardContent className="p-6">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-4">
                            <TypeIcon className="h-5 w-5 text-blue-400" />
                            <h3 className="text-lg font-semibold text-white">
                              {record.project_name || "未命名项目"}
                            </h3>
                            <Badge className={statusConfig.color}>
                              {statusConfig.label}
                            </Badge>
                            <Badge variant="outline" className="border-blue-500 text-blue-400">
                              {typeConfig.label}
                            </Badge>
                          </div>
                          
                          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
                            <div className="flex items-center gap-2 text-sm">
                              <User className="h-4 w-4 text-slate-400" />
                              <span className="text-slate-300">客户:</span>
                              <span className="text-white">{record.customer_name}</span>
                            </div>
                            <div className="flex items-center gap-2 text-sm">
                              <MapPin className="h-4 w-4 text-slate-400" />
                              <span className="text-slate-300">地点:</span>
                              <span className="text-white truncate">{record.service_location}</span>
                            </div>
                            <div className="flex items-center gap-2 text-sm">
                              <Calendar className="h-4 w-4 text-slate-400" />
                              <span className="text-slate-300">日期:</span>
                              <span className="text-white">
                                {record.service_date ? new Date(record.service_date).toLocaleDateString() : "未设置"}
                              </span>
                            </div>
                            <div className="flex items-center gap-2 text-sm">
                              <Clock className="h-4 w-4 text-slate-400" />
                              <span className="text-slate-300">工程师:</span>
                              <span className="text-white">{record.service_engineer}</span>
                            </div>
                          </div>

                          {record.service_content &&
                        <div className="mb-4">
                              <p className="text-sm text-slate-400 mb-1">服务内容:</p>
                              <p className="text-sm text-white line-clamp-2">
                                {record.service_content}
                              </p>
                        </div>
                        }

                          {record.photos && record.photos.length > 0 &&
                        <div className="flex items-center gap-2 text-sm">
                              <Camera className="h-4 w-4 text-slate-400" />
                              <span className="text-slate-300">照片:</span>
                              <span className="text-white">{record.photos.length} 张</span>
                        </div>
                        }
                        </div>

                        <div className="flex items-center gap-2">
                          <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleViewDetail(record)}
                          className="text-slate-400 hover:text-white">

                            <Eye className="h-4 w-4" />
                          </Button>
                          <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => navigate(`/service/records/${record.id}/edit`)}
                          className="text-slate-400 hover:text-white">

                            <Edit className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
              </motion.div>);

          })
          }
        </motion.div>
      </div>

      {/* 创建服务记录对话框 */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="max-w-4xl bg-slate-900 border-slate-700 max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>创建服务记录</DialogTitle>
          </DialogHeader>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-slate-300">服务类型</label>
              <select
                value={formData.service_type}
                onChange={(e) => setFormData((prev) => ({ ...prev, service_type: e.target.value }))}
                className="w-full mt-1 p-2 bg-slate-800 border border-slate-700 rounded text-white">

                {Object.entries(SERVICE_TYPES).map(([key, type]) =>
                <option key={key} value={key}>{type.label}</option>
                )}
              </select>
            </div>
            
            <div>
              <label className="text-sm font-medium text-slate-300">项目名称</label>
              <Input
                value={formData.project_name}
                onChange={(e) => setFormData((prev) => ({ ...prev, project_name: e.target.value }))}
                className="mt-1 bg-slate-800 border-slate-700"
                placeholder="请输入项目名称" />

            </div>
            
            <div>
              <label className="text-sm font-medium text-slate-300">客户名称</label>
              <Input
                value={formData.customer_name}
                onChange={(e) => setFormData((prev) => ({ ...prev, customer_name: e.target.value }))}
                className="mt-1 bg-slate-800 border-slate-700"
                placeholder="请输入客户名称" />

            </div>
            
            <div>
              <label className="text-sm font-medium text-slate-300">服务地点</label>
              <Input
                value={formData.service_location}
                onChange={(e) => setFormData((prev) => ({ ...prev, service_location: e.target.value }))}
                className="mt-1 bg-slate-800 border-slate-700"
                placeholder="请输入服务地点" />

            </div>
            
            <div>
              <label className="text-sm font-medium text-slate-300">服务日期</label>
              <Input
                type="date"
                value={formData.service_date}
                onChange={(e) => setFormData((prev) => ({ ...prev, service_date: e.target.value }))}
                className="mt-1 bg-slate-800 border-slate-700" />

            </div>
            
            <div>
              <label className="text-sm font-medium text-slate-300">服务工程师</label>
              <Input
                value={formData.service_engineer}
                onChange={(e) => setFormData((prev) => ({ ...prev, service_engineer: e.target.value }))}
                className="mt-1 bg-slate-800 border-slate-700"
                placeholder="请输入工程师姓名" />

            </div>
            
            <div>
              <label className="text-sm font-medium text-slate-300">客户联系人</label>
              <Input
                value={formData.customer_contact}
                onChange={(e) => setFormData((prev) => ({ ...prev, customer_contact: e.target.value }))}
                className="mt-1 bg-slate-800 border-slate-700"
                placeholder="请输入联系人姓名" />

            </div>
            
            <div>
              <label className="text-sm font-medium text-slate-300">联系电话</label>
              <Input
                value={formData.customer_phone}
                onChange={(e) => setFormData((prev) => ({ ...prev, customer_phone: e.target.value }))}
                className="mt-1 bg-slate-800 border-slate-700"
                placeholder="请输入联系电话" />

            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
            <div>
              <label className="text-sm font-medium text-slate-300">开始时间</label>
              <Input
                type="datetime-local"
                value={formData.service_start_time}
                onChange={(e) => setFormData((prev) => ({ ...prev, service_start_time: e.target.value }))}
                className="mt-1 bg-slate-800 border-slate-700" />

            </div>
            
            <div>
              <label className="text-sm font-medium text-slate-300">结束时间</label>
              <Input
                type="datetime-local"
                value={formData.service_end_time}
                onChange={(e) => setFormData((prev) => ({ ...prev, service_end_time: e.target.value }))}
                className="mt-1 bg-slate-800 border-slate-700" />

            </div>
          </div>

          <div className="mt-4">
            <label className="text-sm font-medium text-slate-300">服务内容</label>
            <Textarea
              value={formData.service_content}
              onChange={(e) => setFormData((prev) => ({ ...prev, service_content: e.target.value }))}
              className="mt-1 bg-slate-800 border-slate-700"
              rows={4}
              placeholder="请详细描述服务内容..." />

          </div>

          <div className="mt-4">
            <label className="text-sm font-medium text-slate-300">服务结果</label>
            <Textarea
              value={formData.service_result}
              onChange={(e) => setFormData((prev) => ({ ...prev, service_result: e.target.value }))}
              className="mt-1 bg-slate-800 border-slate-700"
              rows={3}
              placeholder="请描述服务结果..." />

          </div>

          <div className="mt-4">
            <label className="text-sm font-medium text-slate-300">照片上传</label>
            <div className="mt-2">
              <input
                type="file"
                multiple
                accept="image/*"
                onChange={handlePhotoUpload}
                className="hidden"
                id="photo-upload" />

              <label htmlFor="photo-upload">
                <Button
                  type="button"
                  variant="outline"
                  className="cursor-pointer">

                  <Upload className="h-4 w-4 mr-2" />
                  选择照片
                </Button>
              </label>
            </div>
            
            {formData.photos.length > 0 &&
            <div className="mt-4 grid grid-cols-4 gap-2">
                {formData.photos.map((photo, index) =>
              <div key={index} className="relative">
                    <img
                  src={photo.url}
                  alt={photo.name}
                  className="w-full h-20 object-cover rounded border border-slate-700" />

                    <Button
                  type="button"
                  variant="destructive"
                  size="sm"
                  className="absolute -top-2 -right-2 h-6 w-6 p-0"
                  onClick={() => removePhoto(index)}>

                      <X className="h-3 w-3" />
                    </Button>
              </div>
              )}
            </div>
            }
          </div>

          <DialogFooter className="mt-6">
            <Button
              variant="outline"
              onClick={() => setShowCreateDialog(false)}>

              取消
            </Button>
            <Button
              onClick={handleCreateRecord}
              className="bg-blue-500 hover:bg-blue-600">

              <FileCheck className="h-4 w-4 mr-2" />
              创建记录
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 详情对话框 */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="max-w-5xl bg-slate-900 border-slate-700 max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>服务记录详情</DialogTitle>
          </DialogHeader>
          
          {selectedRecord &&
          <div className="space-y-6">
              {/* 基本信息 */}
              <div>
                <h3 className="text-lg font-semibold text-white mb-4">基本信息</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  <div>
                    <span className="text-sm text-slate-400">记录编号:</span>
                    <p className="text-white">{selectedRecord.record_no}</p>
                  </div>
                  <div>
                    <span className="text-sm text-slate-400">项目名称:</span>
                    <p className="text-white">{selectedRecord.project_name}</p>
                  </div>
                  <div>
                    <span className="text-sm text-slate-400">客户名称:</span>
                    <p className="text-white">{selectedRecord.customer_name}</p>
                  </div>
                  <div>
                    <span className="text-sm text-slate-400">服务类型:</span>
                    <p className="text-white">
                      {getServiceTypeConfig(selectedRecord.service_type).label}
                    </p>
                  </div>
                  <div>
                    <span className="text-sm text-slate-400">服务地点:</span>
                    <p className="text-white">{selectedRecord.service_location}</p>
                  </div>
                  <div>
                    <span className="text-sm text-slate-400">服务日期:</span>
                    <p className="text-white">
                      {selectedRecord.service_date ? new Date(selectedRecord.service_date).toLocaleDateString() : "-"}
                    </p>
                  </div>
                </div>
              </div>

              {/* 服务内容 */}
              <div>
                <h3 className="text-lg font-semibold text-white mb-4">服务内容</h3>
                <p className="text-slate-300">{selectedRecord.service_content || "-"}</p>
              </div>

              {/* 服务结果 */}
              <div>
                <h3 className="text-lg font-semibold text-white mb-4">服务结果</h3>
                <p className="text-slate-300">{selectedRecord.service_result || "-"}</p>
              </div>

              {/* 照片展示 */}
              {selectedRecord.photos && selectedRecord.photos.length > 0 &&
            <div>
                  <h3 className="text-lg font-semibold text-white mb-4">服务照片</h3>
                  <div className="grid grid-cols-4 gap-4">
                    {selectedRecord.photos.map((photo, index) =>
                <img
                  key={index}
                  src={photo.url || photo}
                  alt={`服务照片 ${index + 1}`}
                  className="w-full h-32 object-cover rounded border border-slate-700" />

                )}
                  </div>
            </div>
            }

              {/* 客户反馈 */}
              {selectedRecord.customer_feedback &&
            <div>
                  <h3 className="text-lg font-semibold text-white mb-4">客户反馈</h3>
                  <div className="bg-slate-800/50 p-4 rounded">
                    {selectedRecord.customer_satisfaction &&
                <div className="flex items-center gap-2 mb-2">
                        <span className="text-sm text-slate-400">满意度:</span>
                        <div className="flex">
                          {[1, 2, 3, 4, 5].map((star) =>
                    <Star
                      key={star}
                      className={`h-4 w-4 ${
                      star <= selectedRecord.customer_satisfaction ?
                      'text-yellow-400 fill-current' :
                      'text-slate-600'}`
                      } />

                    )}
                        </div>
                </div>
                }
                    <p className="text-slate-300">{selectedRecord.customer_feedback}</p>
                  </div>
            </div>
            }
          </div>
          }

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowDetailDialog(false)}>

              关闭
            </Button>
            <Button
              onClick={() => {
                // 下载报告功能
                toast.info("报告下载功能开发中...");
              }}
              className="bg-blue-500 hover:bg-blue-600">

              <Download className="h-4 w-4 mr-2" />
              下载报告
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>);

}
