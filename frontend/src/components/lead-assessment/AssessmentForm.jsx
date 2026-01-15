/**
 * Assessment Form Component
 * 线索评估表单 - 详细的线索评分和评估表单
 */

import { useState, useMemo, useEffect } from "react";
import { motion } from "framer-motion";
import {
  ChevronLeft,
  ChevronRight,
  Save,
  RefreshCw,
  TrendingUp,
  BarChart3,
  Target,
  AlertCircle,
  CheckCircle,
  Calculator,
  Info
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Badge } from "../../components/ui/badge";
import { Progress } from "../../components/ui/progress";
import { Input } from "../../components/ui/input";
import { Label } from "../../components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../components/ui/select";
import {
  RadioGroup,
  RadioGroupItem,
} from "../../components/ui/radio-group";
import { Checkbox } from "../../components/ui/checkbox";
import {
  Textarea,
} from "../../components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "../../components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../../components/ui/tabs";
import { Alert, AlertDescription } from "../../components/ui/alert";
import { cn } from "../../lib/utils";
import {
  SCORING_CATEGORIES,
  ASSESSMENT_QUESTIONS,
  SCORE_THRESHOLDS,
  FOLLOW_UP_STRATEGIES,
  DECISION_TIMELINES,
  BUDGET_RANGES,
  LEAD_TYPES,
  INDUSTRIES,
  LEAD_SOURCES,
  LEAD_PRIORITIES,
  LEAD_STATUSES
} from "./leadAssessmentConstants";

