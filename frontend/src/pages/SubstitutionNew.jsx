/**
 * Material Substitution New - 新建物料替代申请
 * 创建物料替代申请，需要技术审批和生产审批
 */

import { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  RefreshCw,
  Save,
  X,
  Search,
  AlertTriangle,
  CheckCircle2 } from
"lucide-react";
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
  Textarea } from
"../components/ui";
import { fadeIn } from "../lib/animations";
import { shortageApi, projectApi, materialApi } from "../services/api";

export default function SubstitutionNew() {
  const navigate = useNavigate();
  const location = useLocation();
  const [loading, setLoading] = useState(false);
  const [projects, setProjects] = useState([]);
  const [materials, setMaterials] = useState([]);
  const [searchKeyword, _setSearchKeyword] = useState("");
  const [formData, setFormData] = useState({
    shortage_report_id: location.state?.shortage_report_id || "",
    project_id: location.state?.project_id || "",
    bom_item_id: location.state?.bom_item_id || "",
    original_material_id: "",
    substitute_material_id: "",
    original_qty: "",
    substitute_qty: "",
    substitution_reason: "",
    technical_impact: "",
    cost_impact: "0",
    remark: ""
  });
  const [errors, setErrors] = useState({});

  useEffect(() => {
    loadProjects();
    loadMaterials();
  }, []);

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
      const res = await materialApi.list({
        page: 1,
        page_size: 100,
        is_active: true
      });
      setMaterials(res.data.items || res.data?.items || res.data || []);
    } catch (error) {
      console.error("加载物料列表失败", error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    // 验证
    const newErrors = {};
    if (!formData.project_id) {newErrors.project_id = "请选择项目";}
    if (!formData.original_material_id)
    {newErrors.original_material_id = "请选择原物料";}
    if (!formData.substitute_material_id)
    {newErrors.substitute_material_id = "请选择替代物料";}
    if (formData.original_material_id === formData.substitute_material_id) {
      newErrors.substitute_material_id = "替代物料不能与原物料相同";
    }
    if (!formData.original_qty || parseFloat(formData.original_qty) <= 0) {
      newErrors.original_qty = "请输入有效的原物料数量";
    }
    if (!formData.substitute_qty || parseFloat(formData.substitute_qty) <= 0) {
      newErrors.substitute_qty = "请输入有效的替代物料数量";
    }
    if (!formData.substitution_reason.trim()) {
      newErrors.substitution_reason = "请输入替代原因";
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setLoading(true);
    try {
      const submitData = {
        ...formData,
        shortage_report_id: formData.shortage_report_id ?
        parseInt(formData.shortage_report_id) :
        null,
        project_id: parseInt(formData.project_id),
        bom_item_id: formData.bom_item_id ?
        parseInt(formData.bom_item_id) :
        null,
        original_material_id: parseInt(formData.original_material_id),
        substitute_material_id: parseInt(formData.substitute_material_id),
        original_qty: parseFloat(formData.original_qty),
        substitute_qty: parseFloat(formData.substitute_qty),
        cost_impact: parseFloat(formData.cost_impact) || 0
      };

      const res = await shortageApi.substitutions.create(submitData);
      alert("物料替代申请创建成功！");
      navigate(`/shortage/substitutions/${res.data.id}`);
    } catch (error) {
      console.error("创建物料替代申请失败", error);
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

  const filteredMaterials = (materials || []).filter(
    (m) =>
    !searchKeyword ||
    m.material_code?.toLowerCase().includes(searchKeyword.toLowerCase()) ||
    m.material_name?.toLowerCase().includes(searchKeyword.toLowerCase())
  );

  const originalMaterial = (materials || []).find(
    (m) => m.id === parseInt(formData.original_material_id)
  );
  const substituteMaterial = (materials || []).find(
    (m) => m.id === parseInt(formData.substitute_material_id)
  );

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={() => navigate("/shortage")}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          返回
        </Button>
        <PageHeader
          title="新建物料替代申请"
          description="填写替代信息并提交申请" />

      </div>

      <motion.form
        variants={fadeIn}
        initial="hidden"
        animate="visible"
        onSubmit={handleSubmit}
        className="max-w-4xl">

        <Card>
          <CardHeader>
            <CardTitle>基本信息</CardTitle>
            <CardDescription>选择项目和关联信息</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="project_id" className="required">
                  项目 <span className="text-red-400">*</span>
                </Label>
                <Select
                  value={formData.project_id}
                  onValueChange={(value) => handleChange("project_id", value)}>

                  <SelectTrigger
                    id="project_id"
                    className={errors.project_id ? "border-red-400" : ""}>

                    <SelectValue placeholder="请选择项目" />
                  </SelectTrigger>
                  <SelectContent>
                    {(projects || []).map((project) =>
                    <SelectItem key={project.id} value={String(project.id)}>
                        {project.project_name} ({project.project_code})
                    </SelectItem>
                    )}
                  </SelectContent>
                </Select>
                {errors.project_id &&
                <div className="text-sm text-red-400 mt-1">
                    {errors.project_id}
                </div>
                }
              </div>

              <div>
                <Label htmlFor="shortage_report_id">关联缺料上报（可选）</Label>
                <Input
                  id="shortage_report_id"
                  type="number"
                  placeholder="缺料上报ID"
                  value={formData.shortage_report_id}
                  onChange={(e) =>
                  handleChange("shortage_report_id", e.target.value)
                  } />

              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>物料信息</CardTitle>
            <CardDescription>选择原物料和替代物料</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* 原物料 */}
            <div className="p-4 rounded-lg border border-red-500/20 bg-red-500/5">
              <div className="flex items-center gap-2 mb-3">
                <AlertTriangle className="h-4 w-4 text-red-400" />
                <span className="font-medium text-red-400">原物料（缺料）</span>
              </div>
              <div className="space-y-4">
                <div>
                  <Label htmlFor="original_material_id" className="required">
                    原物料 <span className="text-red-400">*</span>
                  </Label>
                  <Select
                    value={formData.original_material_id}
                    onValueChange={(value) =>
                    handleChange("original_material_id", value)
                    }>

                    <SelectTrigger
                      id="original_material_id"
                      className={
                      errors.original_material_id ? "border-red-400" : ""
                      }>

                      <SelectValue placeholder="请选择原物料" />
                    </SelectTrigger>
                    <SelectContent>
                      {(filteredMaterials || []).map((material) =>
                      <SelectItem
                        key={material.id}
                        value={String(material.id)}>

                          {material.material_code} - {material.material_name}
                      </SelectItem>
                      )}
                    </SelectContent>
                  </Select>
                  {errors.original_material_id &&
                  <div className="text-sm text-red-400 mt-1">
                      {errors.original_material_id}
                  </div>
                  }
                </div>
                {originalMaterial &&
                <div className="text-sm text-muted-foreground">
                    规格：{originalMaterial.specification || "-"} | 单位：
                    {originalMaterial.unit || "-"}
                </div>
                }
                <div>
                  <Label htmlFor="original_qty" className="required">
                    原物料数量 <span className="text-red-400">*</span>
                  </Label>
                  <Input
                    id="original_qty"
                    type="number"
                    step="0.01"
                    min="0"
                    placeholder="0.00"
                    value={formData.original_qty}
                    onChange={(e) =>
                    handleChange("original_qty", e.target.value)
                    }
                    className={errors.original_qty ? "border-red-400" : ""} />

                  {errors.original_qty &&
                  <div className="text-sm text-red-400 mt-1">
                      {errors.original_qty}
                  </div>
                  }
                </div>
              </div>
            </div>

            {/* 替代物料 */}
            <div className="p-4 rounded-lg border border-emerald-500/20 bg-emerald-500/5">
              <div className="flex items-center gap-2 mb-3">
                <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                <span className="font-medium text-emerald-400">替代物料</span>
              </div>
              <div className="space-y-4">
                <div>
                  <Label htmlFor="substitute_material_id" className="required">
                    替代物料 <span className="text-red-400">*</span>
                  </Label>
                  <Select
                    value={formData.substitute_material_id}
                    onValueChange={(value) =>
                    handleChange("substitute_material_id", value)
                    }>

                    <SelectTrigger
                      id="substitute_material_id"
                      className={
                      errors.substitute_material_id ? "border-red-400" : ""
                      }>

                      <SelectValue placeholder="请选择替代物料" />
                    </SelectTrigger>
                    <SelectContent>
                      {filteredMaterials.
                      filter(
                        (m) =>
                        m.id !== parseInt(formData.original_material_id)
                      ).
                      map((material) =>
                      <SelectItem
                        key={material.id}
                        value={String(material.id)}>

                            {material.material_code} - {material.material_name}
                      </SelectItem>
                      )}
                    </SelectContent>
                  </Select>
                  {errors.substitute_material_id &&
                  <div className="text-sm text-red-400 mt-1">
                      {errors.substitute_material_id}
                  </div>
                  }
                </div>
                {substituteMaterial &&
                <div className="text-sm text-muted-foreground">
                    规格：{substituteMaterial.specification || "-"} | 单位：
                    {substituteMaterial.unit || "-"}
                </div>
                }
                <div>
                  <Label htmlFor="substitute_qty" className="required">
                    替代物料数量 <span className="text-red-400">*</span>
                  </Label>
                  <Input
                    id="substitute_qty"
                    type="number"
                    step="0.01"
                    min="0"
                    placeholder="0.00"
                    value={formData.substitute_qty}
                    onChange={(e) =>
                    handleChange("substitute_qty", e.target.value)
                    }
                    className={errors.substitute_qty ? "border-red-400" : ""} />

                  {errors.substitute_qty &&
                  <div className="text-sm text-red-400 mt-1">
                      {errors.substitute_qty}
                  </div>
                  }
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>替代原因和影响</CardTitle>
            <CardDescription>说明替代原因并分析影响</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="substitution_reason" className="required">
                替代原因 <span className="text-red-400">*</span>
              </Label>
              <Textarea
                id="substitution_reason"
                placeholder="请详细说明为什么需要替代此物料..."
                value={formData.substitution_reason}
                onChange={(e) =>
                handleChange("substitution_reason", e.target.value)
                }
                rows={4}
                className={errors.substitution_reason ? "border-red-400" : ""} />

              {errors.substitution_reason &&
              <div className="text-sm text-red-400 mt-1">
                  {errors.substitution_reason}
              </div>
              }
            </div>

            <div>
              <Label htmlFor="technical_impact">技术影响分析</Label>
              <Textarea
                id="technical_impact"
                placeholder="分析替代物料对产品性能、质量、工艺等方面的影响..."
                value={formData.technical_impact}
                onChange={(e) =>
                handleChange("technical_impact", e.target.value)
                }
                rows={4} />

            </div>

            <div>
              <Label htmlFor="cost_impact">成本影响（元）</Label>
              <Input
                id="cost_impact"
                type="number"
                step="0.01"
                placeholder="0.00"
                value={formData.cost_impact}
                onChange={(e) => handleChange("cost_impact", e.target.value)} />

              <div className="text-xs text-muted-foreground mt-1">
                正数表示成本增加，负数表示成本减少
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>备注</CardTitle>
          </CardHeader>
          <CardContent>
            <Textarea
              placeholder="其他需要说明的信息..."
              value={formData.remark}
              onChange={(e) => handleChange("remark", e.target.value)}
              rows={3} />

          </CardContent>
        </Card>

        <div className="flex items-center justify-end gap-4">
          <Button
            type="button"
            variant="outline"
            onClick={() => navigate("/shortage")}
            disabled={loading}>

            <X className="h-4 w-4 mr-2" />
            取消
          </Button>
          <Button type="submit" disabled={loading}>
            <Save className="h-4 w-4 mr-2" />
            {loading ? "提交中..." : "提交申请"}
          </Button>
        </div>
      </motion.form>
    </div>);

}