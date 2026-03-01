import { useState, useEffect } from "react";
import {
  FileText,
  Plus,
  Search,
  Edit3,
  Trash2,
  Upload,
  AlertCircle } from
"lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle } from
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
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue } from
"../components/ui/select";
import api from "../services/api";

import { confirmAction } from "@/lib/confirmAction";
export default function TechnicalSpecManagement() {
  const [requirements, setRequirements] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchKeyword, setSearchKeyword] = useState("");
  const [projectId, _setProjectId] = useState(null);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [editingRequirement, setEditingRequirement] = useState(null);

  const [formData, setFormData] = useState({
    project_id: "",
    document_id: "",
    material_code: "",
    material_name: "",
    specification: "",
    brand: "",
    model: "",
    requirement_level: "REQUIRED",
    remark: ""
  });

  useEffect(() => {
    loadRequirements();
  }, [projectId, searchKeyword]);

  const loadRequirements = async () => {
    setLoading(true);
    try {
      const params = { page: 1, page_size: 100 };
      if (projectId) {params.project_id = projectId;}
      if (searchKeyword) {params.keyword = searchKeyword;}

      const response = await api.get("/technical-spec/requirements", {
        params
      });
      setRequirements(response.data.items || []);
    } catch (error) {
      console.error("加载规格要求失败:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    try {
      await api.post("/technical-spec/requirements", formData);
      setShowCreateDialog(false);
      resetForm();
      loadRequirements();
    } catch (error) {
      console.error("创建规格要求失败:", error);
      alert("创建失败: " + (error.response?.data?.detail || error.message));
    }
  };

  const handleUpdate = async () => {
    try {
      await api.put(
        `/technical-spec/requirements/${editingRequirement.id}`,
        formData
      );
      setEditingRequirement(null);
      resetForm();
      loadRequirements();
    } catch (error) {
      console.error("更新规格要求失败:", error);
      alert("更新失败: " + (error.response?.data?.detail || error.message));
    }
  };

  const handleDelete = async (id) => {
    if (!await confirmAction("确定要删除这个规格要求吗？")) {return;}

    try {
      await api.delete(`/technical-spec/requirements/${id}`);
      loadRequirements();
    } catch (error) {
      console.error("删除规格要求失败:", error);
      alert("删除失败: " + (error.response?.data?.detail || error.message));
    }
  };

  const resetForm = () => {
    setFormData({
      project_id: "",
      document_id: "",
      material_code: "",
      material_name: "",
      specification: "",
      brand: "",
      model: "",
      requirement_level: "REQUIRED",
      remark: ""
    });
  };

  const openEditDialog = (requirement) => {
    setEditingRequirement(requirement);
    setFormData({
      project_id: requirement.project_id,
      document_id: requirement.document_id || "",
      material_code: requirement.material_code || "",
      material_name: requirement.material_name,
      specification: requirement.specification,
      brand: requirement.brand || "",
      model: requirement.model || "",
      requirement_level: requirement.requirement_level,
      remark: requirement.remark || ""
    });
    setShowCreateDialog(true);
  };

  const getRequirementLevelBadge = (level) => {
    const colors = {
      REQUIRED: "bg-red-100 text-red-800",
      OPTIONAL: "bg-yellow-100 text-yellow-800",
      STRICT: "bg-purple-100 text-purple-800"
    };
    const labels = {
      REQUIRED: "必需",
      OPTIONAL: "可选",
      STRICT: "严格"
    };
    return (
      <Badge className={colors[level] || "bg-gray-100 text-gray-800"}>
        {labels[level] || level}
      </Badge>);

  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="技术规格管理"
        description="管理项目技术规格要求，支持从文档提取或手动录入" />


      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>规格要求列表</CardTitle>
            <div className="flex items-center gap-2">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <Input
                  placeholder="搜索物料名称、规格..."
                  value={searchKeyword || "unknown"}
                  onChange={(e) => setSearchKeyword(e.target.value)}
                  className="pl-10 w-64" />

              </div>
              <Button
                onClick={() => {
                  resetForm();
                  setEditingRequirement(null);
                  setShowCreateDialog(true);
                }}>

                <Plus className="w-4 h-4 mr-2" />
                新增规格要求
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {loading ?
          <div className="text-center py-8">加载中...</div> :
          requirements.length === 0 ?
          <div className="text-center py-8 text-gray-500">
              暂无规格要求，点击"新增规格要求"开始添加
          </div> :

          <div className="space-y-4">
              {(requirements || []).map((req) =>
            <div
              key={req.id}
              className="border rounded-lg p-4 hover:bg-gray-50 transition-colors">

                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <h3 className="font-semibold text-lg">
                          {req.material_name}
                        </h3>
                        {getRequirementLevelBadge(req.requirement_level)}
                        {req.material_code &&
                    <Badge variant="outline">{req.material_code}</Badge>
                    }
                      </div>
                      <p className="text-sm text-gray-600 mb-2">
                        <span className="font-medium">规格要求:</span>{" "}
                        {req.specification}
                      </p>
                      {req.brand &&
                  <p className="text-sm text-gray-500">
                          <span className="font-medium">品牌:</span> {req.brand}
                          {req.model &&
                    <span className="ml-4">
                              <span className="font-medium">型号:</span>{" "}
                              {req.model}
                    </span>
                    }
                  </p>
                  }
                      {req.remark &&
                  <p className="text-sm text-gray-500 mt-2">
                          {req.remark}
                  </p>
                  }
                    </div>
                    <div className="flex items-center gap-2">
                      <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => openEditDialog(req)}>

                        <Edit3 className="w-4 h-4" />
                      </Button>
                      <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDelete(req.id)}>

                        <Trash2 className="w-4 h-4 text-red-500" />
                      </Button>
                    </div>
                  </div>
            </div>
            )}
          </div>
          }
        </CardContent>
      </Card>

      {/* 创建/编辑对话框 */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {editingRequirement ? "编辑规格要求" : "新增规格要求"}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>项目ID *</Label>
              <Input
                type="number"
                value={formData.project_id}
                onChange={(e) =>
                setFormData({ ...formData, project_id: e.target.value })
                }
                placeholder="请输入项目ID" />

            </div>
            <div>
              <Label>物料名称 *</Label>
              <Input
                value={formData.material_name}
                onChange={(e) =>
                setFormData({ ...formData, material_name: e.target.value })
                }
                placeholder="请输入物料名称" />

            </div>
            <div>
              <Label>规格型号 *</Label>
              <Textarea
                value={formData.specification}
                onChange={(e) =>
                setFormData({ ...formData, specification: e.target.value })
                }
                placeholder="请输入规格型号要求"
                rows={3} />

            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>物料编码</Label>
                <Input
                  value={formData.material_code}
                  onChange={(e) =>
                  setFormData({ ...formData, material_code: e.target.value })
                  }
                  placeholder="可选" />

              </div>
              <div>
                <Label>要求级别</Label>
                <Select
                  value={formData.requirement_level}
                  onValueChange={(value) =>
                  setFormData({ ...formData, requirement_level: value })
                  }>

                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="REQUIRED">必需</SelectItem>
                    <SelectItem value="OPTIONAL">可选</SelectItem>
                    <SelectItem value="STRICT">严格</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>品牌</Label>
                <Input
                  value={formData.brand}
                  onChange={(e) =>
                  setFormData({ ...formData, brand: e.target.value })
                  }
                  placeholder="可选" />

              </div>
              <div>
                <Label>型号</Label>
                <Input
                  value={formData.model}
                  onChange={(e) =>
                  setFormData({ ...formData, model: e.target.value })
                  }
                  placeholder="可选" />

              </div>
            </div>
            <div>
              <Label>备注</Label>
              <Textarea
                value={formData.remark}
                onChange={(e) =>
                setFormData({ ...formData, remark: e.target.value })
                }
                placeholder="可选"
                rows={2} />

            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowCreateDialog(false)}>

              取消
            </Button>
            <Button onClick={editingRequirement ? handleUpdate : handleCreate}>
              {editingRequirement ? "更新" : "创建"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>);

}