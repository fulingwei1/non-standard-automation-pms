/**
 * Opportunity Pipeline Component
 * 商机管道视图组件 - 看板式商机管理
 */

import { useState, useEffect, useMemo, useCallback } from "react";
import { DndProvider, useDrag, useDrop } from "react-dnd";
import { HTML5Backend } from "react-dnd-html5-backend";
import {
  Plus,
  BarChart3,
  Users,
  DollarSign,
  Target,
  TrendingUp,
  RefreshCw,
  Settings,
  Filter,
  Grid,
  List,
  Calendar,
  Eye
} from "lucide-react";
import { Button } from "../../components/ui/button";
import { Badge } from "../../components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../../components/ui/tabs";
import { cn } from "../../lib/utils";
import OpportunityCard from "./OpportunityCard";
import OpportunityFilters from "./OpportunityFilters";
import {
  opportunityStageConfig,
  opportunityStageFlow,
  getOpportunityStats,
  filterOpportunities,
  sortOpportunities
} from "./opportunityBoardConstants";

/**
 * 看板列组件
 */
const PipelineColumn = ({
  stage,
  opportunities,
  onStageChange,
  onEdit,
  onDelete,
  onView,
  onSelect,
  isSelected,
  className
}) => {
  const stageConfig = opportunityStageConfig[stage];
  const [{ isOver }, drop] = useDrop({
    accept: "opportunity",
    drop: (item) => onStageChange(item.id, stage),
    collect: (monitor) => ({
      isOver: !!monitor.isOver()
    })
  });

  const [, drag] = useDrag({
    type: "opportunity",
    item: { id: stage },
    collect: (monitor) => ({
      isDragging: !!monitor.isDragging()
    })
  });

  // 过滤当前阶段的机会
  const stageOpportunities = useMemo(() => {
    return opportunities.filter(opp => opp.stage === stage);
  }, [opportunities, stage]);

  // 计算统计信息
  const stageStats = useMemo(() => {
    const total = stageOpportunities.length;
    const highValue = stageOpportunities.filter(opp =>
      (opp.expected_amount || 0) > 1000000
    ).length;
    const totalAmount = stageOpportunities.reduce(
      (sum, opp) => sum + (opp.expected_amount || 0), 0
    );

    return { total, highValue, totalAmount };
  }, [stageOpportunities]);

  return (
    <div ref={drop} className={cn("flex flex-col h-full", className)}>
      {/* 列标题 */}
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className={cn(
              "w-3 h-3 rounded-full",
              stageConfig.color.split(" ")[0]
            )} />
            <CardTitle className="text-base flex items-center gap-2">
              {stageConfig.label}
              <Badge variant="secondary" className="text-xs">
                {stageStats.total}
              </Badge>
            </CardTitle>
          </div>
          {stageStats.total > 0 && (
            <div className="text-xs text-gray-500">
              {formatCurrency(stageStats.totalAmount)}
            </div>
          )}
        </div>

        {/* 列统计 */}
        {stageStats.highValue > 0 && (
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <BarChart3 className="h-3 w-3" />
            <span>{stageStats.highValue} 个高价值商机</span>
          </div>
        )}
      </CardHeader>

      {/* 列内容 */}
      <CardContent
        ref={drag}
        className={cn(
          "flex-1 space-y-3",
          "min-h-[400px]",
          "transition-all duration-200",
          isOver && "bg-gray-50 rounded-lg"
        )}
      >
        {stageOpportunities.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-gray-400">
            <Target className="h-12 w-12 mb-2" />
            <p className="text-sm">暂无商机</p>
          </div>
        ) : (
          stageOpportunities.map((opportunity) => (
            <OpportunityCard
              key={opportunity.id}
              opportunity={opportunity}
              onStageChange={onStageChange}
              onEdit={onEdit}
              onDelete={onDelete}
              onView={onView}
              onSelect={onSelect}
              isSelected={isSelected}
              compact={false}
            />
          ))
        )}
      </CardContent>

      {/* 添加按钮 */}
      <div className="p-3 pt-0">
        <Button
          variant="outline"
          size="sm"
          className="w-full"
          onClick={() => {
            // 这里应该打开创建商机的对话框
            console.log(`Create new opportunity for ${stage}`);
          }}
        >
          <Plus className="mr-1 h-3 w-3" />
          添加商机
        </Button>
      </div>
    </div>
  );
};

