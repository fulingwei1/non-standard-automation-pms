/**
 * AI处理方案推荐页面
 * Team 3 - AI Solution Recommendation
 */

import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { getAlertSolutions } from '@/services/api/shortage';
import SolutionCard from './components/SolutionCard';
import SolutionCompare from './components/SolutionCompare';
import { ArrowLeft, Loader2, Lightbulb } from 'lucide-react';
import { toast } from '@/hooks/use-toast';

const SolutionRecommendation = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [solutions, setSolutions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [_selectedSolution, setSelectedSolution] = useState(null);

  // 加载方案数据
  useEffect(() => {
    const loadSolutions = async () => {
      try {
        setLoading(true);
        const response = await getAlertSolutions(id);
        const solutionData = response.data.items || [];
        
        // 按推荐排名排序
        const sorted = solutionData.sort((a, b) => {
          if (a.is_recommended && !b.is_recommended) return -1;
          if (!a.is_recommended && b.is_recommended) return 1;
          return (b.ai_score || 0) - (a.ai_score || 0);
        });
        
        setSolutions(sorted);
      } catch (error) {
        console.error('Failed to load solutions:', error);
        toast({
          title: '加载失败',
          description: error.message,
          variant: 'destructive',
        });
      } finally {
        setLoading(false);
      }
    };

    loadSolutions();
  }, [id]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-12 w-12 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* 返回按钮 */}
      <Button
        variant="ghost"
        onClick={() => navigate(`/shortage/alerts/${id}`)}
        className="mb-4"
      >
        <ArrowLeft className="mr-2 h-4 w-4" />
        返回详情
      </Button>

      {/* 页面标题 */}
      <div>
        <div className="flex items-center gap-3 mb-2">
          <Lightbulb className="h-8 w-8 text-yellow-500" />
          <h1 className="text-3xl font-bold text-gray-900">AI 处理方案推荐</h1>
        </div>
        <p className="text-gray-500">
          基于多维度分析，AI为您生成最优处理方案
        </p>
      </div>

      {/* 切换视图 */}
      <Tabs defaultValue="cards" className="w-full">
        <TabsList>
          <TabsTrigger value="cards">方案卡片</TabsTrigger>
          <TabsTrigger value="compare">对比分析</TabsTrigger>
        </TabsList>

        {/* 卡片视图 */}
        <TabsContent value="cards" className="space-y-6 mt-6">
          {solutions.length === 0 ? (
            <Card>
              <CardContent className="p-12 text-center">
                <Lightbulb className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500">暂无方案数据</p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {solutions.map((solution) => (
                <SolutionCard
                  key={solution.id}
                  solution={solution}
                  onClick={setSelectedSolution}
                />
              ))}
            </div>
          )}
        </TabsContent>

        {/* 对比视图 */}
        <TabsContent value="compare" className="mt-6">
          <SolutionCompare solutions={solutions} />
        </TabsContent>
      </Tabs>

      {/* AI 评分说明 */}
      <Card>
        <CardContent className="p-6">
          <h3 className="font-semibold mb-3">评分说明</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div>
              <p className="font-medium text-blue-600 mb-1">可行性评分</p>
              <p className="text-gray-600">方案的实施可能性和执行难度</p>
            </div>
            <div>
              <p className="font-medium text-orange-600 mb-1">成本评分</p>
              <p className="text-gray-600">预计成本越低，评分越高</p>
            </div>
            <div>
              <p className="font-medium text-green-600 mb-1">时间评分</p>
              <p className="text-gray-600">解决时间越短，评分越高</p>
            </div>
            <div>
              <p className="font-medium text-red-600 mb-1">风险评分</p>
              <p className="text-gray-600">潜在风险越少，评分越高</p>
            </div>
          </div>
          <div className="mt-4 pt-4 border-t">
            <p className="font-medium text-purple-600 mb-1">AI 综合评分</p>
            <p className="text-gray-600 text-sm">
              综合评分 = 可行性 × 30% + 成本 × 30% + 时间 × 30% + 风险 × 10%
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default SolutionRecommendation;
