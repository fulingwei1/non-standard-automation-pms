import React, { useState } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
  Badge,
  Progress,
  Button,
  ScrollArea,
  Separator } from
'@/components/ui';
import {
  PROJECT_STAGES,
  MILESTONE_STATUSES,
  PROJECT_HEALTH } from
'@/lib/constants/projectDetail';
import { format, differenceInDays, isAfter, isBefore as _isBefore } from 'date-fns';
import { zhCN as _zhCN } from 'date-fns/locale';

const MilestoneTracker = ({ project, onStageClick, onAddMilestone }) => {
  const [expandedStage, setExpandedStage] = useState(null);

  // Get stage info by code
  const getStageInfo = (stageCode) => {
    return PROJECT_STAGES.find((stage) => stage.code === stageCode) || PROJECT_STAGES[0];
  };

  // Calculate days difference
  const getDaysDiff = (date1, date2) => {
    if (!date1 || !date2) {return 0;}
    return differenceInDays(new Date(date2), new Date(date1));
  };

  // Check if date is overdue
  const isOverdue = (dueDate, currentDate = new Date()) => {
    return dueDate && isAfter(currentDate, new Date(dueDate));
  };

  // Get milestone status
  const getMilestoneStatus = (milestone) => {
    if (!milestone.target_date) {return MILESTONE_STATUSES.NOT_STARTED;}

    const today = new Date();
    const targetDate = new Date(milestone.target_date);

    if (milestone.completed_at) {
      return MILESTONE_STATUSES.COMPLETED;
    }

    if (isOverdue(targetDate)) {
      return MILESTONE_STATUSES.DELAYED;
    }

    if (isAfter(targetDate, today)) {
      return MILESTONE_STATUSES.NOT_STARTED;
    }

    return MILESTONE_STATUSES.IN_PROGRESS;
  };

  // Get status color
  const getStatusColor = (status) => {
    switch (status) {
      case MILESTONE_STATUSES.COMPLETED.code:
        return '#10B981';
      case MILESTONE_STATUSES.IN_PROGRESS.code:
        return '#F59E0B';
      case MILESTONE_STATUSES.DELAYED.code:
        return '#EF4444';
      default:
        return '#9CA3AF';
    }
  };

  // Calculate stage progress
  const calculateStageProgress = (stage) => {
    if (!stage.milestones || stage.milestones?.length === 0) {
      return stage.status === 'COMPLETED' ? 100 : 0;
    }

    const completedMilestones = (stage.milestones || []).filter((m) => m.completed_at).length;
    return Math.round(completedMilestones / stage.milestones?.length * 100);
  };

  // Toggle stage expansion
  const toggleStageExpansion = (stageCode) => {
    setExpandedStage(expandedStage === stageCode ? null : stageCode);
  };

  // Render milestone item
  const renderMilestone = (milestone, _stageCode) => {
    const status = getMilestoneStatus(milestone);
    const daysDiff = milestone.target_date ?
    getDaysDiff(new Date(), milestone.target_date) :
    0;

    return (
      <div
        key={milestone.id}
        className="flex items-start gap-3 p-3 rounded-lg hover:bg-gray-50 transition-colors">

        <div
          className="w-4 h-4 rounded-full mt-1 flex-shrink-0"
          style={{ backgroundColor: getStatusColor(status.code) }} />

        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <div className="min-w-0 flex-1">
              <h4 className="font-medium text-sm text-gray-900 truncate">
                {milestone.name}
              </h4>
              <p className="text-xs text-gray-500 truncate mt-1">
                {milestone.description}
              </p>
            </div>
            <Badge
              variant="outline"
              style={{
                borderColor: getStatusColor(status.code),
                color: getStatusColor(status.code)
              }}
              className="text-xs flex-shrink-0">

              {status.name}
            </Badge>
          </div>

          <div className="mt-2 flex items-center gap-4 text-xs text-gray-500">
            <span className="flex items-center gap-1">
              📅 目标时间: {milestone.target_date ?
              format(new Date(milestone.target_date), 'yyyy-MM-dd') :
              '未设定'
              }
            </span>
            {status.code === MILESTONE_STATUSES.DELAYED.code &&
            <span className="text-red-500">
                已延期 {Math.abs(daysDiff)} 天
            </span>
            }
            {milestone.completed_at &&
            <span className="text-green-500">
                完成于 {format(new Date(milestone.completed_at), 'MM-dd')}
            </span>
            }
          </div>
        </div>
      </div>);

  };

  // Render stage
  const renderStage = (stage, index) => {
    const stageInfo = getStageInfo(stage.code);
    const progress = calculateStageProgress(stage);
    const isExpanded = expandedStage === stage.code;

    return (
      <div key={stage.code} className="space-y-2">
        <div
          className={`p-4 rounded-lg border cursor-pointer transition-all ${
          stage.status === 'COMPLETED' ?
          'bg-green-50 border-green-200' :
          stage.status === 'DELAYED' ?
          'bg-red-50 border-red-200' :
          'bg-white border-gray-200 hover:border-gray-300'}`
          }
          onClick={() => toggleStageExpansion(stage.code)}>

          <div className="flex items-center gap-3">
            <div className="flex-shrink-0">
              <div
                className="w-10 h-10 rounded-lg flex items-center justify-center text-lg"
                style={{ backgroundColor: stageInfo.bgColor }}>

                {stageInfo.icon}
              </div>
            </div>

            <div className="flex-1 min-w-0">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-semibold text-gray-900">
                      {stageInfo.name}
                    </h3>
                    <Badge
                      variant="outline"
                      className="text-xs">

                      阶段 {stage.code}
                    </Badge>
                    <span className="text-xs text-gray-500">
                      {progress}% 完成
                    </span>
                  </div>

                  <p className="text-sm text-gray-600 mb-2">
                    {stageInfo.description}
                  </p>

                  <Progress value={progress} className="h-2" />
                </div>

                <div className="flex items-center gap-2">
                  {stage.status !== 'COMPLETED' &&
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      onStageClick(stage.code);
                    }}>

                      查看详情
                  </Button>
                  }
                  {isExpanded &&
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      onAddMilestone(stage.code);
                    }}>

                      + 里程碑
                  </Button>
                  }
                </div>
              </div>
            </div>
          </div>

          {/* Stage dates */}
          <div className="mt-3 grid grid-cols-2 gap-4 text-xs">
            <div>
              <span className="text-gray-500">开始：</span>
              <span className="font-medium">
                {stage.start_date ?
                format(new Date(stage.start_date), 'yyyy-MM-dd') :
                '未开始'
                }
              </span>
            </div>
            <div>
              <span className="text-gray-500">结束：</span>
              <span className="font-medium">
                {stage.end_date ?
                format(new Date(stage.end_date), 'yyyy-MM-dd') :
                '进行中'
                }
              </span>
            </div>
          </div>
        </div>

        {/* Milestones */}
        {isExpanded && stage.milestones && stage.milestones?.length > 0 &&
        <div className="ml-14 space-y-1">
            {(stage.milestones || []).map((milestone) => renderMilestone(milestone, stage.code))}
        </div>
        }

        {index < PROJECT_STAGES.length - 1 &&
        <Separator className="my-2" />
        }
      </div>);

  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>阶段里程碑追踪</span>
          <Button
            variant="outline"
            size="sm"
            onClick={onAddMilestone}>

            + 添加里程碑
          </Button>
        </CardTitle>
        <CardDescription>
          点击阶段查看详细里程碑信息
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-[600px] pr-4">
          <div className="space-y-2">
            {project.stages ?
            (project.stages || []).map((stage, index) => renderStage(stage, index)) :

            <div className="text-center py-8 text-gray-500">
                暂无阶段数据
            </div>
            }
          </div>
        </ScrollArea>
      </CardContent>
    </Card>);

};

export default MilestoneTracker;