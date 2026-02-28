/**
 * Service Record Overview Component - 服务记录概览组件
 * 显示服务记录的关键指标和快速操作入口
 */
import { useMemo } from "react";
import { 
  FileText, 
  Clock, 
  CheckCircle2, 
  Calendar,
  TrendingUp,
  AlertTriangle,
  Star,
  Users
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { Progress } from "../ui/progress";
import { 
  SERVICE_STATUS, 
  SERVICE_TYPES,
  FEEDBACK_RATINGS,
  calculateServiceCompletionRate,
  getServiceQualityScore
} from "@/lib/constants/serviceRecord";

const ServiceRecordOverview = ({ 
  records, 
  stats, 
  onQuickAction 
}) => {
  // 计算高级统计数据
  const advancedStats = useMemo(() => {
    if (!records || records.length === 0) {
      return {
        serviceTypeDistribution: {},
        statusDistribution: {},
        qualityScore: 0,
        completionRate: 0,
        avgServiceTime: 0,
        recentFeedback: []
      };
    }

    // 服务类型分布
    const serviceTypeDistribution = records.reduce((acc, record) => {
      const type = record.service_type || 'CONSULTATION';
      const typeConfig = SERVICE_TYPES[type] || SERVICE_TYPES.CONSULTATION;
      acc[typeConfig.label] = (acc[typeConfig.label] || 0) + 1;
      return acc;
    }, {});

    // 状态分布
    const statusDistribution = records.reduce((acc, record) => {
      const status = record.status || 'SCHEDULED';
      const statusConfig = SERVICE_STATUS[status] || SERVICE_STATUS.SCHEDULED;
      acc[statusConfig.label] = (acc[statusConfig.label] || 0) + 1;
      return acc;
    }, {});

    // 质量评分（基于反馈）
    const feedbacks = records.filter(r => r.feedback_rating).map(r => ({
      rating: r.feedback_rating,
      comment: r.feedback_comment,
      created_time: r.feedback_time
    }));
    const qualityScore = getServiceQualityScore(feedbacks);

    // 完成率
    const completionRate = calculateServiceCompletionRate(records);

    // 平均服务时间
    const completedRecords = records.filter(r => r.start_time && r.end_time);
    const avgServiceTime = completedRecords.length > 0 
      ? completedRecords.reduce((sum, r) => {
          const duration = (new Date(r.end_time) - new Date(r.start_time)) / (1000 * 60 * 60);
          return sum + duration;
        }, 0) / completedRecords.length
      : 0;

    // 最近的反馈
    const recentFeedback = feedbacks
      .sort((a, b) => new Date(b.created_time) - new Date(a.created_time))
      .slice(0, 5);

    return {
      serviceTypeDistribution,
      statusDistribution,
      qualityScore,
      completionRate,
      avgServiceTime,
      recentFeedback
    };
  }, [records]);

  // 获取优先级服务
  const priorityServices = useMemo(() => {
    if (!records) {return [];}
    
    return records
      .filter(record => {
        const status = record.status || 'SCHEDULED';
        const statusConfig = SERVICE_STATUS[status];
        return statusConfig && (
          status === 'IN_PROGRESS' || 
          (record.priority && record.priority.level >= 3)
        );
      })
      .slice(0, 5);
  }, [records]);

  // 今日服务
  const todayServices = useMemo(() => {
    if (!records) {return [];}
    
    const today = new Date().toDateString();
    return records.filter(record => {
      const serviceDate = new Date(record.scheduled_date || record.created_time);
      return serviceDate.toDateString() === today;
    });
  }, [records]);

  return (
    <div className="space-y-6">
      {/* 核心指标卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-gray-600 mb-1">总记录数</div>
                <div className="text-2xl font-bold text-gray-900">
                  {stats?.total || 0}
                </div>
              </div>
              <FileText className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-gray-600 mb-1">进行中</div>
                <div className="text-2xl font-bold text-amber-600">
                  {stats?.inProgress || 0}
                </div>
              </div>
              <Clock className="h-8 w-8 text-amber-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-gray-600 mb-1">已完成</div>
                <div className="text-2xl font-bold text-emerald-600">
                  {stats?.completed || 0}
                </div>
              </div>
              <CheckCircle2 className="h-8 w-8 text-emerald-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-gray-600 mb-1">本月服务</div>
                <div className="text-2xl font-bold text-purple-600">
                  {stats?.thisMonth || 0}
                </div>
              </div>
              <Calendar className="h-8 w-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-gray-600 mb-1">质量评分</div>
                <div className="text-2xl font-bold text-blue-600">
                  {advancedStats.qualityScore.toFixed(1)}
                </div>
              </div>
              <Star className="h-8 w-8 text-yellow-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 服务分析概览 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 服务类型分布 */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-sm">
              <Users className="h-4 w-4" />
              服务类型分布
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(advancedStats.serviceTypeDistribution).map(([type, count]) => {
                const total = records?.length || 1;
                const percentage = Math.round((count / total) * 100);
                
                return (
                  <div key={type} className="flex items-center justify-between">
                    <span className="text-sm text-gray-700">{type}</span>
                    <div className="flex items-center gap-2">
                      <div className="w-16 bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-blue-500 h-2 rounded-full" 
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                      <span className="text-xs text-gray-500 w-8">{count}</span>
                    </div>
                  </div>
                );
              })}
              {Object.keys(advancedStats.serviceTypeDistribution).length === 0 && (
                <div className="text-center text-gray-500 py-4">
                  暂无服务数据
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* 完成率统计 */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-sm">
              <TrendingUp className="h-4 w-4" />
              完成率统计
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm font-medium">总体完成率</span>
                  <span className="text-sm font-bold">{advancedStats.completionRate}%</span>
                </div>
                <Progress value={advancedStats.completionRate} className="h-2" />
              </div>
              
              <div className="pt-2 border-t">
                <div className="text-sm text-gray-600">
                  平均服务时长
                </div>
                <div className="text-lg font-semibold">
                  {advancedStats.avgServiceTime.toFixed(1)} 小时
                </div>
              </div>
              
              <div className="text-sm text-gray-600">
                今日服务安排
              </div>
              <div className="text-lg font-semibold">
                {todayServices.length} 项
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 优先级服务 */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-sm">
              <AlertTriangle className="h-4 w-4" />
              优先级服务
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {priorityServices.map((service, index) => {
                const statusConfig = SERVICE_STATUS[service.status] || SERVICE_STATUS.SCHEDULED;
                
                return (
                  <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium truncate">
                        {service.customer_name || '未知客户'}
                      </div>
                      <div className="text-xs text-gray-500 truncate">
                        {service.service_type || '咨询'}
                      </div>
                    </div>
                    <Badge className={statusConfig.color} variant="secondary">
                      {statusConfig.label}
                    </Badge>
                  </div>
                );
              })}
              {priorityServices.length === 0 && (
                <div className="text-center text-gray-500 py-4">
                  暂无优先级服务
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 最近反馈 */}
      {advancedStats.recentFeedback.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-sm">
              <Star className="h-4 w-4" />
              最近客户反馈
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {advancedStats.recentFeedback.map((feedback, index) => {
                const ratingConfig = FEEDBACK_RATINGS[`EXCELLENT_${feedback.rating * 5}`] || 
                                   FEEDBACK_RATINGS.SATISFIED;
                
                return (
                  <div key={index} className="flex items-start gap-3 p-3 bg-gray-50 rounded">
                    <div className="flex-shrink-0">
                      <Badge className={ratingConfig.color} variant="secondary">
                        {feedback.rating}/5
                      </Badge>
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm text-gray-700">
                        {feedback.comment || '未提供具体反馈'}
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        {new Date(feedback.created_time).toLocaleDateString()}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* 快速操作 */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm">快速操作</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            <Button 
              size="sm" 
              variant="outline"
              onClick={() => onQuickAction && onQuickAction('createService')}
            >
              <FileText className="h-4 w-4 mr-2" />
              创建服务
            </Button>
            <Button 
              size="sm" 
              variant="outline"
              onClick={() => onQuickAction && onQuickAction('todaySchedule')}
            >
              <Calendar className="h-4 w-4 mr-2" />
              今日安排
            </Button>
            <Button 
              size="sm" 
              variant="outline"
              onClick={() => onQuickAction && onQuickAction('pendingReports')}
            >
              <CheckCircle2 className="h-4 w-4 mr-2" />
              待审核报告
            </Button>
            <Button 
              size="sm" 
              variant="outline"
              onClick={() => onQuickAction && onQuickAction('customerFeedback')}
            >
              <Star className="h-4 w-4 mr-2" />
              客户反馈
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* 性能提醒 */}
      {(advancedStats.completionRate < 80 || advancedStats.qualityScore < 4.0) && (
        <Card className="border-amber-200 bg-amber-50">
          <CardContent className="pt-6">
            <div className="flex items-start gap-3">
              <AlertTriangle className="h-5 w-5 text-amber-600 mt-0.5" />
              <div className="space-y-1">
                {advancedStats.completionRate < 80 && (
                  <p className="text-sm text-amber-800">
                    服务完成率偏低 ({advancedStats.completionRate}%)，建议加强服务过程管理
                  </p>
                )}
                {advancedStats.qualityScore < 4.0 && (
                  <p className="text-sm text-amber-800">
                    客户满意度偏低 ({advancedStats.qualityScore.toFixed(1)})，请关注服务质量改进
                  </p>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default ServiceRecordOverview;