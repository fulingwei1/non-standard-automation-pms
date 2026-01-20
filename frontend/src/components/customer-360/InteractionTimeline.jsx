/**
 * Customer Interaction Timeline Component
 * 客户互动时间轴组件
 * 展示客户所有互动记录的时间轴视图
 */

import { useState } from "react";
import { Badge } from "../../components/ui/badge";
import { Button } from "../../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Input } from "../../components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../../components/ui/select";
import { Separator } from "../../components/ui/separator";
import { cn, formatDate as _formatDate, formatDateTime } from "../../lib/utils";
import {
  interactionTypeConfigs,
  customer360TabConfigs as _customer360TabConfigs,
  getInteractionTypeConfig,
  formatInteractionType } from
"./customer360Constants";

/**
 * InteractionTimeline - 客户互动时间轴组件
 * @param {Object} props - 组件属性
 * @param {Array} props.interactions - 互动记录列表
 * @param {boolean} props.loading - 加载状态
 * @param {Function} props.onAddInteraction - 添加互动回调
 * @param {Function} props.onEditInteraction - 编辑互动回调
 * @param {Function} props.onDeleteInteraction - 删除互动回调
 */
export function InteractionTimeline({
  interactions = [],
  loading = false,
  onAddInteraction,
  onEditInteraction,
  onDeleteInteraction
}) {
  const [filterType, setFilterType] = useState("all");
  const [_filterStatus, _setFilterStatus] = useState("all");
  const [searchTerm, setSearchTerm] = useState("");

  // 如果正在加载，显示骨架屏
  if (loading) {
    return (
      <Card className="border-slate-700 bg-slate-800/50">
        <CardHeader>
          <CardTitle className="text-base text-slate-400">互动历史</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[...Array(3)].map((_, i) =>
            <div key={i} className="flex gap-4">
                <div className="animate-pulse w-2 h-16 bg-slate-700 rounded-full flex-shrink-0" />
                <div className="flex-1 space-y-2">
                  <div className="h-4 bg-slate-700 rounded w-1/3" />
                  <div className="h-3 bg-slate-700 rounded w-full" />
                  <div className="h-3 bg-slate-700 rounded w-2/3" />
                </div>
            </div>
            )}
          </div>
        </CardContent>
      </Card>);

  }

  // 过滤互动记录
  const filteredInteractions = interactions.
  filter((interaction) => {
    if (filterType !== "all" && interaction.type !== filterType) {return false;}
    if (searchTerm && !interaction.description.toLowerCase().includes(searchTerm.toLowerCase())) {return false;}
    return true;
  }).
  sort((a, b) => new Date(b.interaction_date) - new Date(a.interaction_date));

  // 按日期分组
  const groupedInteractions = filteredInteractions.reduce((groups, interaction) => {
    const date = formatDateTime(interaction.interaction_date).split(' ')[0];
    if (!groups[date]) {
      groups[date] = [];
    }
    groups[date].push(interaction);
    return groups;
  }, {});

  // 获取统计数据
  const getInteractionStats = () => {
    const stats = {
      total: interactions.length,
      byType: {},
      byMonth: {}
    };

    interactions.forEach((interaction) => {
      // 按类型统计
      stats.byType[interaction.type] = (stats.byType[interaction.type] || 0) + 1;

      // 按月份统计
      const month = formatDateTime(interaction.interaction_date).substring(0, 7);
      stats.byMonth[month] = (stats.byMonth[month] || 0) + 1;
    });

    return stats;
  };

  const interactionStats = getInteractionStats();

  return (
    <div className="space-y-4">
      {/* 统计概览 */}
      <Card className="border-slate-700 bg-slate-800/50">
        <CardHeader className="pb-3">
          <CardTitle className="text-base text-slate-400 flex items-center justify-between">
            <span>互动统计</span>
            <Badge variant="outline" className="border-slate-600 text-slate-400">
              共 {interactionStats.total} 次互动
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-5 gap-4">
            {Object.entries(interactionTypeConfigs).map(([type, config]) => {
              const count = interactionStats.byType[type] || 0;
              const percentage = interactionStats.total > 0 ? (count / interactionStats.total * 100).toFixed(1) : 0;

              return (
                <div key={type} className="text-center">
                  <div className="text-xs text-slate-500 mb-2">{config.label}</div>
                  <div className="flex items-baseline justify-center gap-1 mb-1">
                    <span className="text-lg font-bold text-white">{count}</span>
                    <span className="text-xs text-slate-500">次</span>
                  </div>
                  <div className="text-xs text-slate-600">{percentage}%</div>
                </div>);

            })}
          </div>
        </CardContent>
      </Card>

      {/* 筛选和搜索 */}
      <Card className="border-slate-700 bg-slate-800/50">
        <CardHeader className="pb-3">
          <CardTitle className="text-base text-slate-400">筛选与搜索</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-3">
            <div className="flex-1 min-w-[200px]">
              <Input
                placeholder="搜索互动内容..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="bg-slate-800 border-slate-700 text-white placeholder:text-slate-500" />

            </div>
            <Select value={filterType} onValueChange={setFilterType}>
              <SelectTrigger className="w-[160px] bg-slate-800 border-slate-700 text-white">
                <SelectValue placeholder="互动类型" />
              </SelectTrigger>
              <SelectContent className="bg-slate-800 border-slate-700">
                <SelectItem value="all">全部类型</SelectItem>
                {Object.entries(interactionTypeConfigs).map(([type, config]) =>
                <SelectItem key={type} value={type} className="text-white">
                    {config.icon} {config.label}
                </SelectItem>
                )}
              </SelectContent>
            </Select>
            <Button
              onClick={onAddInteraction}
              className="bg-blue-600 hover:bg-blue-700 text-white">

              添加互动
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* 时间轴 */}
      <Card className="border-slate-700 bg-slate-800/50">
        <CardHeader>
          <CardTitle className="text-base text-slate-400">互动时间轴</CardTitle>
        </CardHeader>
        <CardContent>
          {filteredInteractions.length === 0 ?
          <div className="text-center py-8 text-slate-500">
              {searchTerm || filterType !== "all" ? "没有找到匹配的互动记录" : "暂无互动记录"}
          </div> :

          <div className="relative">
              {/* 时间轴线 */}
              <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-slate-700" />

              {/* 互动记录 */}
              {Object.entries(groupedInteractions).map(([date, dayInteractions]) =>
            <div key={date} className="relative mb-8 last:mb-0">
                  {/* 日期标签 */}
                  <div className="absolute left-0 top-0 -translate-x-1/2">
                    <div className="bg-slate-700 px-3 py-1 rounded-lg text-xs font-medium text-white">
                      {date}
                    </div>
                  </div>

                  {/* 当天的互动记录 */}
                  <div className="ml-16 space-y-4">
                    {dayInteractions.map((interaction, index) =>
                <div key={interaction.id || index} className="relative">
                        {/* 连接线 */}
                        {index < dayInteractions.length - 1 &&
                  <div className="absolute left-[-8px] top-12 bottom-0 w-0.5 bg-slate-700" />
                  }

                        {/* 互动卡片 */}
                        <div className="bg-slate-800/50 rounded-lg border border-slate-700 p-4 hover:border-slate-600 transition-colors">
                          <div className="flex items-start justify-between mb-3">
                            {/* 互动类型和日期 */}
                            <div className="flex items-center gap-3">
                              <div className="text-lg">
                                {getInteractionTypeConfig(interaction.type).icon}
                              </div>
                              <div>
                                <Badge className={cn(
                            getInteractionTypeConfig(interaction.type).color,
                            getInteractionTypeConfig(interaction.type).textColor,
                            "text-xs"
                          )}>
                                  {formatInteractionType(interaction.type)}
                                </Badge>
                                <div className="text-xs text-slate-500 mt-1">
                                  {formatDateTime(interaction.interaction_date)}
                                </div>
                              </div>
                            </div>

                            {/* 操作按钮 */}
                            <div className="flex gap-2">
                              {onEditInteraction &&
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => onEditInteraction(interaction)}
                          className="h-8 w-8 p-0 text-slate-400 hover:text-white">

                                  ✏️
                        </Button>
                        }
                              {onDeleteInteraction &&
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => onDeleteInteraction(interaction)}
                          className="h-8 w-8 p-0 text-slate-400 hover:text-red-400">

                                  🗑️
                        </Button>
                        }
                            </div>
                          </div>

                          {/* 互动内容 */}
                          <div className="mb-3">
                            <p className="text-sm text-slate-300 whitespace-pre-wrap">
                              {interaction.description || '无描述'}
                            </p>
                          </div>

                          {/* 参与人员 */}
                          {interaction.participants && interaction.participants.length > 0 &&
                    <div className="flex flex-wrap gap-2">
                              <span className="text-xs text-slate-500">参与人员：</span>
                              {interaction.participants.map((participant, pIndex) =>
                      <Badge
                        key={pIndex}
                        variant="outline"
                        className="border-slate-600 text-slate-400 text-xs">

                                  {participant.name} ({participant.role})
                      </Badge>
                      )}
                    </div>
                    }

                          {/* 附件 */}
                          {interaction.attachments && interaction.attachments.length > 0 &&
                    <div className="mt-3 pt-3 border-t border-slate-700">
                              <div className="text-xs text-slate-500 mb-2">附件：</div>
                              <div className="flex flex-wrap gap-2">
                                {interaction.attachments.map((attachment, aIndex) =>
                        <div
                          key={aIndex}
                          className="flex items-center gap-2 px-2 py-1 bg-slate-700/50 rounded text-xs text-slate-300">

                                    📎 {attachment.name}
                                    <span className="text-slate-500">({(attachment.size / 1024).toFixed(1)}KB)</span>
                        </div>
                        )}
                              </div>
                    </div>
                    }
                        </div>
                </div>
                )}
                  </div>
            </div>
            )}
          </div>
          }
        </CardContent>
      </Card>
    </div>);

}

