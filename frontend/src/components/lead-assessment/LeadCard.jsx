/**
 * Lead Card Component
 * 线索信息卡片 - 显示线索基本信息和评估状态
 */

import { useState, useMemo } from "react";
import { motion } from "framer-motion";
import {
  User,
  Building,
  Phone,
  Mail,
  Calendar,
  DollarSign,
  MapPin,
  Tag,
  TrendingUp,
  MoreHorizontal,
  Eye,
  Edit,
  Trash2,
  Star,
  Clock,
  AlertCircle } from
"lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Badge } from "../../components/ui/badge";
import { Button } from "../../components/ui/button";
import { Progress } from "../../components/ui/progress";
import { Avatar, AvatarFallback, AvatarImage } from "../../components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger } from
"../../components/ui/dropdown-menu";
import { cn } from "../../lib/utils";
import {
  LEAD_SOURCES,
  LEAD_TYPES,
  INDUSTRIES,
  LEAD_STATUSES,
  LEAD_PRIORITIES,
  SCORE_THRESHOLDS,
  DECISION_TIMELINES,
  BUDGET_RANGES } from
"./leadAssessmentConstants";

export const LeadCard = ({
  lead,
  onAssess = null,
  onView = null,
  onEdit = null,
  onDelete = null,
  onAssign: _onAssign = null,
  onQuickAction = null,
  showActions = true,
  className = ""
}) => {
  const [_isHovered, setIsHovered] = useState(false);

  // 获取线索来源配置
  const leadSourceConfig = useMemo(() => {
    return LEAD_SOURCES.find((source) => source.value === lead.source) || LEAD_SOURCES[0];
  }, [lead.source]);

  // 获取行业配置
  const industryConfig = useMemo(() => {
    return INDUSTRIES.find((industry) => industry.value === lead.industry) || INDUSTRIES[0];
  }, [lead.industry]);

  // 获取客户类型配置
  const customerTypeConfig = useMemo(() => {
    return LEAD_TYPES.find((type) => type.value === lead.customerType) || LEAD_TYPES[0];
  }, [lead.customerType]);

  // 获取状态配置
  const statusConfig = useMemo(() => {
    return LEAD_STATUSES.find((status) => status.value === lead.status) || LEAD_STATUSES[0];
  }, [lead.status]);

  // 获取优先级配置
  const priorityConfig = useMemo(() => {
    return LEAD_PRIORITIES.find((priority) => priority.value === lead.priority) || LEAD_PRIORITIES[0];
  }, [lead.priority]);

  // 获取评分阈值配置
  const scoreThresholdConfig = useMemo(() => {
    const score = lead.assessmentScore || 0;
    return Object.values(SCORE_THRESHOLDS).find((threshold) => {
      if (threshold.min && threshold.max) {
        return score >= threshold.min && score <= threshold.max;
      } else if (threshold.min) {
        return score >= threshold.min;
      } else {
        return score <= threshold.max;
      }
    }) || SCORE_THRESHOLDS.average;
  }, [lead.assessmentScore]);

  // 获取预算配置
  const budgetConfig = useMemo(() => {
    return BUDGET_RANGES.find((budget) => budget.value === lead.budgetRange) || BUDGET_RANGES[0];
  }, [lead.budgetRange]);

  // 获取决策时间配置
  const decisionTimelineConfig = useMemo(() => {
    return DECISION_TIMELINES.find((timeline) => timeline.value === lead.decisionTimeline) || DECISION_TIMELINES[0];
  }, [lead.decisionTimeline]);

  // 计算健康度指示器
  const healthIndicator = useMemo(() => {
    const score = lead.assessmentScore || 0;
    if (score >= 80) {return { color: 'bg-green-500', label: '优秀' };}
    if (score >= 60) {return { color: 'bg-blue-500', label: '良好' };}
    if (score >= 40) {return { color: 'bg-amber-500', label: '一般' };}
    if (score >= 20) {return { color: 'bg-orange-500', label: '较差' };}
    return { color: 'bg-red-500', label: '很差' };
  }, [lead.assessmentScore]);

  // 格式化联系信息
  const contactInfo = useMemo(() => {
    return {
      name: lead.contactName || '未填写',
      title: lead.contactTitle || '',
      phone: lead.contactPhone || '未填写',
      email: lead.contactEmail || '未填写'
    };
  }, [lead]);

  // 生成公司名称显示
  const companyNameDisplay = useMemo(() => {
    return lead.companyName || '未填写公司名称';
  }, [lead.companyName]);

  // 生成联系人头像
  const generateAvatar = useMemo(() => {
    const name = contactInfo.name;
    if (!name || name === '未填写') {return 'C';}

    const words = name.split(' ').filter((word) => word.length > 0);
    if (words.length === 1) {
      return words[0].substring(0, 2).toUpperCase();
    }
    return words[0][0].toUpperCase() + words[words.length - 1][0].toUpperCase();
  }, [contactInfo.name]);

  // 卡片动画
  const cardVariants = {
    hover: {
      y: -4,
      boxShadow: "0 8px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)"
    },
    tap: {
      scale: 0.98
    }
  };

  // 处理快速操作
  const handleQuickAction = (action, value) => {
    if (onQuickAction) {
      onQuickAction(action, lead, value);
    }
  };

  // 渲染评分指示器
  const renderScoreIndicator = () => {
    if (!lead.assessmentScore) {
      return (
        <div className="flex items-center gap-2 text-slate-500">
          <Clock className="h-4 w-4" />
          <span className="text-sm">待评估</span>
        </div>);

    }

    return (
      <div className="flex items-center gap-2">
        <div className="relative w-12 h-12">
          <Progress
            value={lead.assessmentScore}
            className="h-2" />

          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-xs font-semibold">{lead.assessmentScore}</span>
          </div>
        </div>
        <div className="flex flex-col">
          <span className="text-sm font-medium" style={{ color: scoreThresholdConfig.color }}>
            {scoreThresholdConfig.label}
          </span>
          <span className="text-xs text-slate-500">综合评分</span>
        </div>
      </div>);

  };

  // 渲染健康度指示器
  const renderHealthIndicator = () =>
  <div className="flex items-center gap-2">
      <div className={`w-3 h-3 rounded-full ${healthIndicator.color}`} />
      <span className="text-sm text-slate-600">健康度: {healthIndicator.label}</span>
  </div>;


  return (
    <motion.div
      variants={cardVariants}
      initial="rest"
      whileHover="hover"
      whileTap="tap"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      className={cn(
        "relative bg-white rounded-xl border border-slate-200 transition-all duration-200",
        className
      )}>

      {/* 健康度指示条 */}
      <div className="absolute top-0 left-0 right-0 h-1 rounded-t-xl" style={{ backgroundColor: healthIndicator.color }} />

      <Card className="border-0 shadow-none">
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between">
            {/* 联系人信息 */}
            <div className="flex items-start gap-3 flex-1">
              <Avatar className="h-10 w-10 flex-shrink-0">
                <AvatarImage src={lead.avatarUrl} alt={contactInfo.name} />
                <AvatarFallback className="text-xs font-medium">
                  {generateAvatar}
                </AvatarFallback>
              </Avatar>

              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="font-semibold text-slate-900 truncate">
                    {contactInfo.name}
                  </h3>
                  {lead.isStarred && <Star className="h-4 w-4 text-amber-500 fill-current" />}
                </div>

                {companyNameDisplay &&
                <div className="flex items-center gap-1 mb-1">
                    <Building className="h-3 w-3 text-slate-500" />
                    <span className="text-sm text-slate-600 truncate">
                      {companyNameDisplay}
                    </span>
                </div>
                }

                {contactInfo.title &&
                <div className="text-xs text-slate-500 mb-2">
                    {contactInfo.title}
                </div>
                }

                <div className="flex flex-wrap gap-2">
                  <Badge
                    variant="secondary"
                    style={{ borderColor: statusConfig.color, color: statusConfig.color }}
                    className="text-xs">

                    {statusConfig.label}
                  </Badge>

                  {lead.priority &&
                  <Badge
                    variant="outline"
                    className="text-xs"
                    style={{ borderColor: priorityConfig.color, color: priorityConfig.color }}>

                      {priorityConfig.label}
                  </Badge>
                  }
                </div>
              </div>
            </div>

            {/* 快速操作 */}
            {showActions &&
            <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 w-8 p-0 opacity-60 hover:opacity-100">

                    <MoreHorizontal className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem onClick={() => onView && onView(lead)}>
                    <Eye className="mr-2 h-4 w-4" />
                    查看详情
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => onEdit && onEdit(lead)}>
                    <Edit className="mr-2 h-4 w-4" />
                    编辑线索
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => onAssess && onAssess(lead)}>
                    <TrendingUp className="mr-2 h-4 w-4" />
                    评估线索
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => handleQuickAction('assign', lead)}>
                    <User className="mr-2 h-4 w-4" />
                    分配负责人
                  </DropdownMenuItem>
                  <DropdownMenuItem
                  onClick={() => handleQuickAction('star', lead)}
                  className={lead.isStarred ? "text-amber-600" : ""}>

                    <Star className="mr-2 h-4 w-4" />
                    {lead.isStarred ? "取消星标" : "添加星标"}
                  </DropdownMenuItem>
                  <DropdownMenuItem
                  onClick={() => onDelete && onDelete(lead)}
                  className="text-red-600">

                    <Trash2 className="mr-2 h-4 w-4" />
                    删除线索
                  </DropdownMenuItem>
                </DropdownMenuContent>
            </DropdownMenu>
            }
          </div>
        </CardHeader>

        <CardContent className="pt-0">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            {/* 线索评分 */}
            <div className="flex flex-col gap-1">
              {renderScoreIndicator()}
              {renderHealthIndicator()}
            </div>

            {/* 联系信息 */}
            <div className="flex flex-col gap-2">
              <div className="flex items-center gap-2 text-sm">
                <Phone className="h-4 w-4 text-slate-500" />
                <span className="text-slate-600">{contactInfo.phone}</span>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <Mail className="h-4 w-4 text-slate-500" />
                <span className="text-slate-600">{contactInfo.email}</span>
              </div>
            </div>
          </div>

          {/* 项目信息 */}
          {lead.projectName &&
          <div className="mb-3">
              <div className="text-sm font-medium text-slate-700 mb-1">项目名称</div>
              <div className="text-sm text-slate-900 truncate">
                {lead.projectName}
              </div>
          </div>
          }

          {/* 线索详情 */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-2 text-slate-600">
                <Tag className="h-4 w-4" />
                <span>线索来源</span>
              </div>
              <span className="text-slate-900 font-medium">
                {leadSourceConfig.label} ({leadSourceConfig.score}分)
              </span>
            </div>

            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-2 text-slate-600">
                <MapPin className="h-4 w-4" />
                <span>行业领域</span>
              </div>
              <span className="text-slate-900 font-medium">
                {industryConfig.label}
              </span>
            </div>

            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-2 text-slate-600">
                <DollarSign className="h-4 w-4" />
                <span>预算范围</span>
              </div>
              <span className="text-slate-900 font-medium">
                {budgetConfig.label} {budgetConfig.description && `(${budgetConfig.description})`}
              </span>
            </div>

            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-2 text-slate-600">
                <Calendar className="h-4 w-4" />
                <span>决策时间</span>
              </div>
              <span className="text-slate-900 font-medium">
                {decisionTimelineConfig.label}
              </span>
            </div>

            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-2 text-slate-600">
                <User className="h-4 w-4" />
                <span>客户类型</span>
              </div>
              <span className="text-slate-900 font-medium">
                {customerTypeConfig.label}
              </span>
            </div>
          </div>

          {/* 简短描述 */}
          {lead.description &&
          <div className="mt-3 pt-3 border-t border-slate-100">
              <div className="text-sm text-slate-600 line-clamp-2">
                {lead.description}
              </div>
          </div>
          }
        </CardContent>
      </Card>
    </motion.div>);

};

export default LeadCard;