export const AssessmentForm = ({
  lead,
  isOpen = false,
  onClose = null,
  onSubmit = null,
  onSaveDraft = null,
  onChange = null,
  className = ""
}) => {
  const [activeTab, setActiveTab] = useState("assessment");
  const [formData, setFormData] = useState({});
  const [scores, setScores] = useState({});
  const [isCalculating, setIsCalculating] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [formErrors, setFormErrors] = useState({});
  const [draftSaved, setDraftSaved] = useState(false);

  // 初始化表单数据
  useEffect(() => {
    if (lead) {
      const initialData = {
        // 基础信息
        source: lead.source || "",
        industry: lead.industry || "",
        customerType: lead.customerType || "new",
        companyType: lead.companyType || "",
        description: lead.description || "",

        // 项目信息
        projectName: lead.projectName || "",
        projectType: lead.projectType || "",
        application: lead.application || "",

        // 联系信息
        contactName: lead.contactName || "",
        contactTitle: lead.contactTitle || "",
        contactPhone: lead.contactPhone || "",
        contactEmail: lead.contactEmail || "",

        // 预算信息
        budgetRange: lead.budgetRange || "",
        budgetEstimate: lead.budgetEstimate || "",

        // 时间信息
        decisionTimeline: lead.decisionTimeline || "",
        projectStartDate: lead.projectStartDate || "",
        projectDuration: lead.projectDuration || "",

        // 评估问题
        assessmentQuestions: lead.assessmentQuestions || {}
      };

      setFormData(initialData);
    }
  }, [lead]);

  // 计算各部分分数
  const calculateCategoryScore = useMemo(() => {
    return (category, questionData) => {
      let totalScore = 0;
      let totalWeight = 0;

      if (!questionData || !ASSESSMENT_QUESTIONS[category]) {
        return 0;
      }

      ASSESSMENT_QUESTIONS[category].forEach(question => {
        const answer = questionData[question.id];
        if (answer !== undefined && answer !== null) {
          let questionScore = 0;

          switch (question.type) {
            case 'boolean':
              questionScore = answer ? question.weight * 5 : 0;
              break;
            case 'rating':
              questionScore = (answer / 5) * question.weight * 5;
              break;
            case 'select':
              const option = question.options.find(opt => opt.value === answer);
              questionScore = option ? option.score : 0;
              break;
            default:
              questionScore = answer * question.weight;
          }

          totalScore += questionScore;
          totalWeight += question.weight;
        }
      });

      // 将 0-5 的评分标准转换为 0-100 的百分制，便于与进度条/阈值配置一致
      return totalWeight > 0 ? Math.round(((totalScore / totalWeight) * 20) * 100) / 100 : 0;
    };
  }, []);

  // 计算总分
  const totalScore = useMemo(() => {
    let weightedSum = 0;
    let totalWeight = 0;

    SCORING_CATEGORIES.forEach(category => {
      const categoryScore = calculateCategoryScore(category.id, formData.assessmentQuestions);
      const weightedScore = categoryScore * (category.weight / 100);

      weightedSum += weightedScore;
      totalWeight += category.weight / 100;

      setScores(prev => ({
        ...prev,
        [category.id]: categoryScore,
        [`${category.id}_weighted`]: weightedScore
      }));
    });

    const finalScore = totalWeight > 0 ? Math.round((weightedSum / totalWeight) * 100) / 100 : 0;
    setScores(prev => ({ ...prev, total: finalScore }));

    return finalScore;
  }, [formData.assessmentQuestions, calculateCategoryScore]);

  // 获取评分等级
  const getScoreLevel = useMemo(() => {
    return Object.values(SCORE_THRESHOLDS).find(threshold => {
      const score = totalScore;
      if (threshold.min && threshold.max) {
        return score >= threshold.min && score <= threshold.max;
      } else if (threshold.min) {
        return score >= threshold.min;
      } else {
        return score <= threshold.max;
      }
    }) || SCORE_THRESHOLDS.average;
  }, [totalScore]);

  // 获取跟进策略
  const getFollowUpStrategy = useMemo(() => {
    return FOLLOW_UP_STRATEGIES.find(strategy => {
      const score = totalScore;
      return score >= strategy.scoreRange[0] && score <= strategy.scoreRange[1];
    }) || FOLLOW_UP_STRATEGIES[FOLLOW_UP_STRATEGIES.length - 1];
  }, [totalScore]);

  // 处理表单字段变化
  const handleFieldChange = (field, value) => {
    setFormData(prev => {
      const updatedData = { ...prev, [field]: value };
      if (onChange) onChange(updatedData);
      return updatedData;
    });
  };

  // 处理评估问题变化
  const handleQuestionChange = (categoryId, questionId, value) => {
    const updatedQuestions = {
      ...formData.assessmentQuestions,
      [categoryId]: {
        ...formData.assessmentQuestions[categoryId],
        [questionId]: value
      }
    };

    setFormData(prev => ({
      ...prev,
      assessmentQuestions: updatedQuestions
    }));
  };

  // 验证表单
  const validateForm = () => {
    const errors = {};

    // 必填字段验证
    if (!formData.contactName) {
      errors.contactName = "联系人姓名不能为空";
    }
    if (!formData.contactPhone && !formData.contactEmail) {
      errors.contact = "至少需要填写联系电话或邮箱";
    }
    if (!formData.industry) {
      errors.industry = "请选择行业领域";
    }
    if (!formData.decisionTimeline) {
      errors.decisionTimeline = "请选择决策时间";
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  // 计算总分
  const calculateTotalScore = async () => {
    setIsCalculating(true);

    // 模拟计算过程
    await new Promise(resolve => setTimeout(resolve, 800));

    setIsCalculating(false);
    setShowResults(true);
  };

  // 提交表单
  const handleSubmit = async () => {
    if (!validateForm()) {
      return;
    }

    const assessmentData = {
      ...formData,
      assessmentQuestions: formData.assessmentQuestions,
      totalScore,
      scoreLevel: getScoreLevel.label,
      followUpStrategy: getFollowUpStrategy
    };

    if (onSubmit) {
      await onSubmit(assessmentData);
    }

    setShowResults(false);
    if (onClose) onClose();
  };

  // 保存草稿
  const handleSaveDraft = async () => {
    const draftData = {
      ...formData,
      assessmentQuestions: formData.assessmentQuestions,
      savedAt: new Date().toISOString()
    };

    if (onSaveDraft) {
      await onSaveDraft(draftData);
    }

    setDraftSaved(true);
    setTimeout(() => setDraftSaved(false), 3000);
  };

  // 渲染评估问题
  const renderAssessmentQuestions = (categoryId) => {
    const questions = ASSESSMENT_QUESTIONS[categoryId];
    if (!questions) return null;

    return questions.map((question, index) => {
      const questionId = `${categoryId}_${index}`;
      const currentValue = formData.assessmentQuestions?.[categoryId]?.[question.id];

      return (
        <div key={questionId} className="space-y-3">
          <div className="flex items-start gap-2">
            <Label className="text-sm font-medium leading-relaxed">
              {question.question}
            </Label>
            <Info className="h-4 w-4 text-slate-500 mt-0.5 flex-shrink-0" />
          </div>

          {question.type === 'boolean' && (
            <RadioGroup
              value={currentValue || ""}
              onValueChange={(value) => handleQuestionChange(categoryId, question.id, value === 'true')}
              className="flex gap-4"
            >
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="true" id={`${questionId}_yes`} />
                <Label htmlFor={`${questionId}_yes`} className="text-sm">是</Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="false" id={`${questionId}_no`} />
                <Label htmlFor={`${questionId}_no`} className="text-sm">否</Label>
              </div>
            </RadioGroup>
          )}

          {question.type === 'rating' && (
            <div className="space-y-2">
              <RadioGroup
                value={currentValue || ""}
                onValueChange={(value) => handleQuestionChange(categoryId, question.id, parseInt(value))}
                className="flex gap-4"
              >
                {[1, 2, 3, 4, 5].map(rating => (
                  <div key={rating} className="flex items-center space-x-2">
                    <RadioGroupItem value={rating.toString()} id={`${questionId}_${rating}`} />
                    <Label htmlFor={`${questionId}_${rating}`} className="text-sm flex items-center gap-1">
                      {[...Array(rating)].map((_, i) => (
                        <span key={i} className="text-amber-500">★</span>
                      ))}
                    </Label>
                  </div>
                ))}
              </RadioGroup>
              <div className="text-xs text-slate-500 text-right">
                权重: {(question.weight * 100).toFixed(0)}%
              </div>
            </div>
          )}

          {question.type === 'select' && (
            <Select
              value={currentValue || ""}
              onValueChange={(value) => handleQuestionChange(categoryId, question.id, value)}
            >
              <SelectTrigger>
                <SelectValue placeholder="请选择..." />
              </SelectTrigger>
              <SelectContent>
                {question.options.map(option => (
                  <SelectItem key={option.value} value={option.value}>
                    <div className="flex items-center justify-between w-full">
                      <span>{option.label}</span>
                      {option.score && (
                        <Badge variant="secondary" className="ml-2">
                          +{option.score}分
                        </Badge>
                      )}
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        </div>
      );
    });
  };

  // 渲染评分摘要
  const renderScoreSummary = () => {
    return (
      <div className="space-y-4">
        <div className="text-center">
          <div className="text-4xl font-bold mb-2" style={{ color: getScoreLevel.color }}>
            {totalScore}
          </div>
          <Badge variant="outline" className="text-lg px-4 py-2" style={{ borderColor: getScoreLevel.color, color: getScoreLevel.color }}>
            {getScoreLevel.label}
          </Badge>
        </div>

        <div className="space-y-3">
          {SCORING_CATEGORIES.map(category => {
            const score = scores[category.id] || 0;
            const weightedScore = scores[`${category.id}_weighted`] || 0;

            return (
              <div key={category.id} className="space-y-1">
                <div className="flex justify-between text-sm">
                  <span className="font-medium">{category.name}</span>
                  <span className="text-slate-600">{score.toFixed(1)}分 ({(category.weight)}%)</span>
                </div>
                <Progress value={score} className="h-2" />
              </div>
            );
          })}
        </div>

        <Alert>
          <TrendingUp className="h-4 w-4" />
          <AlertDescription>
            <div className="space-y-2">
              <div className="font-medium">建议跟进策略:</div>
              <div>
                <span className="font-medium">{getFollowUpStrategy.strategy}</span>
                <div className="text-sm text-slate-600 mt-1">
                  {getFollowUpStrategy.description}
                </div>
              </div>
            </div>
          </AlertDescription>
        </Alert>
      </div>
    );
  };

  // 表单标签页
  const tabs = [
    { value: "basic", label: "基础信息" },
    { value: "project", label: "项目详情" },
    { value: "assessment", label: "评估问答" },
    { value: "summary", label: "评分结果" }
  ];

  if (!isOpen) return null;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-5xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            线索评估
            {lead && (
              <Badge variant="outline" className="ml-2">
                {lead.contactName} - {lead.companyName}
              </Badge>
            )}
          </DialogTitle>
        </DialogHeader>

        <div className={cn("space-y-6", className)}>
          {/* 进度指示器 */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm text-slate-600">
              <Calculator className="h-4 w-4" />
              评估进度
            </div>
            <Progress value={activeTab === "summary" ? 100 : (tabs.findIndex(t => t.value === activeTab) + 1) * 25} className="flex-1 mx-4" />
            <div className="text-sm font-medium">
              {activeTab === "summary" && "计算完成"}
              {activeTab !== "summary" && `${tabs.findIndex(t => t.value === activeTab) + 1}/${tabs.length}`}
            </div>
          </div>

          {/* 表单标签页 */}
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-4">
              {tabs.map(tab => (
                <TabsTrigger
                  key={tab.value}
                  value={tab.value}
                  className="text-xs"
                >
                  {tab.label}
                </TabsTrigger>
              ))}
            </TabsList>

            {/* 基础信息 */}
            <TabsContent value="basic" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">联系信息</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>联系人姓名 *</Label>
                      <Input
                        value={formData.contactName || ""}
                        onChange={(e) => handleFieldChange("contactName", e.target.value)}
                        placeholder="请输入联系人姓名"
                      />
                      {formErrors.contactName && (
                        <div className="text-sm text-red-600">{formErrors.contactName}</div>
                      )}
                    </div>
                    <div className="space-y-2">
                      <Label>职位</Label>
                      <Input
                        value={formData.contactTitle || ""}
                        onChange={(e) => handleFieldChange("contactTitle", e.target.value)}
                        placeholder="请输入职位"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>联系电话</Label>
                      <Input
                        value={formData.contactPhone || ""}
                        onChange={(e) => handleFieldChange("contactPhone", e.target.value)}
                        placeholder="请输入联系电话"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>联系邮箱</Label>
                      <Input
                        type="email"
                        value={formData.contactEmail || ""}
                        onChange={(e) => handleFieldChange("contactEmail", e.target.value)}
                        placeholder="请输入联系邮箱"
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">公司信息</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label>公司名称</Label>
                    <Input
                      value={formData.companyName || ""}
                      onChange={(e) => handleFieldChange("companyName", e.target.value)}
                      placeholder="请输入公司名称"
                    />
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>公司类型</Label>
                      <Input
                        value={formData.companyType || ""}
                        onChange={(e) => handleFieldChange("companyType", e.target.value)}
                        placeholder="如：国企、外企、民营"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>行业领域 *</Label>
                      <Select value={formData.industry || ""} onValueChange={(value) => handleFieldChange("industry", value)}>
                        <SelectTrigger>
                          <SelectValue placeholder="请选择行业领域" />
                        </SelectTrigger>
                        <SelectContent>
                          {INDUSTRIES.map(industry => (
                            <SelectItem key={industry.value} value={industry.value}>
                              <div className="flex items-center justify-between w-full">
                                <span>{industry.label}</span>
                                <Badge variant="secondary" className="ml-2">
                                  优先级: {industry.priority}
                                </Badge>
                              </div>
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      {formErrors.industry && (
                        <div className="text-sm text-red-600">{formErrors.industry}</div>
                      )}
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label>线索来源</Label>
                    <Select value={formData.source || ""} onValueChange={(value) => handleFieldChange("source", value)}>
                      <SelectTrigger>
                        <SelectValue placeholder="请选择线索来源" />
                      </SelectTrigger>
                      <SelectContent>
                        {LEAD_SOURCES.map(source => (
                          <SelectItem key={source.value} value={source.value}>
                            <div className="flex items-center justify-between w-full">
                              <span>{source.label}</span>
                              <Badge variant="secondary" className="ml-2">
                                {source.score}分
                              </Badge>
                            </div>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* 项目详情 */}
            <TabsContent value="project" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">项目基本信息</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label>项目名称</Label>
                    <Input
                      value={formData.projectName || ""}
                      onChange={(e) => handleFieldChange("projectName", e.target.value)}
                      placeholder="请输入项目名称"
                    />
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>项目类型</Label>
                      <Input
                        value={formData.projectType || ""}
                        onChange={(e) => handleFieldChange("projectType", e.target.value)}
                        placeholder="如：ICT测试设备、老化设备等"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>客户类型</Label>
                      <Select value={formData.customerType || ""} onValueChange={(value) => handleFieldChange("customerType", value)}>
                        <SelectTrigger>
                          <SelectValue placeholder="请选择客户类型" />
                        </SelectTrigger>
                        <SelectContent>
                          {LEAD_TYPES.map(type => (
                            <SelectItem key={type.value} value={type.value}>
                              <div className="flex items-center justify-between w-full">
                                <span>{type.label}</span>
                                {type.score && <Badge variant="secondary" className="ml-2">+{type.score}分</Badge>}
                              </div>
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label>项目应用领域</Label>
                    <Textarea
                      value={formData.application || ""}
                      onChange={(e) => handleFieldChange("application", e.target.value)}
                      placeholder="请描述项目应用领域"
                      rows={3}
                    />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">预算与时间</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label>预算范围</Label>
                    <Select value={formData.budgetRange || ""} onValueChange={(value) => handleFieldChange("budgetRange", value)}>
                      <SelectTrigger>
                        <SelectValue placeholder="请选择预算范围" />
                      </SelectTrigger>
                      <SelectContent>
                        {BUDGET_RANGES.map(budget => (
                          <SelectItem key={budget.value} value={budget.value}>
                            <div>
                              <div className="font-medium">{budget.label}</div>
                              <div className="text-sm text-slate-600">{budget.description}</div>
                            </div>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>预计预算（元）</Label>
                      <Input
                        type="number"
                        value={formData.budgetEstimate || ""}
                        onChange={(e) => handleFieldChange("budgetEstimate", e.target.value)}
                        placeholder="请输入预计预算"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>决策时间 *</Label>
                      <Select value={formData.decisionTimeline || ""} onValueChange={(value) => handleFieldChange("decisionTimeline", value)}>
                        <SelectTrigger>
                          <SelectValue placeholder="请选择决策时间" />
                        </SelectTrigger>
                        <SelectContent>
                          {DECISION_TIMELINES.map(timeline => (
                            <SelectItem key={timeline.value} value={timeline.value}>
                              <div className="flex items-center justify-between w-full">
                                <span>{timeline.label}</span>
                                <Badge variant="secondary" className="ml-2">
                                  {timeline.score}分
                                </Badge>
                              </div>
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      {formErrors.decisionTimeline && (
                        <div className="text-sm text-red-600">{formErrors.decisionTimeline}</div>
                      )}
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>项目开始日期</Label>
                      <Input
                        type="date"
                        value={formData.projectStartDate || ""}
                        onChange={(e) => handleFieldChange("projectStartDate", e.target.value)}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>预计项目周期</Label>
                      <Select value={formData.projectDuration || ""} onValueChange={(value) => handleFieldChange("projectDuration", value)}>
                        <SelectTrigger>
                          <SelectValue placeholder="请选择项目周期" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="short">3个月以内</SelectItem>
                          <SelectItem value="medium">3-6个月</SelectItem>
                          <SelectItem value="long">6-12个月</SelectItem>
                          <SelectItem value="very_long">12个月以上</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* 评估问答 */}
            <TabsContent value="assessment" className="space-y-6">
              {SCORING_CATEGORIES.map((category, index) => (
                <Card key={category.id}>
                  <CardHeader>
                    <CardTitle className="text-lg flex items-center justify-between">
                      <span>{index + 1}. {category.name}</span>
                      <Badge variant="outline">
                        权重: {category.weight}%
                      </Badge>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    {renderAssessmentQuestions(category.id)}
                  </CardContent>
                </Card>
              ))}

              <div className="flex justify-between items-center">
                <Button variant="outline" onClick={() => setActiveTab("basic")}>
                  <ChevronLeft className="mr-2 h-4 w-4" />
                  上一步
                </Button>
                <Button onClick={calculateTotalScore} disabled={isCalculating}>
                  <BarChart3 className="mr-2 h-4 w-4" />
                  {isCalculating ? "计算中..." : "计算评分"}
                </Button>
                <Button onClick={() => setActiveTab("summary")}>
                  下一步
                  <ChevronRight className="ml-2 h-4 w-4" />
                </Button>
              </div>
            </TabsContent>

            {/* 评分结果 */}
            <TabsContent value="summary" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <Target className="h-5 w-5" />
                    评估结果
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {renderScoreSummary()}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">综合建议</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <Alert>
                    <CheckCircle className="h-4 w-4" />
                    <AlertDescription>
                      <div className="space-y-3">
                        <div>
                          <strong>跟进频率:</strong> {getFollowUpStrategy.frequency === 'daily' ? '每天' :
                            getFollowUpStrategy.frequency === 'every_2_days' ? '每两天' :
                            getFollowUpStrategy.frequency === 'weekly' ? '每周' :
                            getFollowUpStrategy.frequency === 'biweekly' ? '每两周' : '每月'}
                        </div>
                        <div>
                          <strong>推荐联系方式:</strong> {getFollowUpStrategy.contactMethod}
                        </div>
                        <div className="text-sm text-slate-600">
                          {getFollowUpStrategy.description}
                        </div>
                      </div>
                    </AlertDescription>
                  </Alert>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>

          {/* 操作按钮 */}
          <div className="flex justify-between items-center border-t border-slate-200 pt-4">
            <div className="flex gap-2">
              <Button variant="outline" onClick={handleSaveDraft}>
                <Save className="mr-2 h-4 w-4" />
                保存草稿
              </Button>
            </div>

            {draftSaved && (
              <Alert className="max-w-sm">
                <CheckCircle className="h-4 w-4" />
                <AlertDescription className="text-sm">
                  草稿已保存
                </AlertDescription>
              </Alert>
            )}

            <div className="flex gap-2">
              <Button variant="outline" onClick={onClose}>
                取消
              </Button>
              <Button onClick={handleSubmit}>
                提交评估
              </Button>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default AssessmentForm;
