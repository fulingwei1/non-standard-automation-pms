/**
 * Qualification Level Form - 任职资格等级表单
 * 用于创建和编辑任职资格等级
 */
import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useForm } from "react-hook-form";
import { motion } from "framer-motion";
import { ArrowLeft, Save, X, AlertCircle } from "lucide-react";
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
import { Textarea } from "../components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue } from
"../components/ui/select";
import { Checkbox } from "../components/ui/checkbox";
import { qualificationApi } from "../services/api";
import { toast } from "../components/ui/toast";
import { fadeIn } from "../lib/animations";

export default function QualificationLevelForm() {
  const navigate = useNavigate();
  const { id } = useParams();
  const isEdit = !!id;
  const [loading, setLoading] = useState(false);
  const [_level, setLevel] = useState(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
    setValue,
    watch
  } = useForm({
    defaultValues: {
      level_code: "",
      level_name: "",
      level_order: 1,
      role_type: "",
      description: "",
      is_active: true
    }
  });

  useEffect(() => {
    if (isEdit) {
      loadLevel();
    }
  }, [id]);

  const loadLevel = async () => {
    try {
      const response = await qualificationApi.getLevel(id);
      if (response.data?.code === 200) {
        const levelData = response.data.data;
        setLevel(levelData);
        setValue("level_code", levelData.level_code);
        setValue("level_name", levelData.level_name);
        setValue("level_order", levelData.level_order);
        setValue("role_type", levelData.role_type || "");
        setValue("description", levelData.description || "");
        setValue("is_active", levelData.is_active);
      }
    } catch (error) {
      console.error("加载等级失败:", error);
      toast.error("加载等级信息失败");
    }
  };

  const onSubmit = async (data) => {
    setLoading(true);
    try {
      if (isEdit) {
        await qualificationApi.updateLevel(id, data);
        toast.success("等级更新成功");
      } else {
        await qualificationApi.createLevel(data);
        toast.success("等级创建成功");
      }
      navigate("/qualifications");
    } catch (error) {
      console.error("保存失败:", error);
      toast.error(error.response?.data?.detail || "保存失败");
    } finally {
      setLoading(false);
    }
  };

  const isActive = watch("is_active");

  return (
    <motion.div
      variants={fadeIn}
      initial="hidden"
      animate="show"
      className="space-y-6">

      <PageHeader
        title={isEdit ? "编辑任职资格等级" : "新建任职资格等级"}
        description={isEdit ? "修改等级信息" : "创建新的任职资格等级"}
        icon={ArrowLeft}
        onBack={() => navigate("/qualifications")} />


      <Card>
        <CardHeader>
          <CardTitle>等级信息</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* 等级编码 */}
              <div className="space-y-2">
                <Label htmlFor="level_code">
                  等级编码 <span className="text-red-500">*</span>
                </Label>
                <Input
                  id="level_code"
                  {...register("level_code", {
                    required: "等级编码不能为空",
                    pattern: {
                      value: /^[A-Z_]+$/,
                      message: "等级编码只能包含大写字母和下划线"
                    }
                  })}
                  placeholder="如: ASSISTANT, JUNIOR, MIDDLE, SENIOR, EXPERT"
                  disabled={isEdit} />

                {errors.level_code &&
                <p className="text-sm text-red-500 flex items-center gap-1">
                    <AlertCircle className="h-4 w-4" />
                    {errors.level_code.message}
                  </p>
                }
                <p className="text-xs text-gray-500">
                  建议使用: ASSISTANT(助理级), JUNIOR(初级), MIDDLE(中级),
                  SENIOR(高级), EXPERT(专家级)
                </p>
              </div>

              {/* 等级名称 */}
              <div className="space-y-2">
                <Label htmlFor="level_name">
                  等级名称 <span className="text-red-500">*</span>
                </Label>
                <Input
                  id="level_name"
                  {...register("level_name", {
                    required: "等级名称不能为空"
                  })}
                  placeholder="如: 助理级、初级、中级、高级、专家级" />

                {errors.level_name &&
                <p className="text-sm text-red-500 flex items-center gap-1">
                    <AlertCircle className="h-4 w-4" />
                    {errors.level_name.message}
                  </p>
                }
              </div>

              {/* 排序顺序 */}
              <div className="space-y-2">
                <Label htmlFor="level_order">
                  排序顺序 <span className="text-red-500">*</span>
                </Label>
                <Input
                  id="level_order"
                  type="number"
                  {...register("level_order", {
                    required: "排序顺序不能为空",
                    valueAsNumber: true,
                    min: { value: 1, message: "排序顺序必须大于0" }
                  })}
                  placeholder="1-5" />

                {errors.level_order &&
                <p className="text-sm text-red-500 flex items-center gap-1">
                    <AlertCircle className="h-4 w-4" />
                    {errors.level_order.message}
                  </p>
                }
                <p className="text-xs text-gray-500">
                  数字越小，等级越低（1=最低，5=最高）
                </p>
              </div>

              {/* 适用角色类型 */}
              <div className="space-y-2">
                <Label htmlFor="role_type">适用角色类型</Label>
                <Select
                  value={watch("role_type")}
                  onValueChange={(value) => setValue("role_type", value)}>

                  <SelectTrigger id="role_type">
                    <SelectValue placeholder="选择适用角色（留空表示通用）" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__empty__">通用（所有角色）</SelectItem>
                    <SelectItem value="ENGINEER">工程师</SelectItem>
                    <SelectItem value="SALES">销售</SelectItem>
                    <SelectItem value="CUSTOMER_SERVICE">客服</SelectItem>
                    <SelectItem value="WORKER">生产工人</SelectItem>
                  </SelectContent>
                </Select>
                <p className="text-xs text-gray-500">
                  留空表示该等级适用于所有角色类型
                </p>
              </div>
            </div>

            {/* 等级描述 */}
            <div className="space-y-2">
              <Label htmlFor="description">等级描述</Label>
              <Textarea
                id="description"
                {...register("description")}
                placeholder="描述该等级的能力要求、经验要求等..."
                rows={4} />

            </div>

            {/* 启用状态 */}
            <div className="flex items-center space-x-2">
              <Checkbox
                id="is_active"
                checked={isActive}
                onCheckedChange={(checked) => setValue("is_active", checked)} />

              <Label htmlFor="is_active" className="cursor-pointer">
                启用该等级
              </Label>
            </div>

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
              <Button type="submit" disabled={loading}>
                <Save className="h-4 w-4 mr-2" />
                {loading ? "保存中..." : "保存"}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </motion.div>);

}