/**
 * Shortage Report New - 新建缺料上报
 * 车间人员、仓管、PMC等角色可以创建缺料上报
 */

import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  Package,
  AlertTriangle,
  Save,
  X,
  Search,
} from "lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
  Button,
  Input,
  Label,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Textarea,
} from "../components/ui";
import { fadeIn } from "../lib/animations";
import { shortageApi, projectApi, materialApi } from "../services/api";

const urgentLevels = [
  { value: "NORMAL", label: "普通" },
  { value: "URGENT", label: "紧急" },
  { value: "CRITICAL", label: "特急" },
];

export default function ShortageReportNew() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [projects, setProjects] = useState([]);
  const [materials, setMaterials] = useState([]);
  const [searchKeyword, setSearchKeyword] = useState("");
  const [formData, setFormData] = useState({
    project_id: "",
    machine_id: "",
    work_order_id: "",
    material_id: "",
    required_qty: "",
    shortage_qty: "",
    urgent_level: "NORMAL",
    report_location: "",
    remark: "",
  });
  const [errors, setErrors] = useState({});

  useEffect(() => {
    loadProjects();
    loadMaterials();
  }, []);

  useEffect(() => {
    // 当搜索关键词变化时，重新加载物料列表
    loadMaterials();
  }, [searchKeyword]);

  const loadProjects = async () => {
    try {
      const res = await projectApi.list({ page: 1, page_size: 100 });
      setProjects(res.data.items || []);
    } catch (error) {
      console.error("加载项目列表失败", error);
    }
  };

  const loadMaterials = async () => {
    try {
      const params = {
        page: 1,
        page_size: 100,
      };
      if (searchKeyword) {
        // 如果后端支持关键词搜索，可以添加keyword参数
        // params.keyword = searchKeyword
      }
      const res = await materialApi.list(params);
      const materialList = res.data?.items || res.data || [];

      // 如果有搜索关键词，前端过滤
      let filteredMaterials = materialList;
      if (searchKeyword) {
        const keyword = searchKeyword.toLowerCase();
        filteredMaterials = materialList.filter(
          (m) =>
            ((m.material_code || "").toLowerCase().includes(keyword)) ||
            ((m.material_name || "").toLowerCase().includes(keyword)),
        );
      }

      setMaterials(filteredMaterials);
    } catch (error) {
      console.error("加载物料列表失败", error);
      setMaterials([]);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    // 验证
    const newErrors = {};
    if (!formData.project_id) {newErrors.project_id = "请选择项目";}
    if (!formData.material_id) {newErrors.material_id = "请选择物料";}
    if (!formData.required_qty || parseFloat(formData.required_qty) <= 0) {
      newErrors.required_qty = "请输入有效的需求数量";
    }
    if (!formData.shortage_qty || parseFloat(formData.shortage_qty) <= 0) {
      newErrors.shortage_qty = "请输入有效的缺料数量";
    }
    if (parseFloat(formData.shortage_qty) > parseFloat(formData.required_qty)) {
      newErrors.shortage_qty = "缺料数量不能大于需求数量";
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setLoading(true);
    try {
      const submitData = {
        ...formData,
        project_id: parseInt(formData.project_id),
        machine_id: formData.machine_id ? parseInt(formData.machine_id) : null,
        work_order_id: formData.work_order_id
          ? parseInt(formData.work_order_id)
          : null,
        material_id: parseInt(formData.material_id),
        required_qty: parseFloat(formData.required_qty),
        shortage_qty: parseFloat(formData.shortage_qty),
      };

      const res = await shortageApi.reports.create(submitData);
      alert("缺料上报创建成功！");
      navigate(`/shortage/reports/${res.data.id}`);
    } catch (error) {
      console.error("创建缺料上报失败", error);
      alert("创建失败：" + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: null }));
    }
  };

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={() => navigate("/shortage")}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          返回
        </Button>
        <PageHeader title="新建缺料上报" description="填写缺料信息并提交上报" />
      </div>

      <motion.form
        variants={fadeIn}
        initial="hidden"
        animate="visible"
        onSubmit={handleSubmit}
        className="max-w-4xl"
      >
        <Card>
          <CardHeader>
            <CardTitle>基本信息</CardTitle>
            <CardDescription>选择项目和上报地点</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="project_id" className="required">
                  项目 <span className="text-red-400">*</span>
                </Label>
                <Select
                  value={formData.project_id}
                  onValueChange={(value) => handleChange("project_id", value)}
                >
                  <SelectTrigger
                    id="project_id"
                    className={errors.project_id ? "border-red-400" : ""}
                  >
                    <SelectValue placeholder="请选择项目" />
                  </SelectTrigger>
                  <SelectContent>
                    {projects.map((project) => (
                      <SelectItem key={project.id} value={String(project.id)}>
                        {project.project_name} ({project.project_code})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {errors.project_id && (
                  <div className="text-sm text-red-400 mt-1">
                    {errors.project_id}
                  </div>
                )}
              </div>

              <div>
                <Label htmlFor="report_location">上报地点</Label>
                <Input
                  id="report_location"
                  placeholder="如：装配车间A区"
                  value={formData.report_location}
                  onChange={(e) =>
                    handleChange("report_location", e.target.value)
                  }
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="machine_id">机台（可选）</Label>
                <Input
                  id="machine_id"
                  type="number"
                  placeholder="机台ID"
                  value={formData.machine_id}
                  onChange={(e) => handleChange("machine_id", e.target.value)}
                />
              </div>

              <div>
                <Label htmlFor="work_order_id">工单（可选）</Label>
                <Input
                  id="work_order_id"
                  type="number"
                  placeholder="工单ID"
                  value={formData.work_order_id}
                  onChange={(e) =>
                    handleChange("work_order_id", e.target.value)
                  }
                />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>物料信息</CardTitle>
            <CardDescription>选择缺料物料并填写数量</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="material_id" className="required">
                物料 <span className="text-red-400">*</span>
              </Label>
              <div className="space-y-2">
                <Input
                  id="material_search"
                  placeholder="搜索物料编码或名称..."
                  value={searchKeyword}
                  onChange={(e) => setSearchKeyword(e.target.value)}
                  className="mb-2"
                />
                <Select
                  value={formData.material_id}
                  onValueChange={(value) => handleChange("material_id", value)}
                >
                  <SelectTrigger
                    id="material_id"
                    className={errors.material_id ? "border-red-400" : ""}
                  >
                    <SelectValue placeholder="请选择物料" />
                  </SelectTrigger>
                  <SelectContent className="max-h-[300px]">
                    {materials.length === 0 ? (
                      <SelectItem value="__disabled__" disabled>
                        {searchKeyword ? "未找到匹配的物料" : "暂无物料数据"}
                      </SelectItem>
                    ) : (
                      materials.map((material) => (
                        <SelectItem
                          key={material.id}
                          value={material.id.toString()}
                        >
                          {material.material_code || "N/A"} -{" "}
                          {material.material_name || "未命名物料"}
                        </SelectItem>
                      ))
                    )}
                  </SelectContent>
                </Select>
                {errors.material_id && (
                  <div className="text-sm text-red-400 mt-1">
                    {errors.material_id}
                  </div>
                )}
                <div className="text-xs text-muted-foreground">
                  提示：可以通过物料编码或名称搜索，或从BOM中选择
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="required_qty" className="required">
                  需求数量 <span className="text-red-400">*</span>
                </Label>
                <Input
                  id="required_qty"
                  type="number"
                  step="0.01"
                  min="0"
                  placeholder="0.00"
                  value={formData.required_qty}
                  onChange={(e) => handleChange("required_qty", e.target.value)}
                  className={errors.required_qty ? "border-red-400" : ""}
                />
                {errors.required_qty && (
                  <div className="text-sm text-red-400 mt-1">
                    {errors.required_qty}
                  </div>
                )}
              </div>

              <div>
                <Label htmlFor="shortage_qty" className="required">
                  缺料数量 <span className="text-red-400">*</span>
                </Label>
                <Input
                  id="shortage_qty"
                  type="number"
                  step="0.01"
                  min="0"
                  placeholder="0.00"
                  value={formData.shortage_qty}
                  onChange={(e) => handleChange("shortage_qty", e.target.value)}
                  className={errors.shortage_qty ? "border-red-400" : ""}
                />
                {errors.shortage_qty && (
                  <div className="text-sm text-red-400 mt-1">
                    {errors.shortage_qty}
                  </div>
                )}
              </div>
            </div>

            <div>
              <Label htmlFor="urgent_level">紧急程度</Label>
              <Select
                value={formData.urgent_level}
                onValueChange={(value) => handleChange("urgent_level", value)}
              >
                <SelectTrigger id="urgent_level">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {urgentLevels.map((level) => (
                    <SelectItem key={level.value} value={level.value}>
                      {level.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>备注信息</CardTitle>
            <CardDescription>补充说明缺料情况</CardDescription>
          </CardHeader>
          <CardContent>
            <Textarea
              placeholder="请描述缺料的具体情况、影响等..."
              value={formData.remark}
              onChange={(e) => handleChange("remark", e.target.value)}
              rows={4}
            />
          </CardContent>
        </Card>

        <div className="flex items-center justify-end gap-4">
          <Button
            type="button"
            variant="outline"
            onClick={() => navigate("/shortage")}
            disabled={loading}
          >
            <X className="h-4 w-4 mr-2" />
            取消
          </Button>
          <Button type="submit" disabled={loading}>
            <Save className="h-4 w-4 mr-2" />
            {loading ? "提交中..." : "提交上报"}
          </Button>
        </div>
      </motion.form>
    </div>
  );
}
