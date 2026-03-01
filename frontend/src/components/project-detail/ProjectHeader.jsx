import React from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
  Badge,
  Progress,
  Button,
  Separator } from
'@/components/ui';
import {
  PROJECT_STATUS,
  PROJECT_HEALTH,
  PROJECT_PRIORITY,
  PROJECT_STAGES,
  METRICS } from
'@/lib/constants/projectDetail';
import { format } from 'date-fns';
import { zhCN } from 'date-fns/locale';

const ProjectHeader = ({ project, onEdit, onViewDocuments, onViewTimeline }) => {

  // Calculate project progress based on stages
  const calculateProgress = () => {
    if (!project.stages || project.stages?.length === 0) {return 0;}

    const completedStages = (project.stages || []).filter((stage) =>
    stage.status === 'COMPLETED'
    ).length;

    return Math.round(completedStages / PROJECT_STAGES.length * 100);
  };

  // Get stage info by code
  const getStageInfo = (stageCode) => {
    return PROJECT_STAGES.find((stage) => stage.code === stageCode) || PROJECT_STAGES[0];
  };

  // Get project status info
  const getStatusInfo = (status) => {
    const statusMap = {
      'ACTIVE': PROJECT_STATUS.ACTIVE,
      'COMPLETED': PROJECT_STATUS.COMPLETED,
      'DELAYED': PROJECT_STATUS.DELAYED,
      'SUSPENDED': PROJECT_STATUS.SUSPENDED,
      'CANCELLED': PROJECT_STATUS.CANCELLED
    };
    return statusMap[status] || PROJECT_STATUS.ACTIVE;
  };

  // Get health info
  const getHealthInfo = (health) => {
    const healthMap = {
      'H1': PROJECT_HEALTH.H1,
      'H2': PROJECT_HEALTH.H2,
      'H3': PROJECT_HEALTH.H3,
      'H4': PROJECT_HEALTH.H4
    };
    return healthMap[health] || PROJECT_HEALTH.H1;
  };

  // Get priority info
  const getPriorityInfo = (priority) => {
    const priorityMap = {
      'HIGH': PROJECT_PRIORITY.HIGH,
      'MEDIUM': PROJECT_PRIORITY.MEDIUM,
      'LOW': PROJECT_PRIORITY.LOW
    };
    return priorityMap[priority] || PROJECT_PRIORITY.MEDIUM;
  };

  const progress = calculateProgress();
  const statusInfo = getStatusInfo(project.status);
  const healthInfo = getHealthInfo(project.health);
  const priorityInfo = getPriorityInfo(project.priority);

  return (
    <div className="space-y-6">
      {/* Header Section */}
      <div className="flex flex-col lg:flex-row gap-6">
        {/* Basic Info */}
        <div className="flex-1">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                {project.name}
              </h1>
              <div className="flex items-center gap-3 flex-wrap">
                <Badge
                  variant="outline"
                  style={{
                    borderColor: statusInfo.color,
                    color: statusInfo.color
                  }}>

                  {statusInfo.icon} {statusInfo.name}
                </Badge>
                <Badge
                  variant="outline"
                  style={{
                    borderColor: healthInfo.color,
                    color: healthInfo.color
                  }}>

                  {healthInfo.icon} {healthInfo.name}
                </Badge>
                <Badge
                  variant="outline"
                  style={{
                    borderColor: priorityInfo.color,
                    color: priorityInfo.color
                  }}>

                  {priorityInfo.icon} {priorityInfo.name}优先级
                </Badge>
              </div>
            </div>

            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={onViewDocuments}>

                📄 文档
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={onViewTimeline}>

                📅 时间线
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={onEdit}>

                ✏️ 编辑
              </Button>
            </div>
          </div>

          <p className="text-gray-600 mb-4">
            {project.description || '暂无项目描述'}
          </p>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-gray-500">项目编号：</span>
              <span className="font-medium">{project.code}</span>
            </div>
            <div>
              <span className="text-gray-500">客户：</span>
              <span className="font-medium">{project.customer || '-'}</span>
            </div>
            <div>
              <span className="text-gray-500">机台号：</span>
              <span className="font-medium">{project.machine_code || '-'}</span>
            </div>
            <div>
              <span className="text-gray-500">合同金额：</span>
              <span className="font-medium">
                {project.budget ? `¥${Number(project.budget).toLocaleString()}` : '-'}
              </span>
            </div>
          </div>
        </div>

        {/* Progress Card */}
        <div className="lg:w-80">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg">项目进度</CardTitle>
              <CardDescription>当前完成度</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-3xl font-bold">{progress}%</span>
                  <span className="text-sm text-gray-500">
                    {progress === 100 ? '已完成' : '进行中'}
                  </span>
                </div>
                <Progress value={progress || "unknown"} className="h-3" />
                <div className="text-xs text-gray-500">
                  已完成 {project.stages?.filter((s) => s.status === 'COMPLETED').length || 0} /
                  {PROJECT_STAGES.length} 个阶段
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Timeline Info */}
      <Card>
        <CardHeader>
          <CardTitle>时间节点</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-sm text-gray-500 mb-1">开始时间</div>
              <div className="font-medium">
                {project.start_date ?
                format(new Date(project.start_date), 'yyyy-MM-dd', { locale: zhCN }) :
                '-'
                }
              </div>
            </div>
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-sm text-gray-500 mb-1">计划完成</div>
              <div className="font-medium">
                {project.planned_end_date ?
                format(new Date(project.planned_end_date), 'yyyy-MM-dd', { locale: zhCN }) :
                '-'
                }
              </div>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-sm text-gray-500 mb-1">实际完成</div>
              <div className="font-medium">
                {project.actual_end_date ?
                format(new Date(project.actual_end_date), 'yyyy-MM-dd', { locale: zhCN }) :
                '进行中'
                }
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Current Stage */}
      {project.current_stage &&
      <Card>
          <CardHeader>
            <CardTitle>当前阶段</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-4">
              <div
              className="w-16 h-16 rounded-full flex items-center justify-center text-2xl"
              style={{ backgroundColor: getStageInfo(project.current_stage).bgColor }}>

                {getStageInfo(project.current_stage).icon}
              </div>
              <div className="flex-1">
                <h3 className="text-xl font-semibold mb-1">
                  {getStageInfo(project.current_stage).name}
                </h3>
                <p className="text-gray-600 mb-2">
                  {getStageInfo(project.current_stage).description}
                </p>
                <div className="flex items-center gap-2">
                  <Badge variant="secondary">
                    阶段 {project.current_stage}
                  </Badge>
                  <span className="text-sm text-gray-500">
                    开始于: {project.current_stage_start_date ?
                  format(new Date(project.current_stage_start_date), 'MM-dd', { locale: zhCN }) :
                  '-'
                  }
                  </span>
                </div>
              </div>
            </div>
          </CardContent>
      </Card>
      }

      {/* Additional Info */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">团队成员</p>
                <p className="text-2xl font-bold">{project.team_members?.length || 0}</p>
              </div>
              <div className="text-2xl">👥</div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">关联文档</p>
                <p className="text-2xl font-bold">{project.document_count || 0}</p>
              </div>
              <div className="text-2xl">📄</div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">风险数量</p>
                <p className="text-2xl font-bold">{project.risk_count || 0}</p>
              </div>
              <div className="text-2xl">⚠️</div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">更新时间</p>
                <p className="text-sm font-medium">
                  {project.updated_at ?
                  format(new Date(project.updated_at), 'MM-dd HH:mm', { locale: zhCN }) :
                  '-'
                  }
                </p>
              </div>
              <div className="text-2xl">🕐</div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>);

};

export default ProjectHeader;
