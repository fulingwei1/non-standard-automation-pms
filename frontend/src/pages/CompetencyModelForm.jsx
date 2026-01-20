/**
 * Competency Model Form - 能力模型表单
 * 用于创建和编辑岗位能力模型
 */
import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useForm } from "react-hook-form";
import { motion } from "framer-motion";
import { ArrowLeft, Save, X, Plus, Trash2, AlertCircle } from "lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle } from
"../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue } from
"../components/ui/select";
import { qualificationApi } from "../services/api";
import { toast } from "../components/ui/toast";
import { fadeIn } from "../lib/animations";

export default function CompetencyModelForm() {
  const navigate = useNavigate();
  const { id } = useParams();
  const isEdit = !!id;
  const [loading, setLoading] = useState(false);
  const [_model, setModel] = useState(null);
  const [levels, setLevels] = useState([]);

  const {
    register: _register,
    handleSubmit,
    formState: { errors },
    setValue,
    watch
  } = useForm({
    defaultValues: {
      position_type: "",
      position_subtype: "",
      level_id: "",
      competency_dimensions: {}
    }
  });

  useEffect(() => {
    loadLevels();
    if (isEdit) {
      loadModel();
    } else {
      // 初始化默认维度
      initializeDefaultDimensions();
    }
  }, [id]);

  const loadLevels = async () => {
    try {
      const response = await qualificationApi.getLevels({
        page: 1,
        page_size: 100
      });
      if (response.data?.code === 200) {
        setLevels(response.data.data?.items || []);
      }
    } catch (error) {
      console.error("加载等级列表失败:", error);
    }
  };

  const loadModel = async () => {
    try {
      const response = await qualificationApi.getModelById(id);
      if (response.data?.code === 200) {
        const modelData = response.data.data;
        if (modelData) {
          setModel(modelData);
          setValue("position_type", modelData.position_type);
          setValue("position_subtype", modelData.position_subtype || "");
          setValue("level_id", modelData.level_id);
          setValue(
            "competency_dimensions",
            modelData.competency_dimensions || {}
          );
        }
      }
    } catch (error) {
      console.error("加载能力模型失败:", error);
      toast.error("加载能力模型失败");
    }
  };

  const initializeDefaultDimensions = () => {
    const defaultDimensions = {
      technical_skills: {
        name: "专业技能",
        weight: 40,
        items: []
      },
      business_skills: {
        name: "业务能力",
        weight: 25,
        items: []
      },
      communication_skills: {
        name: "沟通协作",
        weight: 20,
        items: []
      },
      learning_skills: {
        name: "学习成长",
        weight: 15,
        items: []
      }
    };
    setValue("competency_dimensions", defaultDimensions);
  };

  const onSubmit = async (data) => {
    // 验证权重总和为100
    const dimensions = data.competency_dimensions || {};
    const totalWeight = Object.values(dimensions).reduce((sum, dim) => {
      return sum + (dim.weight || 0);
    }, 0);

    if (Math.abs(totalWeight - 100) > 0.01) {
      toast.error(`各维度权重总和必须为100%，当前为${totalWeight.toFixed(1)}%`);
      return;
    }

    setLoading(true);
    try {
      if (isEdit) {
        await qualificationApi.updateModel(id, data);
        toast.success("能力模型更新成功");
      } else {
        await qualificationApi.createModel(data);
        toast.success("能力模型创建成功");
      }
      navigate("/qualifications");
    } catch (error) {
      console.error("保存失败:", error);
      toast.error(error.response?.data?.detail || "保存失败");
    } finally {
      setLoading(false);
    }
  };

  const positionType = watch("position_type");
  const competencyDimensions = watch("competency_dimensions") || {};
  const totalWeight = Object.values(competencyDimensions).reduce(
    (sum, dim) => sum + (dim?.weight || 0),
    0
  );

  const addDimensionItem = (dimensionKey) => {
    const dimensions = { ...competencyDimensions };
    if (!dimensions[dimensionKey]) {
      dimensions[dimensionKey] = {
        name: "",
        weight: 0,
        items: []
      };
    }
    dimensions[dimensionKey].items.push({
      name: "",
      description: "",
      score_range: [0, 100]
    });
    setValue("competency_dimensions", dimensions);
  };

  const removeDimensionItem = (dimensionKey, itemIndex) => {
    const dimensions = { ...competencyDimensions };
    if (dimensions[dimensionKey]?.items) {
      dimensions[dimensionKey].items.splice(itemIndex, 1);
      setValue("competency_dimensions", dimensions);
    }
  };

  const updateDimensionItem = (dimensionKey, itemIndex, field, value) => {
    const dimensions = { ...competencyDimensions };
    if (dimensions[dimensionKey]?.items?.[itemIndex]) {
      dimensions[dimensionKey].items[itemIndex][field] = value;
      setValue("competency_dimensions", dimensions);
    }
  };

  const dimensionTemplates = {
    ENGINEER: [
    "technical_skills",
    "business_skills",
    "communication_skills",
    "learning_skills",
    "project_management_skills"],

    SALES: [
    "business_skills",
    "customer_service_skills",
    "communication_skills",
    "learning_skills"],

    CUSTOMER_SERVICE: [
    "customer_service_skills",
    "business_skills",
    "communication_skills",
    "learning_skills"],

    WORKER: [
    "technical_skills",
    "quality_skills",
    "efficiency_skills",
    "learning_skills"]

  };

  const dimensionLabels = {
    technical_skills: "专业技能",
    business_skills: "业务能力",
    communication_skills: "沟通协作",
    learning_skills: "学习成长",
    project_management_skills: "项目管理",
    customer_service_skills: "客户服务",
    quality_skills: "质量意识",
    efficiency_skills: "效率能力"
  };

  const availableDimensions = dimensionTemplates[positionType] || [];

  return (
    <motion.div
      variants={fadeIn}
      initial="hidden"
      animate="show"
      className="space-y-6">

      <PageHeader
        title={isEdit ? "编辑能力模型" : "新建能力模型"}
        description={isEdit ? "修改能力模型信息" : "创建新的岗位能力模型"}
        icon={ArrowLeft}
        onBack={() => navigate("/qualifications")} />


      <Card>
        <CardHeader>
          <CardTitle>基本信息</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* 岗位类型 */}
              <div className="space-y-2">
                <Label htmlFor="position_type">
                  岗位类型 <span className="text-red-500">*</span>
                </Label>
                <Select
                  value={positionType}
                  onValueChange={(value) => {
                    setValue("position_type", value);
                    setValue("position_subtype", "");
                    initializeDefaultDimensions();
                  }}>

                  <SelectTrigger id="position_type">
                    <SelectValue placeholder="选择岗位类型" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ENGINEER">工程师</SelectItem>
                    <SelectItem value="SALES">销售</SelectItem>
                    <SelectItem value="CUSTOMER_SERVICE">客服</SelectItem>
                    <SelectItem value="WORKER">生产工人</SelectItem>
                  </SelectContent>
                </Select>
                {errors.position_type &&
                <p className="text-sm text-red-500 flex items-center gap-1">
                    <AlertCircle className="h-4 w-4" />
                    {errors.position_type.message}
                </p>
                }
              </div>

              {/* 岗位子类型（仅工程师） */}
              {positionType === "ENGINEER" &&
              <div className="space-y-2">
                  <Label htmlFor="position_subtype">岗位子类型</Label>
                  <Select
                  value={watch("position_subtype")}
                  onValueChange={(value) =>
                  setValue("position_subtype", value)
                  }>

                    <SelectTrigger id="position_subtype">
                      <SelectValue placeholder="选择子类型（可选）" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="__empty__">通用</SelectItem>
                      <SelectItem value="ME">机械工程师</SelectItem>
                      <SelectItem value="EE">电气工程师</SelectItem>
                      <SelectItem value="SW">软件工程师</SelectItem>
                      <SelectItem value="TE">测试工程师</SelectItem>
                    </SelectContent>
                  </Select>
              </div>
              }

              {/* 等级 */}
              <div className="space-y-2">
                <Label htmlFor="level_id">
                  等级 <span className="text-red-500">*</span>
                </Label>
                <Select
                  value={watch("level_id")?.toString()}
                  onValueChange={(value) =>
                  setValue("level_id", parseInt(value))
                  }>

                  <SelectTrigger id="level_id">
                    <SelectValue placeholder="选择等级" />
                  </SelectTrigger>
                  <SelectContent>
                    {levels.map((level) =>
                    <SelectItem key={level.id} value={level.id.toString()}>
                        {level.level_code} - {level.level_name}
                    </SelectItem>
                    )}
                  </SelectContent>
                </Select>
                {errors.level_id &&
                <p className="text-sm text-red-500 flex items-center gap-1">
                    <AlertCircle className="h-4 w-4" />
                    {errors.level_id.message}
                </p>
                }
              </div>
            </div>

            {/* 能力维度配置 */}
            {positionType &&
            <div className="space-y-6 pt-6 border-t">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold">能力维度配置</h3>
                  <p className="text-sm text-gray-500">
                    各维度权重总和必须为 100%
                  </p>
                </div>

                {availableDimensions.map((dimKey) => {
                const dimension = competencyDimensions[dimKey] || {
                  name: dimensionLabels[dimKey],
                  weight: 0,
                  items: []
                };
                const _totalWeight = Object.values(
                  competencyDimensions
                ).reduce((sum, dim) => sum + (dim.weight || 0), 0);

                return (
                  <Card key={dimKey} className="border-2">
                      <CardHeader className="pb-3">
                        <div className="flex items-center justify-between">
                          <CardTitle className="text-base">
                            {dimensionLabels[dimKey]}
                          </CardTitle>
                          <div className="flex items-center gap-2">
                            <Input
                            type="number"
                            value={dimension.weight || 0}
                            onChange={(e) => {
                              const dimensions = { ...competencyDimensions };
                              dimensions[dimKey] = {
                                ...dimension,
                                weight: parseFloat(e.target.value) || 0
                              };
                              setValue("competency_dimensions", dimensions);
                            }}
                            className="w-20"
                            min="0"
                            max="100"
                            step="0.1" />

                            <span className="text-sm text-gray-500">%</span>
                          </div>
                        </div>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        {/* 能力项列表 */}
                        {dimension.items?.map((item, itemIndex) =>
                      <div
                        key={itemIndex}
                        className="flex gap-2 p-3 border rounded-lg">

                            <div className="flex-1 grid grid-cols-2 gap-2">
                              <Input
                            placeholder="能力项名称"
                            value={item.name || ""}
                            onChange={(e) =>
                            updateDimensionItem(
                              dimKey,
                              itemIndex,
                              "name",
                              e.target.value
                            )
                            } />

                              <Input
                            placeholder="能力项描述"
                            value={item.description || ""}
                            onChange={(e) =>
                            updateDimensionItem(
                              dimKey,
                              itemIndex,
                              "description",
                              e.target.value
                            )
                            } />

                            </div>
                            <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() =>
                          removeDimensionItem(dimKey, itemIndex)
                          }>

                              <Trash2 className="h-4 w-4 text-red-500" />
                            </Button>
                      </div>
                      )}

                        <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => addDimensionItem(dimKey)}>

                          <Plus className="h-4 w-4 mr-2" />
                          添加能力项
                        </Button>
                      </CardContent>
                  </Card>);

              })}

                {/* 权重总和提示 */}
                <div className="p-4 bg-blue-50 rounded-lg">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">权重总和</span>
                    <span
                    className={`text-lg font-bold ${Math.abs(totalWeight - 100) < 0.01 ? "text-green-600" : "text-red-600"}`}>

                      {totalWeight.toFixed(1)}%
                    </span>
                  </div>
                  {Math.abs(totalWeight - 100) >= 0.01 &&
                <p className="text-xs text-red-500 mt-1">
                      各维度权重总和必须为 100%
                </p>
                }
                </div>
            </div>
            }

            {/* 操作按钮 */}
            <div className="flex justify-end gap-4 pt-4 border-t">
              <Button
                type="button"
                variant="outline"
                onClick={() => navigate("/qualifications")}
                disabled={loading}>

                <X className="h-4 w-4 mr-2" />
                取消
              </Button>
              <Button type="submit" disabled={loading || !positionType}>
                <Save className="h-4 w-4 mr-2" />
                {loading ? "保存中..." : "保存"}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </motion.div>);

}
