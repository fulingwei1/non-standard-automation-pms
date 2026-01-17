import React from "react";
import { motion } from "framer-motion";
import {
  Target,
  TrendingUp,
  DollarSign,
  Flame,
  Clock,
  CheckCircle2,
  AlertTriangle,
  BarChart3,
  Eye,
  Calendar } from
"lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import {
  OpportunityUtils,
  OPPORTUNITY_STAGES,
  OPPORTUNITY_STAGE_CONFIGS,
  OPPORTUNITY_PRIORITY } from
"./opportunityBoardConstants";

export default function OpportunityBoardOverview({ opportunities = [] }) {
  // 计算统计数据
  const stats = {
    total: opportunities.length,
    hot: opportunities.filter((opp) => OpportunityUtils.isHotOpportunity(opp)).length,
    overdue: opportunities.filter((opp) => OpportunityUtils.isOverdue(opp)).length,
    totalValue: opportunities.reduce((sum, opp) => sum + (opp.expectedAmount || 0), 0),
    expectedRevenue: opportunities.reduce((sum, opp) => sum + OpportunityUtils.calculateExpectedRevenue(opp), 0),
    wonThisMonth: opportunities.filter((opp) => {
      return opp.stage === OPPORTUNITY_STAGES.WON &&
      new Date(opp.createdDate || opp.createdAt).getMonth() === new Date().getMonth();
    }).length
  };

  // 计算阶段分布
  const stageDistribution = Object.values(OPPORTUNITY_STAGES).map((stage) => {
    const config = OPPORTUNITY_STAGE_CONFIGS[stage];
    const stageOpportunities = opportunities.filter((opp) => opp.stage === stage);
    const count = stageOpportunities.length;
    const value = stageOpportunities.reduce((sum, opp) => sum + (opp.expectedAmount || 0), 0);
    const percentage = stats.total > 0 ? (count / stats.total * 100).toFixed(1) : 0;

    return {
      stage,
      label: config.label,
      color: config.color,
      count,
      value,
      percentage,
      probability: config.probability
    };
  });

  // 获取热门机会
  const hotOpportunities = opportunities.
  filter((opp) => OpportunityUtils.isHotOpportunity(opp)).
  slice(0, 5).
  map((opp) => ({
    id: opp.id,
    name: opp.name,
    customerName: opp.customerName,
    expectedAmount: opp.expectedAmount,
    stage: opp.stage,
    score: OpportunityUtils.calculateOpportunityScore(opp),
    priority: opp.priority
  }));

  // 获取超期机会
  const overdueOpportunities = opportunities.
  filter((opp) => OpportunityUtils.isOverdue(opp)).
  slice(0, 5).
  map((opp) => ({
    id: opp.id,
    name: opp.name,
    customerName: opp.customerName,
    expectedCloseDate: opp.expectedCloseDate,
    overdueDays: OpportunityUtils.getOverdueDays(opp),
    expectedAmount: opp.expectedAmount
  }));

  // 获取即将到期的机会（7天内）
  const upcomingOpportunities = opportunities.
  filter((opp) => {
    const expectedDate = new Date(opp.expectedCloseDate);
    const sevenDaysFromNow = new Date();
    sevenDaysFromNow.setDate(sevenDaysFromNow.getDate() + 7);
    return expectedDate >= new Date() && expectedDate <= sevenDaysFromNow;
  }).
  slice(0, 5).
  map((opp) => ({
    id: opp.id,
    name: opp.name,
    customerName: opp.customerName,
    expectedCloseDate: opp.expectedCloseDate,
    expectedAmount: opp.expectedAmount,
    stage: opp.stage
  }));

  // 计算转化率
  const _conversionRates = OpportunityUtils.calculateConversionRates(opportunities);
  const overallConversionRate = opportunities.filter((opp) => opp.stage === OPPORTUNITY_STAGES.WON).length / (
  opportunities.length || 1) * 100;

  return (
    <div className="space-y-6">
      {/* 关键指标卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <motion.div
          whileHover={{ scale: 1.02 }}
          className="bg-surface-1 rounded-xl border border-border p-4">

          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-text-secondary">总机会数</p>
              <p className="text-2xl font-bold text-white mt-1">{stats.total}</p>
              <p className="text-xs text-text-secondary mt-1">
                热门机会: {stats.hot}
              </p>
            </div>
            <div className="bg-blue-500/20 p-3 rounded-lg">
              <Target className="h-6 w-6 text-blue-400" />
            </div>
          </div>
        </motion.div>

        <motion.div
          whileHover={{ scale: 1.02 }}
          className="bg-surface-1 rounded-xl border border-border p-4">

          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-text-secondary">预期收入</p>
              <p className="text-2xl font-bold text-white mt-1">
                ¥{(stats.expectedRevenue / 10000).toFixed(1)}万
              </p>
              <p className="text-xs text-text-secondary mt-1">
                总价值: ¥{(stats.totalValue / 10000).toFixed(1)}万
              </p>
            </div>
            <div className="bg-green-500/20 p-3 rounded-lg">
              <DollarSign className="h-6 w-6 text-green-400" />
            </div>
          </div>
        </motion.div>

        <motion.div
          whileHover={{ scale: 1.02 }}
          className="bg-surface-1 rounded-xl border border-border p-4">

          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-text-secondary">超期机会</p>
              <p className="text-2xl font-bold text-red-400 mt-1">{stats.overdue}</p>
              <p className="text-xs text-text-secondary mt-1">
                本月赢单: {stats.wonThisMonth}
              </p>
            </div>
            <div className="bg-red-500/20 p-3 rounded-lg">
              <AlertTriangle className="h-6 w-6 text-red-400" />
            </div>
          </div>
        </motion.div>

        <motion.div
          whileHover={{ scale: 1.02 }}
          className="bg-surface-1 rounded-xl border border-border p-4">

          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-text-secondary">赢单率</p>
              <p className="text-2xl font-bold text-white mt-1">{overallConversionRate.toFixed(1)}%</p>
              <p className="text-xs text-text-secondary mt-1">
                本月赢单: {stats.wonThisMonth}
              </p>
            </div>
            <div className="bg-emerald-500/20 p-3 rounded-lg">
              <CheckCircle2 className="h-6 w-6 text-emerald-400" />
            </div>
          </div>
        </motion.div>
      </div>

      {/* 阶段分布 */}
      <Card className="bg-surface-1 border-border">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            销售漏斗分布
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {stageDistribution.map((stage) =>
            <motion.div
              key={stage.stage}
              whileHover={{ scale: 1.05 }}
              className="text-center">

                <div className={`w-12 h-12 ${stage.color} rounded-lg mx-auto mb-2 flex items-center justify-center`}>
                  <span className="text-white font-semibold text-sm">{stage.count}</span>
                </div>
                <p className="text-xs text-text-secondary">{stage.label}</p>
                <p className="text-xs text-white font-semibold">{stage.percentage}%</p>
                <p className="text-xs text-text-secondary">
                  {stage.probability}% 成功率
                </p>
              </motion.div>
            )}
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 热门机会 */}
        <Card className="bg-surface-1 border-border">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Flame className="h-5 w-5 text-amber-400" />
              热门机会 ({hotOpportunities.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            {hotOpportunities.length > 0 ?
            <div className="space-y-3">
                {hotOpportunities.map((opp) =>
              <div
                key={opp.id}
                className="flex items-center justify-between p-3 bg-surface-2 rounded-lg">

                    <div className="flex-1">
                      <p className="text-sm font-medium text-white truncate">{opp.name}</p>
                      <p className="text-xs text-text-secondary">{opp.customerName}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-semibold text-white">
                        ¥{OpportunityUtils.formatCurrency(opp.expectedAmount)}
                      </p>
                      <Badge variant="outline" className="text-xs">
                        {opp.score}分
                      </Badge>
                    </div>
                  </div>
              )}
              </div> :

            <div className="text-center py-8">
                <Flame className="h-12 w-12 text-slate-400 mx-auto mb-2" />
                <p className="text-text-secondary">暂无热门机会</p>
              </div>
            }
          </CardContent>
        </Card>

        {/* 超期机会 */}
        <Card className="bg-surface-1 border-border">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-red-400" />
              超期机会 ({overdueOpportunities.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            {overdueOpportunities.length > 0 ?
            <div className="space-y-3">
                {overdueOpportunities.map((opp) =>
              <div
                key={opp.id}
                className="flex items-center justify-between p-3 bg-surface-2 rounded-lg">

                    <div className="flex-1">
                      <p className="text-sm font-medium text-white truncate">{opp.name}</p>
                      <p className="text-xs text-text-secondary">{opp.customerName}</p>
                    </div>
                    <div className="text-right">
                      <Badge variant="destructive" className="text-xs">
                        超期 {opp.overdueDays} 天
                      </Badge>
                      <p className="text-xs text-text-secondary mt-1">
                        {OpportunityUtils.formatDate(opp.expectedCloseDate)}
                      </p>
                    </div>
                  </div>
              )}
              </div> :

            <div className="text-center py-8">
                <CheckCircle2 className="h-12 w-12 text-emerald-400 mx-auto mb-2" />
                <p className="text-text-secondary">暂无超期机会</p>
              </div>
            }
          </CardContent>
        </Card>

        {/* 即将到期 */}
        <Card className="bg-surface-1 border-border">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Clock className="h-5 w-5 text-amber-400" />
              即将到期 ({upcomingOpportunities.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            {upcomingOpportunities.length > 0 ?
            <div className="space-y-3">
                {upcomingOpportunities.map((opp) =>
              <div
                key={opp.id}
                className="flex items-center justify-between p-3 bg-surface-2 rounded-lg">

                    <div className="flex-1">
                      <p className="text-sm font-medium text-white truncate">{opp.name}</p>
                      <p className="text-xs text-text-secondary">{opp.customerName}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-semibold text-white">
                        ¥{OpportunityUtils.formatCurrency(opp.expectedAmount)}
                      </p>
                      <Badge variant="outline" className="text-xs">
                        {OpportunityUtils.formatDate(opp.expectedCloseDate)}
                      </Badge>
                    </div>
                  </div>
              )}
              </div> :

            <div className="text-center py-8">
                <Calendar className="h-12 w-12 text-blue-400 mx-auto mb-2" />
                <p className="text-text-secondary">7天内无到期机会</p>
              </div>
            }
          </CardContent>
        </Card>
      </div>

      {/* 快速统计 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-surface-1 border-border">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="bg-blue-500/20 p-2 rounded-lg">
                <TrendingUp className="h-5 w-5 text-blue-400" />
              </div>
              <div>
                <p className="text-xs text-text-secondary">平均赢单周期</p>
                <p className="text-lg font-semibold text-white">
                  {Math.round(opportunities.reduce((sum, opp) =>
                  sum + OpportunityUtils.calculateSalesCycle(opp), 0) / (opportunities.length || 1))}天
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-surface-1 border-border">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="bg-emerald-500/20 p-2 rounded-lg">
                <DollarSign className="h-5 w-5 text-emerald-400" />
              </div>
              <div>
                <p className="text-xs text-text-secondary">平均赢单金额</p>
                <p className="text-lg font-semibold text-white">
                  ¥{(opportunities.filter((opp) => opp.stage === OPPORTUNITY_STAGES.WON).
                  reduce((sum, opp) => sum + (opp.expectedAmount || 0), 0) / (
                  opportunities.filter((opp) => opp.stage === OPPORTUNITY_STAGES.WON).length || 1) / 10000).toFixed(1)}万
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-surface-1 border-border">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="bg-amber-500/20 p-2 rounded-lg">
                <Target className="h-5 w-5 text-amber-400" />
              </div>
              <div>
                <p className="text-xs text-text-secondary">高优先级机会</p>
                <p className="text-lg font-semibold text-white">
                  {opportunities.filter((opp) => opp.priority === OPPORTUNITY_PRIORITY.HIGH).length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-surface-1 border-border">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="bg-purple-500/20 p-2 rounded-lg">
                <Eye className="h-5 w-5 text-purple-400" />
              </div>
              <div>
                <p className="text-xs text-text-secondary">平均机会评分</p>
                <p className="text-lg font-semibold text-white">
                  {Math.round(opportunities.reduce((sum, opp) =>
                  sum + OpportunityUtils.calculateOpportunityScore(opp), 0) / (opportunities.length || 1))}分
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>);

}