/**
 * 项目影响分析页面
 * Team 3 - Project Impact Analysis
 */

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { getProjectImpactAnalysis } from '@/services/api/shortage';
import { Folder, Clock, DollarSign, AlertTriangle } from 'lucide-react';
import { toast } from '@/hooks/use-toast';

const ProjectImpactAnalysis = () => {
  const [loading, setLoading] = useState(true);
  const [projects, setProjects] = useState([]);

  // 加载项目影响数据
  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        const response = await getProjectImpactAnalysis();
        setProjects(response.data.projects || []);
      } catch (error) {
        console.error('Failed to load project impact data:', error);
        toast({
          title: '加载失败',
          description: error.message,
          variant: 'destructive',
        });
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  // 按风险评分排序
  const sortedProjects = [...projects].sort(
    (a, b) => (b.risk_score || 0) - (a.risk_score || 0)
  );

  return (
    <div className="p-6 space-y-6">
      {/* 页面标题 */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">项目影响分析</h1>
        <p className="text-gray-500 mt-1">
          分析缺料对项目的影响程度，优先处理高风险项目
        </p>
      </div>

      {/* 总体统计 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Folder className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">受影响项目</p>
                <p className="text-2xl font-bold text-gray-900">
                  {projects.length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-red-100 rounded-lg">
                <AlertTriangle className="h-5 w-5 text-red-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">高风险项目</p>
                <p className="text-2xl font-bold text-red-600">
                  {projects.filter((p) => p.risk_score >= 75).length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-orange-100 rounded-lg">
                <Clock className="h-5 w-5 text-orange-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">预计总延期</p>
                <p className="text-2xl font-bold text-orange-600">
                  {projects.reduce((sum, p) => sum + (p.estimated_delay_days || 0), 0)} 天
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <DollarSign className="h-5 w-5 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">预计总成本</p>
                <p className="text-2xl font-bold text-green-600">
                  ¥
                  {projects
                    .reduce((sum, p) => sum + parseFloat(p.cost_impact || 0), 0)
                    .toLocaleString()}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 项目列表 */}
      <Card>
        <CardHeader>
          <CardTitle>项目影响详情（按风险评分排序）</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {sortedProjects.length === 0 ? (
              <div className="text-center py-12">
                <Folder className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500">暂无受影响的项目</p>
              </div>
            ) : (
              sortedProjects.map((project, index) => (
                <ProjectCard key={project.project_id || index} project={project} />
              ))
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// 项目卡片组件
const ProjectCard = ({ project }) => {
  const riskScore = project.risk_score || 0;
  const riskLevel =
    riskScore >= 75
      ? { label: '极高', color: 'text-red-600', bg: 'bg-red-50', border: 'border-red-200' }
      : riskScore >= 50
      ? { label: '高', color: 'text-orange-600', bg: 'bg-orange-50', border: 'border-orange-200' }
      : riskScore >= 25
      ? { label: '中', color: 'text-yellow-600', bg: 'bg-yellow-50', border: 'border-yellow-200' }
      : { label: '低', color: 'text-blue-600', bg: 'bg-blue-50', border: 'border-blue-200' };

  return (
    <Card className={`border-l-4 ${riskLevel.border}`}>
      <CardContent className="p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <h3 className="text-lg font-semibold text-gray-900">
                {project.project_name || `项目 ${project.project_id}`}
              </h3>
              <Badge variant="outline" className={riskLevel.color}>
                风险: {riskLevel.label}
              </Badge>
              {project.is_critical_path && (
                <Badge variant="destructive">关键路径</Badge>
              )}
            </div>
            <p className="text-sm text-gray-500">
              项目ID: {project.project_id}
            </p>
          </div>
        </div>

        {/* 风险评分 */}
        <div className="mb-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-600">风险评分</span>
            <span className={`text-lg font-bold ${riskLevel.color}`}>
              {riskScore}/100
            </span>
          </div>
          <Progress value={riskScore} className="h-2" />
        </div>

        {/* 影响指标 */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* 预警数量 */}
          <div className={`p-3 rounded-lg ${riskLevel.bg}`}>
            <p className="text-xs text-gray-600 mb-1">相关预警</p>
            <p className={`text-xl font-bold ${riskLevel.color}`}>
              {project.alert_count || 0} 条
            </p>
          </div>

          {/* 预计延期 */}
          {project.estimated_delay_days !== null && (
            <div className="p-3 rounded-lg bg-orange-50">
              <p className="text-xs text-gray-600 mb-1">预计延期</p>
              <p className="text-xl font-bold text-orange-600">
                {project.estimated_delay_days} 天
              </p>
            </div>
          )}

          {/* 成本影响 */}
          {project.cost_impact !== null && (
            <div className="p-3 rounded-lg bg-green-50">
              <p className="text-xs text-gray-600 mb-1">成本影响</p>
              <p className="text-xl font-bold text-green-600">
                ¥{parseFloat(project.cost_impact).toLocaleString()}
              </p>
            </div>
          )}
        </div>

        {/* 缺料物料列表 */}
        {project.shortage_materials && project.shortage_materials.length > 0 && (
          <div className="mt-4 pt-4 border-t">
            <p className="text-sm font-medium text-gray-700 mb-2">
              缺料物料 ({project.shortage_materials.length})
            </p>
            <div className="flex flex-wrap gap-2">
              {project.shortage_materials.map((material, idx) => (
                <Badge key={idx} variant="outline">
                  {material.material_name || material.material_code}
                </Badge>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default ProjectImpactAnalysis;
