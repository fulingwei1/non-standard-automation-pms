/**
 * Opportunity Card Component
 * 商机卡片组件 - 显示单个商机信息
 */

import { useState } from "react";
import { motion } from "framer-motion";
import {
  MoreHorizontal,
  Edit3,
  Trash2,
  User,
  Building,
  Phone,
  Mail,
  Calendar,
  Clock,
  ArrowRight,
  ExternalLink,
  Copy
} from "lucide-react";
import { Card, CardContent, CardHeader } from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Badge } from "../../components/ui/badge";
import { Progress } from "../../components/ui/progress";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../../components/ui/dialog";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "../../components/ui/dropdown-menu";
import { cn } from "../../lib/utils";
import {
  getStageConfig,
  getPriorityConfig,
  getSourceConfig,
  getTypeConfig,
  getSizeConfig,
  formatOpportunityAmount,
  formatOpportunityDate,
  calculateOpportunityHealth,
  getOpportunityHealthStatus,
  opportunityStageFlow
} from "@/lib/constants/opportunityBoard";

/**
 * 商机卡片组件属性
 */
export const OpportunityCard = ({
  opportunity,
  onEdit,
  onDelete,
  onView,
  onStageChange,
  isSelected,
  onSelect,
  className,
  showActions = true,
  compact = false
}) => {
  const [showDetails, setShowDetails] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  // 获取配置
  const stageConfig = getStageConfig(opportunity.stage);
  const priorityConfig = getPriorityConfig(opportunity.priority);
  const sourceConfig = getSourceConfig(opportunity.source);
  const typeConfig = getTypeConfig(opportunity.type);
  const sizeConfig = getSizeConfig(opportunity.size);

  // 计算健康度
  const health = calculateOpportunityHealth(opportunity);
  const healthStatus = getOpportunityHealthStatus(health);

  // 计算预计成交时间
  const expectedCloseDate = opportunity.expected_close_date ? new Date(opportunity.expected_close_date) : null;
  const today = new Date();
  const daysToClose = expectedCloseDate
    ? Math.ceil((expectedCloseDate - today) / (1000 * 60 * 60 * 24))
    : null;

  // 处理阶段变更
  const handleStageChange = (newStage) => {
    if (onStageChange) {
      onStageChange(opportunity.id, newStage);
    }
  };

  // 获取下一个阶段
  const getNextStage = () => {
    const currentIndex = opportunityStageFlow.indexOf(opportunity.stage);
    if (currentIndex < opportunityStageFlow.length - 1) {
      return opportunityStageFlow[currentIndex + 1];
    }
    return null;
  };

  // 获取上一个阶段
  const getPreviousStage = () => {
    const currentIndex = opportunityStageFlow.indexOf(opportunity.stage);
    if (currentIndex > 0) {
      return opportunityStageFlow[currentIndex - 1];
    }
    return null;
  };

  // 渲染健康度指示器
  const renderHealthIndicator = () => {
    const healthColors = {
      excellent: "bg-green-500",
      good: "bg-green-400",
      warning: "bg-amber-400",
      critical: "bg-red-400"
    };

    return (
      <div className="flex items-center gap-2">
        <div className={cn(
          "w-2 h-2 rounded-full",
          healthColors[healthStatus]
        )} />
        <span className="text-xs text-gray-500">
          {health}%
        </span>
      </div>
    );
  };

  // 渲染预计成交时间
  const renderExpectedClose = () => {
    if (!daysToClose) {return null;}

    let timeText;
    let timeColor;

    if (daysToClose < 0) {
      timeText = `已过期 ${Math.abs(daysToClose)} 天`;
      timeColor = "text-red-600";
    } else if (daysToClose <= 7) {
      timeText = `${daysToClose} 天`;
      timeColor = "text-red-600";
    } else if (daysToClose <= 30) {
      timeText = `${daysToClose} 天`;
      timeColor = "text-amber-600";
    } else {
      timeText = `${daysToClose} 天`;
      timeColor = "text-gray-600";
    }

    return (
      <div className={cn("flex items-center gap-1", timeColor)}>
        <Clock className="w-3 h-3" />
        <span className="text-xs">{timeText}</span>
      </div>
    );
  };

  // 渲染优先级标签
  const renderPriorityBadge = () => {
    return (
      <Badge variant="secondary" className={cn(
        "text-xs",
        priorityConfig.badgeColor
      )}>
        {priorityConfig.label}
      </Badge>
    );
  };

  // 渲染卡片头部
  const renderCardHeader = () => (
    <div className="flex items-start justify-between">
      <div className="flex-1">
        <div className="flex items-center gap-2 mb-2">
          <h3 className="font-semibold text-sm line-clamp-1">
            {opportunity.name}
          </h3>
          {renderPriorityBadge()}
        </div>

        <div className="flex items-center gap-4 text-xs text-gray-500">
          {renderHealthIndicator()}
          {renderExpectedClose()}
        </div>
      </div>

      {showActions && (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => onView(opportunity)}>
              <ExternalLink className="mr-2 h-4 w-4" />
              查看详情
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => onEdit(opportunity)}>
              <Edit3 className="mr-2 h-4 w-4" />
              编辑商机
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => handleStageChange(getNextStage())}>
              <ArrowRight className="mr-2 h-4 w-4" />
              下一个阶段
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => handleStageChange(getPreviousStage())}>
              <ArrowRight className="mr-2 h-4 w-4" className="rotate-180" />
              上一个阶段
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => setShowDetails(true)}>
              <Copy className="mr-2 h-4 w-4" />
              复制链接
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => onDelete(opportunity)}>
              <Trash2 className="mr-2 h-4 w-4 text-red-500" />
              删除商机
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      )}
    </div>
  );

  // 渲染卡片内容
  const renderCardContent = () => (
    <div className="space-y-3">
      {/* 客户信息 */}
      <div className="space-y-1">
        <div className="flex items-center gap-2 text-sm">
          <Building className="w-4 h-4 text-gray-400" />
          <span className="font-medium truncate">
            {opportunity.company_name}
          </span>
        </div>
        <div className="flex items-center gap-4 text-xs text-gray-500">
          <div className="flex items-center gap-1">
            <User className="w-3 h-3" />
            <span>{opportunity.contact_person}</span>
          </div>
          <div className="flex items-center gap-1">
            <Phone className="w-3 h-3" />
            <span>{opportunity.contact_phone}</span>
          </div>
          <div className="flex items-center gap-1">
            <Mail className="w-3 h-3" />
            <span className="truncate">{opportunity.contact_email}</span>
          </div>
        </div>
      </div>

      {/* 商机信息 */}
      <div className="grid grid-cols-2 gap-2 text-xs">
        <div>
          <div className="text-gray-500">预计金额</div>
          <div className="font-semibold">
            {formatOpportunityAmount(opportunity.expected_amount)}
          </div>
        </div>
        <div>
          <div className="text-gray-500">商机类型</div>
          <div className="font-semibold">{typeConfig.label}</div>
        </div>
        <div>
          <div className="text-gray-500">商机规模</div>
          <Badge variant="outline" className={sizeConfig.color}>
            {sizeConfig.label}
          </Badge>
        </div>
        <div>
          <div className="text-gray-500">来源</div>
          <div className="font-semibold">{sourceConfig.label}</div>
        </div>
      </div>

      {/* 进度信息 */}
      <div className="space-y-2">
        <div className="flex justify-between text-xs">
          <span className="text-gray-500">成交概率</span>
          <span className="font-medium">
            {opportunity.win_probability || 0}%
          </span>
        </div>
        <Progress value={opportunity.win_probability || 0} className="h-2" />
      </div>

      {/* 最后联系 */}
      {opportunity.last_contact_date && (
        <div className="flex items-center gap-2 text-xs text-gray-500">
          <Calendar className="w-3 h-3" />
          <span>
            最后联系: {formatOpportunityDate(opportunity.last_contact_date)}
          </span>
        </div>
      )}
    </div>
  );

  // 渲染阶段操作按钮
  const renderStageActions = () => {
    const nextStage = getNextStage();
    const prevStage = getPreviousStage();

    return (
      <div className="flex gap-1">
        {prevStage && (
          <Button
            variant="ghost"
            size="sm"
            className="h-6 px-2 text-xs"
            onClick={() => handleStageChange(prevStage)}
          >
            上一步
          </Button>
        )}
        {nextStage && (
          <Button
            size="sm"
            className="h-6 px-2 text-xs"
            onClick={() => handleStageChange(nextStage)}
          >
            下一步
          </Button>
        )}
      </div>
    );
  };

  // 卡片拖拽配置
  const dragConfig = {
    whileHover: { y: -2 },
    whileTap: { scale: 0.98 },
    drag: true,
    dragConstraints: { left: 0, right: 0 },
    dragElastic: 0.2,
    onDragStart: () => setIsDragging(true),
    onDragEnd: () => setIsDragging(false)
  };

  return (
    <>
      <motion.div
        {...dragConfig}
        className={cn(
          "group relative cursor-move",
          className,
          isDragging && "opacity-50",
          isSelected && "ring-2 ring-blue-500 ring-offset-2"
        )}
        onClick={() => onSelect && onSelect(opportunity)}
      >
        {/* 阶段标签 */}
        <div className={cn(
          "absolute -top-2 -right-2 px-2 py-1 rounded-full text-xs font-medium text-white",
          stageConfig.color
        )}>
          {stageConfig.label}
        </div>

        <Card className={cn(
          "h-full border transition-all duration-200",
          "hover:shadow-md",
          compact ? "p-3" : "p-4",
          isSelected && "shadow-md border-blue-200"
        )}>
          {/* 卡片头部 */}
          <CardHeader className="pb-2" className="pb-2">
            {renderCardHeader()}
          </CardHeader>

          {/* 卡片内容 */}
          <CardContent className="pt-0">
            {renderCardContent()}
          </CardContent>

          {/* 底部操作 */}
          {showActions && (
            <div className="flex items-center justify-between pt-3 border-t">
              <div className="flex items-center gap-1 text-xs text-gray-500">
                <span>创建于:</span>
                <span>{formatOpportunityDate(opportunity.created_at)}</span>
              </div>
              {renderStageActions()}
            </div>
          )}
        </Card>
      </motion.div>

      {/* 详情对话框 */}
      <Dialog open={showDetails} onOpenChange={setShowDetails}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>{opportunity.name}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            {/* 完整商机信息 */}
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <div className="text-gray-500">客户公司</div>
                <div className="font-medium">{opportunity.company_name}</div>
              </div>
              <div>
                <div className="text-gray-500">联系人</div>
                <div>{opportunity.contact_person}</div>
              </div>
              <div>
                <div className="text-gray-500">联系电话</div>
                <div>{opportunity.contact_phone}</div>
              </div>
              <div>
                <div className="text-gray-500">联系邮箱</div>
                <div>{opportunity.contact_email}</div>
              </div>
              <div>
                <div className="text-gray-500">预计金额</div>
                <div className="font-semibold text-lg">
                  {formatOpportunityAmount(opportunity.expected_amount)}
                </div>
              </div>
              <div>
                <div className="text-gray-500">成交概率</div>
                <div className="font-semibold">{opportunity.win_probability}%</div>
              </div>
            </div>

            {/* 描述信息 */}
            {opportunity.description && (
              <div>
                <div className="text-gray-500 mb-2">商机描述</div>
                <div className="text-sm text-gray-600">
                  {opportunity.description}
                </div>
              </div>
            )}

            {/* 备注信息 */}
            {opportunity.notes && (
              <div>
                <div className="text-gray-500 mb-2">备注</div>
                <div className="text-sm text-gray-600">
                  {opportunity.notes}
                </div>
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
};

export default OpportunityCard;