/**
 * 商机管道主组件
 */
export const OpportunityPipeline = ({
  opportunities = [],
  onStageChange,
  onEdit,
  onDelete,
  onView,
  onSelect,
  className,
  refreshTrigger,
  onRefresh
}) => {
  const [filters, setFilters] = useState({});
  const [selectedView, setSelectedView] = useState("kanban");
  const [selectedOpportunities, setSelectedOpportunities] = useState(new Set());

  // 过滤和排序商机
  const filteredOpportunities = useMemo(() => {
    let result = filterOpportunities(opportunities, filters);
    if (filters.sort) {
      const [field, order] = filters.sort.split("_");
      result = sortOpportunities(result, field, order);
    }
    return result;
  }, [opportunities, filters]);

  // 统计信息
  const stats = useMemo(() => {
    return getOpportunityStats(filteredOpportunities);
  }, [filteredOpportunities]);

  // 刷新处理
  useEffect(() => {
    if (refreshTrigger) {
      onRefresh();
    }
  }, [refreshTrigger, onRefresh]);

  // 处理商机选择
  const handleSelectOpportunity = (opportunity) => {
    const newSelection = new Set(selectedOpportunities);
    if (newSelection.has(opportunity.id)) {
      newSelection.delete(opportunity.id);
    } else {
      newSelection.add(opportunity.id);
    }
    setSelectedOpportunities(newSelection);
  };

  // 处理阶段变更
  const handleStageChange = (opportunityId, newStage) => {
    if (onStageChange) {
      onStageChange(opportunityId, newStage);
    }
  };

  // 选中状态检查
  const isOpportunitySelected = (opportunityId) => {
    return selectedOpportunities.has(opportunityId);
  };

  return (
    <DndProvider backend={HTML5Backend}>
      <div className={cn("w-full h-full flex flex-col", className)}>
        {/* 头部统计 */}
        <Card className="mb-4">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="h-5 w-5" />
                  商机管道概览
                </CardTitle>
                <p className="text-sm text-gray-500 mt-1">
                  管理和跟踪销售机会
                </p>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={onRefresh}
                >
                  <RefreshCw className="mr-1 h-3 w-3" />
                  刷新
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold">{stats.total}</div>
                <div className="text-xs text-gray-500">总商机数</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {stats.my_opportunities || 0}
                </div>
                <div className="text-xs text-gray-500">我的商机</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-red-600">
                  {stats.high_priority || 0}
                </div>
                <div className="text-xs text-gray-500">高优先级</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-emerald-600">
                  {formatCurrency(stats.total_expected_amount)}
                </div>
                <div className="text-xs text-gray-500">预计总金额</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-orange-600">
                  {stats.conversion_rate}%
                </div>
                <div className="text-xs text-gray-500">转化率</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">
                  {stats.expected_to_win || 0}
                </div>
                <div className="text-xs text-gray-500">预计成交</div>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="flex-1 flex gap-4">
          {/* 过滤器 */}
          <div className="w-80 flex-shrink-0">
            <OpportunityFilters
              onFilterChange={setFilters}
              initialFilters={filters}
            />
          </div>

          {/* 主要内容区 */}
          <div className="flex-1 flex flex-col">
            {/* 视图切换 */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Tabs value={selectedView} onValueChange={setSelectedView}>
                  <TabsList>
                    <TabsTrigger value="kanban" className="flex items-center gap-1">
                      <Grid className="h-4 w-4" />
                      看板
                    </TabsTrigger>
                    <TabsTrigger value="list" className="flex items-center gap-1">
                      <List className="h-4 w-4" />
                      列表
                    </TabsTrigger>
                    <TabsTrigger value="stats" className="flex items-center gap-1">
                      <BarChart3 className="h-4 w-4" />
                      统计
                    </TabsTrigger>
                  </TabsList>
                </Tabs>

                {selectedOpportunities.size > 0 && (
                  <div className="flex items-center gap-2">
                    <Badge variant="secondary">
                      {selectedOpportunities.size} 个已选中
                    </Badge>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setSelectedOpportunities(new Set())}
                    >
                      取消选择
                    </Button>
                  </div>
                )}
              </div>
            </div>

            {/* 看板视图 */}
            {selectedView === "kanban" && (
              <div className="flex-1 overflow-x-auto">
                <div className="flex gap-4 min-w-max">
                  {opportunityStageFlow.map((stage) => (
                    <div
                      key={stage}
                      className="w-80 flex-shrink-0"
                    >
                      <PipelineColumn
                        stage={stage}
                        opportunities={filteredOpportunities}
                        onStageChange={handleStageChange}
                        onEdit={onEdit}
                        onDelete={onDelete}
                        onView={onView}
                        onSelect={handleSelectOpportunity}
                        isSelected={isOpportunitySelected}
                      />
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 列表视图 */}
            {selectedView === "list" && (
              <div className="flex-1">
                <div className="space-y-3">
                  {filteredOpportunities.map((opportunity) => (
                    <OpportunityCard
                      key={opportunity.id}
                      opportunity={opportunity}
                      onStageChange={handleStageChange}
                      onEdit={onEdit}
                      onDelete={onDelete}
                      onView={onView}
                      onSelect={handleSelectOpportunity}
                      isSelected={isOpportunitySelected(opportunity.id)}
                      compact={true}
                    />
                  ))}
                </div>
              </div>
            )}

            {/* 统计视图 */}
            {selectedView === "stats" && (
              <div className="flex-1">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {/* 阶段分布统计 */}
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base">阶段分布</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        {opportunityStageFlow.map((stage) => {
                          const stageConfig = opportunityStageConfig[stage];
                          const stageCount = filteredOpportunities.filter(
                            opp => opp.stage === stage
                          ).length;
                          const percentage = stats.total > 0
                            ? (stageCount / stats.total * 100).toFixed(1)
                            : 0;

                          return (
                            <div key={stage} className="space-y-1">
                              <div className="flex justify-between text-sm">
                                <span>{stageConfig.label}</span>
                                <span>{percentage}%</span>
                              </div>
                              <div className="w-full bg-gray-200 rounded-full h-2">
                                <div
                                  className="bg-blue-600 h-2 rounded-full"
                                  style={{ width: `${percentage}%` }}
                                />
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </CardContent>
                  </Card>

                  {/* 金额分布统计 */}
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base">金额分布</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        <div className="text-center">
                          <div className="text-3xl font-bold">
                            {formatCurrency(stats.total_expected_amount)}
                          </div>
                          <div className="text-sm text-gray-500">预计总金额</div>
                        </div>
                        <div className="space-y-2">
                          <div className="flex justify-between text-sm">
                            <span>平均金额</span>
                            <span>
                              {stats.total > 0
                                ? formatCurrency(stats.total_expected_amount / stats.total)
                                : formatCurrency(0)}
                            </span>
                          </div>
                          <div className="flex justify-between text-sm">
                            <span>最大金额</span>
                            <span>
                              {formatCurrency(
                                Math.max(...filteredOpportunities.map(opp => opp.expected_amount || 0), 0)
                              )}
                            </span>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  {/* 转化漏斗 */}
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base">转化漏斗</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        {opportunityStageFlow.slice(0, -1).map((stage, index) => {
                          const stageCount = filteredOpportunities.filter(
                            opp => opp.stage === stage
                          ).length;
                          const nextStageCount = filteredOpportunities.filter(
                            opp => opp.stage === opportunityStageFlow[index + 1]
                          ).length;
                          const conversionRate = stageCount > 0
                            ? (nextStageCount / stageCount * 100).toFixed(1)
                            : 0;

                          return (
                            <div key={stage} className="space-y-1">
                              <div className="flex justify-between text-sm">
                                <span>{opportunityStageConfig[stage].label}</span>
                                <span>{conversionRate}%</span>
                              </div>
                              <div className="flex gap-1">
                                <div className="flex-1 bg-gray-200 rounded h-2" />
                                <div className="flex-1 bg-green-500 rounded h-2" style={{ width: `${conversionRate}%` }} />
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </DndProvider>
  );
};

export default OpportunityPipeline;