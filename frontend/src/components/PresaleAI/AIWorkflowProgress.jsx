/**
 * AI工作流进度组件
 * Team 10: 售前AI系统集成与前端UI
 */
import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  CheckCircle,
  Circle,
  Clock,
  XCircle,
  Loader2,
  Brain,
  FileText,
  DollarSign,
  TrendingUp,
  File,
} from 'lucide-react';

const AIWorkflowProgress = ({ workflowStatus }) => {
  if (!workflowStatus) {
    return (
      <Card>
        <CardContent className="p-6 text-center text-muted-foreground">
          暂无工作流数据
        </CardContent>
      </Card>
    );
  }

  const steps = [
    {
      key: 'requirement',
      label: '需求理解',
      icon: Brain,
      description: 'AI分析客户需求',
    },
    {
      key: 'solution',
      label: '方案生成',
      icon: FileText,
      description: '自动生成技术方案',
    },
    {
      key: 'cost',
      label: '成本估算',
      icon: DollarSign,
      description: '智能成本评估',
    },
    {
      key: 'winrate',
      label: '赢率预测',
      icon: TrendingUp,
      description: '项目赢率分析',
    },
    {
      key: 'quotation',
      label: '报价生成',
      icon: File,
      description: '生成正式报价',
    },
  ];

  const getStepStatus = (stepKey) => {
    const step = workflowStatus.steps?.find((s) => s.workflow_step === stepKey);
    return step?.status || 'pending';
  };

  const getStepIcon = (status) => {
    switch (status) {
      case 'success':
        return CheckCircle;
      case 'running':
        return Loader2;
      case 'failed':
        return XCircle;
      case 'pending':
      default:
        return Circle;
    }
  };

  const getStepColor = (status) => {
    switch (status) {
      case 'success':
        return 'text-green-600';
      case 'running':
        return 'text-blue-600 animate-spin';
      case 'failed':
        return 'text-red-600';
      case 'pending':
      default:
        return 'text-gray-400';
    }
  };

  const getStatusBadge = (status) => {
    const variants = {
      success: { label: '已完成', variant: 'success' },
      running: { label: '进行中', variant: 'default' },
      failed: { label: '失败', variant: 'destructive' },
      pending: { label: '待处理', variant: 'secondary' },
    };
    const { label, variant } = variants[status] || variants.pending;
    return <Badge variant={variant}>{label}</Badge>;
  };

  return (
    <Card>
      <CardContent className="p-6">
        {/* Overall Progress */}
        <div className="mb-6">
          <div className="flex justify-between items-center mb-2">
            <h3 className="text-lg font-semibold">AI工作流进度</h3>
            <Badge variant="outline">
              {Math.round(workflowStatus.progress || 0)}%
            </Badge>
          </div>
          <div className="w-full bg-secondary rounded-full h-2">
            <div
              className="bg-primary h-2 rounded-full transition-all duration-300"
              style={{ width: `${workflowStatus.progress || 0}%` }}
            />
          </div>
        </div>

        {/* Steps */}
        <div className="space-y-4">
          {steps.map((step, index) => {
            const status = getStepStatus(step.key);
            const StepIcon = step.icon;
            const StatusIcon = getStepIcon(status);
            const stepData = workflowStatus.steps?.find(
              (s) => s.workflow_step === step.key
            );

            return (
              <div key={step.key} className="flex items-start gap-4">
                {/* Step Number & Line */}
                <div className="flex flex-col items-center">
                  <div className="relative">
                    <div
                      className={`w-10 h-10 rounded-full flex items-center justify-center ${
                        status === 'success'
                          ? 'bg-green-100'
                          : status === 'running'
                          ? 'bg-blue-100'
                          : status === 'failed'
                          ? 'bg-red-100'
                          : 'bg-gray-100'
                      }`}
                    >
                      <StatusIcon className={`h-5 w-5 ${getStepColor(status)}`} />
                    </div>
                  </div>
                  {index < steps.length - 1 && (
                    <div
                      className={`w-0.5 h-16 mt-2 ${
                        status === 'success' ? 'bg-green-300' : 'bg-gray-200'
                      }`}
                    />
                  )}
                </div>

                {/* Step Content */}
                <div className="flex-1 pb-8">
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-2">
                      <StepIcon className="h-5 w-5 text-muted-foreground" />
                      <h4 className="font-medium">{step.label}</h4>
                    </div>
                    {getStatusBadge(status)}
                  </div>
                  <p className="text-sm text-muted-foreground mb-2">
                    {step.description}
                  </p>

                  {/* Step Details */}
                  {stepData && (
                    <div className="text-xs text-muted-foreground space-y-1">
                      {stepData.started_at && (
                        <p>开始: {new Date(stepData.started_at).toLocaleString()}</p>
                      )}
                      {stepData.completed_at && (
                        <p>完成: {new Date(stepData.completed_at).toLocaleString()}</p>
                      )}
                      {stepData.error_message && (
                        <p className="text-red-600">
                          错误: {stepData.error_message}
                        </p>
                      )}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Summary */}
        <div className="mt-6 pt-6 border-t">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">当前步骤:</span>
            <span className="font-medium">
              {steps.find((s) => s.key === workflowStatus.current_step)?.label ||
                '已完成'}
            </span>
          </div>
          <div className="flex justify-between text-sm mt-2">
            <span className="text-muted-foreground">整体状态:</span>
            <span className="font-medium capitalize">
              {workflowStatus.overall_status}
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default AIWorkflowProgress;
