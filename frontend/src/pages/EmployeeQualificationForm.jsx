/**
 * Employee Qualification Form - 员工任职资格认证表单
 * 用于认证员工任职资格和查看详情
 */
import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useForm } from "react-hook-form";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  Save,
  X,
  TrendingUp } from
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
import { Label } from "../components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue } from
"../components/ui/select";
import { Badge } from "../components/ui/badge";
import { CompetencyRadarChart } from "../components/qualification/CompetencyRadarChart";
import { QualificationTrendChart } from "../components/qualification/QualificationTrendChart";
import { qualificationApi, employeeApi } from "../services/api";
import { toast } from "../components/ui/toast";
import { fadeIn } from "../lib/animations";
import { formatDate } from "../lib/utils";

export default function EmployeeQualificationForm() {
  const navigate = useNavigate();
  const { employeeId, action } = useParams();
  const isCertify = action === "certify";
  const isPromote = action === "promote";
  const isView = !action || action === "view";
  const [loading, setLoading] = useState(false);
  const [qualification, setQualification] = useState(null);
  const [levels, setLevels] = useState([]);
  const [assessments, setAssessments] = useState([]);
  const [employees, setEmployees] = useState([]);

  const {
    register,
    handleSubmit,
    formState: { errors: _errors },
    setValue,
    watch
  } = useForm({
    defaultValues: {
      employee_id: employeeId ? parseInt(employeeId) : "",
      position_type: "",
      level_id: "",
      assessment_details: {},
      certified_date: "",
      valid_until: ""
    }
  });

  useEffect(() => {
    loadLevels();
    loadEmployees();
    if (employeeId && !isCertify) {
      loadQualification();
      loadAssessments();
    }
  }, [employeeId, action]);

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

  const loadEmployees = async () => {
    try {
      const response = await employeeApi.list({ page: 1, page_size: 100 });
      if (response.data?.code === 200) {
        setEmployees(response.data.data?.items || []);
      } else if (response.data?.data) {
        // 兼容不同的响应格式
        setEmployees(
          Array.isArray(response.data.data) ? response.data.data : []
        );
      }
    } catch (error) {
      console.error("加载员工列表失败:", error);
      setEmployees([]);
    }
  };

  const loadQualification = async () => {
    try {
      const response =
      await qualificationApi.getEmployeeQualification(employeeId);
      if (response.data?.code === 200) {
        const qualData = response.data.data;
        setQualification(qualData);
        setValue("position_type", qualData.position_type);
        setValue("level_id", qualData.current_level_id);
        setValue("assessment_details", qualData.assessment_details || {});
        setValue("certified_date", qualData.certified_date || "");
        setValue("valid_until", qualData.valid_until || "");
      }
    } catch (error) {
      console.error("加载任职资格失败:", error);
    }
  };

  const loadAssessments = async () => {
    try {
      const response = await qualificationApi.getAssessments(employeeId);
      if (response.data?.code === 200) {
        setAssessments(response.data.data?.items || []);
      }
    } catch (error) {
      console.error("加载评估历史失败:", error);
    }
  };

  const onSubmit = async (data) => {
    setLoading(true);
    try {
      if (isPromote) {
        const response = await qualificationApi.promoteEmployee(employeeId, {
          target_level_id: data.level_id,
          assessment_details: data.assessment_details,
          assessment_period: new Date().toISOString().slice(0, 7)
        });
        if (response.data?.code === 200) {
          toast.success("晋升评估完成");
          navigate("/qualifications");
        }
      } else {
        const targetEmployeeId = employeeId || data.employee_id;
        await qualificationApi.certifyEmployee(targetEmployeeId, {
          position_type: data.position_type,
          level_id: data.level_id,
          assessment_details: data.assessment_details,
          certified_date: data.certified_date || undefined,
          valid_until: data.valid_until || undefined
        });
        toast.success("员工认证成功");
        navigate("/qualifications");
      }
    } catch (error) {
      console.error("保存失败:", error);
      toast.error(error.response?.data?.detail || "保存失败");
    } finally {
      setLoading(false);
    }
  };

  const positionType = watch("position_type");
  const levelId = watch("level_id");
  const assessmentDetails = watch("assessment_details") || {};

  // 获取能力模型
  const [competencyModel, setCompetencyModel] = useState(null);
  useEffect(() => {
    if (positionType && levelId) {
      loadCompetencyModel();
    }
  }, [positionType, levelId]);

  const loadCompetencyModel = async () => {
    try {
      const response = await qualificationApi.getModel(positionType, levelId);
      if (response.data?.code === 200) {
        setCompetencyModel(response.data.data);
      }
    } catch (error) {
      console.error("加载能力模型失败:", error);
    }
  };

  const updateScore = (dimensionKey, score) => {
    const details = { ...assessmentDetails };
    if (!details[dimensionKey]) {
      details[dimensionKey] = { score: 0, items: {} };
    }
    details[dimensionKey].score = score;
    setValue("assessment_details", details);
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

  const competencyDimensions = competencyModel?.competency_dimensions || {};

  if (isView && qualification) {
    // 查看模式
    return (
      <motion.div
        variants={fadeIn}
        initial="hidden"
        animate="show"
        className="space-y-6">

        <PageHeader
          title="员工任职资格详情"
          description={`员工 #${employeeId} 的任职资格信息`}
          icon={ArrowLeft}
          onBack={() => navigate("/qualifications")} />


        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* 基本信息 */}
          <Card>
            <CardHeader>
              <CardTitle>基本信息</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label className="text-gray-500">员工ID</Label>
                <p className="text-lg font-semibold">
                  {qualification.employee_id}
                </p>
              </div>
              <div>
                <Label className="text-gray-500">岗位类型</Label>
                <p className="text-lg">{qualification.position_type}</p>
              </div>
              <div>
                <Label className="text-gray-500">当前等级</Label>
                <Badge className="mt-1">
                  {qualification.level?.level_code} -{" "}
                  {qualification.level?.level_name}
                </Badge>
              </div>
              <div>
                <Label className="text-gray-500">认证日期</Label>
                <p>
                  {qualification.certified_date ?
                  formatDate(qualification.certified_date) :
                  "-"}
                </p>
              </div>
              <div>
                <Label className="text-gray-500">有效期至</Label>
                <p>
                  {qualification.valid_until ?
                  formatDate(qualification.valid_until) :
                  "-"}
                </p>
              </div>
              <div>
                <Label className="text-gray-500">状态</Label>
                <Badge
                  className={
                  qualification.status === "APPROVED" ?
                  "bg-green-100 text-green-800" :
                  ""
                  }>

                  {qualification.status}
                </Badge>
              </div>
            </CardContent>
          </Card>

          {/* 能力维度雷达图 */}
          <Card>
            <CardHeader>
              <CardTitle>能力维度分析</CardTitle>
            </CardHeader>
            <CardContent>
              {qualification.assessment_details &&
              Object.keys(qualification.assessment_details).length > 0 ?
              <CompetencyRadarChart data={qualification.assessment_details} /> :

              <div className="flex items-center justify-center h-64 text-gray-400">
                  暂无评估数据
              </div>
              }
            </CardContent>
          </Card>
        </div>

        {/* 评估历史趋势 */}
        {assessments.length > 0 &&
        <Card>
            <CardHeader>
              <CardTitle>评估历史趋势</CardTitle>
            </CardHeader>
            <CardContent>
              <QualificationTrendChart
              data={assessments.map((a) => ({
                date: a.assessed_at || a.assessment_period,
                total_score: a.total_score,
                result: a.result,
                period: a.assessment_period
              }))} />

            </CardContent>
        </Card>
        }

        {/* 操作按钮 */}
        <div className="flex justify-end gap-4">
          <Button variant="outline" onClick={() => navigate("/qualifications")}>
            <X className="h-4 w-4 mr-2" />
            返回
          </Button>
          <Button
            onClick={() =>
            navigate(`/qualifications/employees/${employeeId}/promote`)
            }>

            <TrendingUp className="h-4 w-4 mr-2" />
            晋升评估
          </Button>
        </div>
      </motion.div>);

  }

  // 认证/晋升模式
  return (
    <motion.div
      variants={fadeIn}
      initial="hidden"
      animate="show"
      className="space-y-6">

      <PageHeader
        title={isPromote ? "员工晋升评估" : "员工任职资格认证"}
        description={
        isPromote ? "评估员工是否满足晋升条件" : "为员工认证任职资格"
        }
        icon={ArrowLeft}
        onBack={() => navigate("/qualifications")} />


      <Card>
        <CardHeader>
          <CardTitle>基本信息</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            {!employeeId &&
            <div className="space-y-2">
                <Label htmlFor="employee_id">
                  选择员工 <span className="text-red-500">*</span>
                </Label>
                <Select
                value={watch("employee_id")?.toString()}
                onValueChange={(value) =>
                setValue("employee_id", parseInt(value))
                }>

                  <SelectTrigger id="employee_id">
                    <SelectValue placeholder="选择员工" />
                  </SelectTrigger>
                  <SelectContent>
                    {employees.map((emp) =>
                  <SelectItem key={emp.id} value={emp.id.toString()}>
                        {emp.employee_code || `E${emp.id}`} -{" "}
                        {emp.name || `员工${emp.id}`}
                  </SelectItem>
                  )}
                  </SelectContent>
                </Select>
            </div>
            }

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <Label htmlFor="position_type">
                  岗位类型 <span className="text-red-500">*</span>
                </Label>
                <Select
                  value={positionType}
                  onValueChange={(value) => setValue("position_type", value)}>

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
              </div>

              <div className="space-y-2">
                <Label htmlFor="level_id">
                  {isPromote ? "目标等级" : "等级"}{" "}
                  <span className="text-red-500">*</span>
                </Label>
                <Select
                  value={levelId?.toString()}
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
              </div>

              {!isPromote &&
              <>
                  <div className="space-y-2">
                    <Label htmlFor="certified_date">认证日期</Label>
                    <Input
                    id="certified_date"
                    type="date"
                    {...register("certified_date")} />

                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="valid_until">有效期至</Label>
                    <Input
                    id="valid_until"
                    type="date"
                    {...register("valid_until")} />

                  </div>
              </>
              }
            </div>

            {/* 能力维度评分 */}
            {positionType && levelId && competencyModel &&
            <div className="space-y-4 pt-6 border-t">
                <h3 className="text-lg font-semibold">能力维度评分</h3>
                <p className="text-sm text-gray-500">
                  根据能力模型要求，对各维度进行评分（0-100分）
                </p>

                {Object.entries(competencyDimensions).map(
                ([key, dimension]) =>
                <Card key={key} className="border">
                      <CardHeader className="pb-3">
                        <div className="flex items-center justify-between">
                          <CardTitle className="text-base">
                            {dimension.name || dimensionLabels[key]}
                          </CardTitle>
                          <div className="flex items-center gap-2">
                            <Input
                          type="number"
                          min="0"
                          max="100"
                          value={assessmentDetails[key]?.score || 0}
                          onChange={(e) =>
                          updateScore(
                            key,
                            parseFloat(e.target.value) || 0
                          )
                          }
                          className="w-24" />

                            <span className="text-sm text-gray-500">分</span>
                          </div>
                        </div>
                        <p className="text-xs text-gray-500 mt-1">
                          权重: {dimension.weight}%
                        </p>
                      </CardHeader>
                      {dimension.items && dimension.items.length > 0 &&
                  <CardContent>
                          <div className="space-y-2">
                            {dimension.items.map((item, itemIndex) =>
                      <div
                        key={itemIndex}
                        className="flex items-center justify-between p-2 bg-gray-50 rounded">

                                <div>
                                  <p className="text-sm font-medium">
                                    {item.name}
                                  </p>
                                  {item.description &&
                          <p className="text-xs text-gray-500">
                                      {item.description}
                          </p>
                          }
                                </div>
                                <Input
                          type="number"
                          min="0"
                          max="100"
                          value={
                          assessmentDetails[key]?.items?.[
                          item.name] ||
                          0
                          }
                          onChange={(e) => {
                            const details = { ...assessmentDetails };
                            if (!details[key])
                            {details[key] = { score: 0, items: {} };}
                            if (!details[key].items)
                            {details[key].items = {};}
                            details[key].items[item.name] =
                            parseFloat(e.target.value) || 0;
                            setValue("assessment_details", details);
                          }}
                          className="w-20" />

                      </div>
                      )}
                          </div>
                  </CardContent>
                  }
                </Card>

              )}

                {/* 雷达图预览 */}
                {Object.keys(assessmentDetails).length > 0 &&
              <Card>
                    <CardHeader>
                      <CardTitle>能力维度预览</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <CompetencyRadarChart data={assessmentDetails} />
                    </CardContent>
              </Card>
              }
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
              <Button
                type="submit"
                disabled={loading || !positionType || !levelId}>

                <Save className="h-4 w-4 mr-2" />
                {loading ?
                "提交中..." :
                isPromote ?
                "提交晋升评估" :
                "提交认证"}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </motion.div>);

}