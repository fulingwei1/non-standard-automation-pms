import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import {
  Plus,
  Edit,
  Trash2,
  Search,
  DollarSign,
  Users,
  Briefcase,
  Building2,
  History,
} from "lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "../components/ui/dialog";
import { Label } from "../components/ui/label";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "../components/ui/tabs";
import { hourlyRateApi } from "../services/api";
import { formatDate } from "../lib/utils";
import { fadeIn } from "../lib/animations";

import { confirmAction } from "@/lib/confirmAction";
export default function HourlyRateManagement() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [configs, setConfigs] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);

  // 筛选条件
  const [configType, setConfigType] = useState("");
  const [userId, setUserId] = useState("");
  const [roleId, setRoleId] = useState("");
  const [deptId, setDeptId] = useState("");

  // 对话框
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingConfig, setEditingConfig] = useState(null);
  const [formData, setFormData] = useState({
    config_type: "DEFAULT",
    user_id: null,
    role_id: null,
    dept_id: null,
    hourly_rate: "",
    effective_date: "",
    expiry_date: "",
    is_active: true,
  });

  const loadConfigs = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const params = {
        page,
        page_size: pageSize,
      };

      if (configType) {params.config_type = configType;}
      if (userId) {params.user_id = parseInt(userId);}
      if (roleId) {params.role_id = parseInt(roleId);}
      if (deptId) {params.dept_id = parseInt(deptId);}

      const response = await hourlyRateApi.list(params);
      const data = response.data?.data || response.data || response;

      if (data && typeof data === "object" && "items" in data) {
        setConfigs(data.items || []);
        setTotal(data.total || 0);
      } else if (Array.isArray(data)) {
        setConfigs(data);
        setTotal(data?.length);
      } else {
        setConfigs([]);
        setTotal(0);
      }
    } catch (err) {
      console.error("Failed to load configs:", err);
      setError(err.response?.data?.detail || err.message || "加载配置失败");
      setConfigs([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, configType, userId, roleId, deptId]);

  useEffect(() => {
    loadConfigs();
  }, [loadConfigs]);

  const handleCreate = () => {
    setEditingConfig(null);
    setFormData({
      config_type: "DEFAULT",
      user_id: null,
      role_id: null,
      dept_id: null,
      hourly_rate: "",
      effective_date: "",
      expiry_date: "",
      is_active: true,
    });
    setDialogOpen(true);
  };

  const handleEdit = (config) => {
    setEditingConfig(config);
    setFormData({
      config_type: config.config_type,
      user_id: config.user_id,
      role_id: config.role_id,
      dept_id: config.dept_id,
      hourly_rate: config.hourly_rate,
      effective_date: config.effective_date || "",
      expiry_date: config.expiry_date || "",
      is_active: config.is_active,
    });
    setDialogOpen(true);
  };

  const handleSave = async () => {
    try {
      setLoading(true);
      setError(null);

      const submitData = {
        ...formData,
        hourly_rate: parseFloat(formData.hourly_rate),
        user_id: formData.user_id ? parseInt(formData.user_id) : null,
        role_id: formData.role_id ? parseInt(formData.role_id) : null,
        dept_id: formData.dept_id ? parseInt(formData.dept_id) : null,
      };

      if (editingConfig) {
        await hourlyRateApi.update(editingConfig.id, submitData);
      } else {
        await hourlyRateApi.create(submitData);
      }

      setDialogOpen(false);
      loadConfigs();
    } catch (err) {
      console.error("Failed to save config:", err);
      setError(err.response?.data?.detail || err.message || "保存失败");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!await confirmAction("确定要删除这个配置吗？")) {
      return;
    }

    try {
      setLoading(true);
      await hourlyRateApi.delete(id);
      loadConfigs();
    } catch (err) {
      console.error("Failed to delete config:", err);
      setError(err.response?.data?.detail || err.message || "删除失败");
    } finally {
      setLoading(false);
    }
  };

  const getConfigTypeLabel = (type) => {
    const labels = {
      DEFAULT: "默认",
      USER: "用户",
      ROLE: "角色",
      DEPT: "部门",
    };
    return labels[type] || type;
  };

  const getConfigTypeIcon = (type) => {
    switch (type) {
      case "USER":
        return <Users className="h-4 w-4" />;
      case "ROLE":
        return <Briefcase className="h-4 w-4" />;
      case "DEPT":
        return <Building2 className="h-4 w-4" />;
      default:
        return <DollarSign className="h-4 w-4" />;
    }
  };

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={fadeIn}
      className="space-y-6"
    >
      <PageHeader title="时薪配置管理" />

      {/* 筛选区域 */}
      <Card>
        <CardHeader>
          <CardTitle>筛选条件</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <Label>配置类型</Label>
              <Select value={configType} onValueChange={setConfigType}>
                <SelectTrigger>
                  <SelectValue placeholder="全部" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部</SelectItem>
                  <SelectItem value="DEFAULT">默认</SelectItem>
                  <SelectItem value="USER">用户</SelectItem>
                  <SelectItem value="ROLE">角色</SelectItem>
                  <SelectItem value="DEPT">部门</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label>用户ID</Label>
              <Input
                type="number"
                placeholder="用户ID"
                value={userId}
                onChange={(e) => setUserId(e.target.value)}
              />
            </div>

            <div>
              <Label>角色ID</Label>
              <Input
                type="number"
                placeholder="角色ID"
                value={roleId}
                onChange={(e) => setRoleId(e.target.value)}
              />
            </div>

            <div>
              <Label>部门ID</Label>
              <Input
                type="number"
                placeholder="部门ID"
                value={deptId}
                onChange={(e) => setDeptId(e.target.value)}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 错误提示 */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {/* 配置列表 */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>时薪配置列表</CardTitle>
          <Button onClick={handleCreate}>
            <Plus className="h-4 w-4 mr-2" />
            新建配置
          </Button>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8">加载中...</div>
          ) : configs.length === 0 ? (
            <div className="text-center py-8 text-gray-500">暂无配置</div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left p-2">ID</th>
                      <th className="text-left p-2">配置类型</th>
                      <th className="text-left p-2">关联对象</th>
                      <th className="text-left p-2">时薪</th>
                      <th className="text-left p-2">生效日期</th>
                      <th className="text-left p-2">失效日期</th>
                      <th className="text-left p-2">状态</th>
                      <th className="text-left p-2">操作</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(configs || []).map((config) => (
                      <tr key={config.id} className="border-b hover:bg-gray-50">
                        <td className="p-2">{config.id}</td>
                        <td className="p-2">
                          <Badge
                            variant="outline"
                            className="flex items-center gap-1 w-fit"
                          >
                            {getConfigTypeIcon(config.config_type)}
                            {getConfigTypeLabel(config.config_type)}
                          </Badge>
                        </td>
                        <td className="p-2">
                          {config.user_name && (
                            <div>用户: {config.user_name}</div>
                          )}
                          {config.role_name && (
                            <div>角色: {config.role_name}</div>
                          )}
                          {config.dept_name && (
                            <div>部门: {config.dept_name}</div>
                          )}
                          {!config.user_name &&
                            !config.role_name &&
                            !config.dept_name && (
                              <span className="text-gray-400">默认配置</span>
                            )}
                        </td>
                        <td className="p-2 font-semibold">
                          ¥{config.hourly_rate}
                        </td>
                        <td className="p-2 text-sm">
                          {config.effective_date
                            ? formatDate(config.effective_date)
                            : "-"}
                        </td>
                        <td className="p-2 text-sm">
                          {config.expiry_date
                            ? formatDate(config.expiry_date)
                            : "-"}
                        </td>
                        <td className="p-2">
                          <Badge
                            variant={config.is_active ? "default" : "secondary"}
                          >
                            {config.is_active ? "启用" : "禁用"}
                          </Badge>
                        </td>
                        <td className="p-2">
                          <div className="flex gap-2">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleEdit(config)}
                            >
                              <Edit className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleDelete(config.id)}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* 分页 */}
              <div className="flex items-center justify-between mt-4">
                <div className="text-sm text-gray-600">共 {total} 条记录</div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={page === 1}
                    onClick={() => setPage(page - 1)}
                  >
                    上一页
                  </Button>
                  <span className="px-4 py-2 text-sm">
                    第 {page} 页 / 共 {Math.ceil(total / pageSize)} 页
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={page >= Math.ceil(total / pageSize)}
                    onClick={() => setPage(page + 1)}
                  >
                    下一页
                  </Button>
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* 编辑对话框 */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>{editingConfig ? "编辑配置" : "新建配置"}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>配置类型 *</Label>
              <Select
                value={formData.config_type}
                onValueChange={(value) =>
                  setFormData({ ...formData, config_type: value })
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="DEFAULT">默认</SelectItem>
                  <SelectItem value="USER">用户</SelectItem>
                  <SelectItem value="ROLE">角色</SelectItem>
                  <SelectItem value="DEPT">部门</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {formData.config_type === "USER" && (
              <div>
                <Label>用户ID *</Label>
                <Input
                  type="number"
                  value={formData.user_id || ""}
                  onChange={(e) =>
                    setFormData({ ...formData, user_id: e.target.value })
                  }
                />
              </div>
            )}

            {formData.config_type === "ROLE" && (
              <div>
                <Label>角色ID *</Label>
                <Input
                  type="number"
                  value={formData.role_id || ""}
                  onChange={(e) =>
                    setFormData({ ...formData, role_id: e.target.value })
                  }
                />
              </div>
            )}

            {formData.config_type === "DEPT" && (
              <div>
                <Label>部门ID *</Label>
                <Input
                  type="number"
                  value={formData.dept_id || ""}
                  onChange={(e) =>
                    setFormData({ ...formData, dept_id: e.target.value })
                  }
                />
              </div>
            )}

            <div>
              <Label>时薪 *</Label>
              <Input
                type="number"
                step="0.01"
                value={formData.hourly_rate}
                onChange={(e) =>
                  setFormData({ ...formData, hourly_rate: e.target.value })
                }
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>生效日期</Label>
                <Input
                  type="date"
                  value={formData.effective_date}
                  onChange={(e) =>
                    setFormData({ ...formData, effective_date: e.target.value })
                  }
                />
              </div>
              <div>
                <Label>失效日期</Label>
                <Input
                  type="date"
                  value={formData.expiry_date}
                  onChange={(e) =>
                    setFormData({ ...formData, expiry_date: e.target.value })
                  }
                />
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>
              取消
            </Button>
            <Button onClick={handleSave} disabled={loading}>
              保存
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </motion.div>
  );
}