/**
 * InteractionDetail - 互动详情组件
 * @param {Object} interaction - 互动记录详情
 */
export function InteractionDetail({ interaction }) {
  if (!interaction) {return null;}

  const typeConfig = getInteractionTypeConfig(interaction.type);

  return (
    <Card className="border-slate-700 bg-slate-800/50">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="text-2xl">{typeConfig.icon}</div>
            <div>
              <CardTitle className="text-base text-white">
                {formatInteractionType(interaction.type)}
              </CardTitle>
              <div className="text-sm text-slate-500">
                {formatDateTime(interaction.interaction_date)}
              </div>
            </div>
          </div>
          <Badge className={cn(typeConfig.color, typeConfig.textColor, "text-xs")}>
            {typeConfig.label}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* 互动描述 */}
        <div>
          <div className="text-sm text-slate-500 mb-2">互动内容</div>
          <p className="text-sm text-slate-300 whitespace-pre-wrap">
            {interaction.description || '无描述'}
          </p>
        </div>

        <Separator className="bg-slate-700" />

        {/* 基本信息 */}
        <div className="grid grid-cols-2 gap-4">
          {interaction.duration &&
          <div>
              <div className="text-sm text-slate-500 mb-1">互动时长</div>
              <div className="text-sm text-white">{interaction.duration}</div>
          </div>
          }
          {interaction.location &&
          <div>
              <div className="text-sm text-slate-500 mb-1">地点</div>
              <div className="text-sm text-white">{interaction.location}</div>
          </div>
          }
          {interaction.next_action &&
          <div>
              <div className="text-sm text-slate-500 mb-1">下一步行动</div>
              <div className="text-sm text-white">{interaction.next_action}</div>
          </div>
          }
          {interaction.outcome &&
          <div>
              <div className="text-sm text-slate-500 mb-1">结果</div>
              <div className="text-sm text-white">{interaction.outcome}</div>
          </div>
          }
        </div>

        {/* 参与人员 */}
        {interaction.participants && interaction.participants.length > 0 &&
        <div>
            <div className="text-sm text-slate-500 mb-2">参与人员</div>
            <div className="space-y-2">
              {interaction.participants.map((participant, index) =>
            <div key={index} className="flex items-center justify-between py-2 border-b border-slate-700 last:border-b-0">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center text-sm">
                      {participant.name.charAt(0)}
                    </div>
                    <div>
                      <div className="text-sm font-medium text-white">{participant.name}</div>
                      <div className="text-xs text-slate-500">{participant.role}</div>
                    </div>
                  </div>
                  <div className="text-xs text-slate-500">
                    {participant.department}
                  </div>
            </div>
            )}
            </div>
        </div>
        }
      </CardContent>
    </Card>);

}

export default InteractionTimeline;