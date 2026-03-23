/**
 * Customer Purchase History Component
 * 客户采购历史组件
 * 展示客户所有采购记录和统计分析
 */

import { useState } from "react";
import { cn, formatDate, formatCurrency } from "../../lib/utils";
import {
  contractStatusConfigs,
  getContractStatusConfig,
  formatContractStatus } from
"@/lib/constants/customer360";

/**
 * PurchaseHistory - 客户采购历史组件
 * @param {Object} props - 组件属性
 * @param {Array} props.purchases - 采购记录列表
 * @param {boolean} props.loading - 加载状态
 * @param {Function} props.onAddPurchase - 添加采购回调
 * @param {Function} props.onEditPurchase - 编辑采购回调
 * @param {Function} props.onDeletePurchase - 删除采购回调
 */
export function PurchaseHistory({
  purchases = [],
  loading = false,
  onAddPurchase,
  onEditPurchase,
  onDeletePurchase
}) {
  const [filterStatus, setFilterStatus] = useState("all");
  const [filterYear, setFilterYear] = useState("all");
  const [searchTerm, setSearchTerm] = useState("");

  // 如果正在加载，显示骨架屏
  if (loading) {
    return (
      <Card className="border-slate-700 bg-slate-800/50">
        <CardHeader>
          <CardTitle className="text-base text-slate-400">采购记录</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[...Array(3)].map((_, i) =>
            <div key={i} className="animate-pulse">
                <div className="h-4 bg-slate-700 rounded mb-2 w-1/4" />
                <div className="h-3 bg-slate-700 rounded mb-2" />
                <div className="h-8 bg-slate-700 rounded w-1/3" />
            </div>
            )}
          </div>
        </CardContent>
      </Card>);

  }

  // 过滤采购记录
  const filteredPurchases = purchases.
  filter((purchase) => {
    if (filterStatus !== "all" && purchase.status !== filterStatus) {return false;}
    if (filterYear !== "all") {
      const purchaseYear = new Date(purchase.contract_date || purchase.created_at).getFullYear().toString();
      if (purchaseYear !== filterYear) {return false;}
    }
    if (searchTerm && !purchase.project_name.toLowerCase().includes(searchTerm.toLowerCase())) {return false;}
    return true;
  }).
  sort((a, b) => new Date(b.contract_date || b.created_at) - new Date(a.contract_date || a.created_at));

  // 获取统计数据
  const getPurchaseStats = () => {
    const stats = {
      total: purchases.length,
      totalAmount: 0,
      avgAmount: 0,
      byStatus: {},
      byYear: {},
      byType: {}
    };

    (purchases || []).forEach((purchase) => {
      const amount = Number(purchase.contract_amount || purchase.total_amount || 0);
      stats.totalAmount += amount;

      // 按状态统计
      const status = purchase.status || 'DRAFT';
      stats.byStatus[status] = (stats.byStatus[status] || 0) + 1;

      // 按年份统计
      const year = new Date(purchase.contract_date || purchase.created_at).getFullYear().toString();
      stats.byYear[year] = (stats.byYear[year] || 0) + amount;

      // 按类型统计
      const type = purchase.project_type || purchase.product_type || 'OTHER';
      stats.byType[type] = (stats.byType[type] || 0) + 1;
    });

    stats.avgAmount = stats.total > 0 ? stats.totalAmount / stats.total : 0;

    return stats;
  };

  const purchaseStats = getPurchaseStats();

  // 获取年度统计
  const getYearStats = () => {
    const years = [...new Set((purchases || []).map((p) =>
    new Date(p.contract_date || p.created_at).getFullYear()
    ))].sort((a, b) => b - a);

    return (years || []).map((year) => {
      const yearPurchases = (purchases || []).filter((p) =>
      new Date(p.contract_date || p.created_at).getFullYear() === year
      );
      const yearTotal = (yearPurchases || []).reduce((sum, p) =>
      sum + (Number(p.contract_amount || p.total_amount) || 0), 0
      );

      return {
        year,
        count: yearPurchases.length,
        total: yearTotal,
        avg: yearTotal / yearPurchases.length
      };
    });
  };

  const yearStats = getYearStats();

  return (
    <div className="space-y-4">
      {/* 统计概览 */}
      <div className="grid grid-cols-4 gap-4">
        <Card className="border-slate-700 bg-slate-800/50">
          <CardContent className="p-4">
            <div className="text-sm text-slate-500 mb-1">合同总数</div>
            <div className="text-2xl font-bold text-white">
              {purchaseStats.total}
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-700 bg-slate-800/50">
          <CardContent className="p-4">
            <div className="text-sm text-slate-500 mb-1">合同总额</div>
            <div className="text-2xl font-bold text-emerald-400">
              {formatCurrency(purchaseStats.totalAmount)}
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-700 bg-slate-800/50">
          <CardContent className="p-4">
            <div className="text-sm text-slate-500 mb-1">平均合同额</div>
            <div className="text-2xl font-bold text-blue-400">
              {formatCurrency(purchaseStats.avgAmount)}
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-700 bg-slate-800/50">
          <CardContent className="p-4">
            <div className="text-sm text-slate-500 mb-1">本年度合同</div>
            <div className="text-2xl font-bold text-purple-400">
              {yearStats.length > 0 ? yearStats[0].count : 0}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 筛选和搜索 */}
      <Card className="border-slate-700 bg-slate-800/50">
        <CardHeader className="pb-3">
          <CardTitle className="text-base text-slate-400">筛选与搜索</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-3">
            <div className="flex-1 min-w-[200px]">
              <Input
                placeholder="搜索项目名称..."
                value={searchTerm || "unknown"}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="bg-slate-800 border-slate-700 text-white placeholder:text-slate-500" />

            </div>
            <Select value={filterStatus || "unknown"} onValueChange={setFilterStatus}>
              <SelectTrigger className="w-[160px] bg-slate-800 border-slate-700 text-white">
                <SelectValue placeholder="合同状态" />
              </SelectTrigger>
              <SelectContent className="bg-slate-800 border-slate-700">
                <SelectItem value="all">全部状态</SelectItem>
                {Object.entries(contractStatusConfigs).map(([status, config]) =>
                <SelectItem key={status} value={status || "unknown"} className="text-white">
                    {config.icon} {config.label}
                </SelectItem>
                )}
              </SelectContent>
            </Select>
            <Select value={filterYear || "unknown"} onValueChange={setFilterYear}>
              <SelectTrigger className="w-[140px] bg-slate-800 border-slate-700 text-white">
                <SelectValue placeholder="年份" />
              </SelectTrigger>
              <SelectContent className="bg-slate-800 border-slate-700">
                <SelectItem value="all">全部年份</SelectItem>
                {[...new Set((yearStats || []).map((s) => s.year))].sort((a, b) => b - a).map((year) =>
                <SelectItem key={year} value={year || "unknown"} className="text-white">
                    {year}年
                </SelectItem>
                )}
              </SelectContent>
            </Select>
            <Button
              onClick={onAddPurchase}
              className="bg-blue-600 hover:bg-blue-700 text-white">

              添加合同
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* 年度统计 */}
      {yearStats.length > 0 &&
      <Card className="border-slate-700 bg-slate-800/50">
          <CardHeader className="pb-3">
            <CardTitle className="text-base text-slate-400">年度统计</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {yearStats.slice(0, 5).map((stat, _index) =>
            <div key={stat.year} className="flex items-center justify-between py-2 border-b border-slate-700 last:border-b-0">
                  <div className="flex items-center gap-4">
                    <div className="text-sm font-medium text-white">
                      {stat.year}年
                    </div>
                    <div className="text-sm text-slate-400">
                      {stat.count} 个合同
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-sm text-emerald-400">
                      {formatCurrency(stat.total)}
                    </div>
                    <div className="text-sm text-slate-500">
                      平均 {formatCurrency(stat.avg)}
                    </div>
                  </div>
            </div>
            )}
            </div>
          </CardContent>
      </Card>
      }

      {/* 采购记录列表 */}
      <Card className="border-slate-700 bg-slate-800/50">
        <CardHeader>
          <CardTitle className="text-base text-slate-400">合同列表</CardTitle>
        </CardHeader>
        <CardContent>
          {filteredPurchases.length === 0 ?
          <div className="text-center py-8 text-slate-500">
              {searchTerm || filterStatus !== "all" || filterYear !== "all" ?
            "没有找到匹配的合同记录" :
            "暂无合同记录"
            }
          </div> :

          <div className="space-y-3">
              {(filteredPurchases || []).map((purchase) => {
              const statusConfig = getContractStatusConfig(purchase.status || 'DRAFT');
              const contractDate = purchase.contract_date || purchase.created_at;

              return (
                <div key={purchase.id} className="bg-slate-800/50 rounded-lg border border-slate-700 p-4 hover:border-slate-600 transition-colors">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="text-lg font-semibold text-white">
                            {purchase.project_name || purchase.product_name || '未命名项目'}
                          </h3>
                          <Badge className={cn(
                          statusConfig.color,
                          statusConfig.textColor,
                          "text-xs"
                        )}>
                            {formatContractStatus(purchase.status || 'DRAFT')}
                          </Badge>
                        </div>
                        <div className="flex flex-wrap gap-4 text-sm text-slate-500">
                          <div>合同编号: {purchase.contract_no || purchase.project_code || '无编号'}</div>
                          <div>签约日期: {contractDate ? formatDate(contractDate) : '未知'}</div>
                          <div>负责人: {purchase.sales_manager || purchase.project_manager || '未分配'}</div>
                        </div>
                      </div>

                      <div className="text-right">
                        <div className="text-2xl font-bold text-emerald-400 mb-1">
                          {formatCurrency(purchase.contract_amount || purchase.total_amount || 0)}
                        </div>
                        <div className="text-xs text-slate-500">
                          {purchase.currency || 'CNY'}
                        </div>
                      </div>
                    </div>

                    {/* 项目详情 */}
                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div>
                        <span className="text-slate-500">设备类型:</span>
                        <span className="text-white ml-2">{purchase.machine_type || '未指定'}</span>
                      </div>
                      <div>
                        <span className="text-slate-500">项目阶段:</span>
                        <span className="text-white ml-2">{purchase.project_stage || '未开始'}</span>
                      </div>
                      <div>
                        <span className="text-slate-500">交付周期:</span>
                        <span className="text-white ml-2">{purchase.delivery_period || '未确定'}天</span>
                      </div>
                    </div>

                    {/* 项目描述 */}
                    {purchase.description &&
                  <div className="mt-3 pt-3 border-t border-slate-700">
                        <p className="text-sm text-slate-300">
                          {purchase.description}
                        </p>
                  </div>
                  }

                    {/* 操作按钮 */}
                    <div className="flex justify-end gap-2 mt-4">
                      {onEditPurchase &&
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => onEditPurchase(purchase)}
                      className="border-slate-600 text-slate-300 hover:text-white hover:border-slate-500">

                          编辑
                    </Button>
                    }
                      {onDeletePurchase &&
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => onDeletePurchase(purchase)}
                      className="border-slate-600 text-slate-300 hover:text-red-400 hover:border-red-500">

                          删除
                    </Button>
                    }
                    </div>
                </div>);

            })}
          </div>
          }
        </CardContent>
      </Card>
    </div>);

}

/**
 * PurchaseDetail - 采购详情组件
 * @param {Object} purchase - 采购记录详情
 */
export function PurchaseDetail({ purchase }) {
  if (!purchase) {return null;}

  const statusConfig = getContractStatusConfig(purchase.status || 'DRAFT');

  return (
    <Card className="border-slate-700 bg-slate-800/50">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-xl text-white mb-2">
              {purchase.project_name || purchase.product_name || '未命名项目'}
            </CardTitle>
            <div className="flex items-center gap-3">
              <Badge className={cn(
                statusConfig.color,
                statusConfig.textColor,
                "text-sm"
              )}>
                {formatContractStatus(purchase.status || 'DRAFT')}
              </Badge>
              <span className="text-sm text-slate-500">
                {purchase.contract_no || purchase.project_code || '无编号'}
              </span>
            </div>
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold text-emerald-400">
              {formatCurrency(purchase.contract_amount || purchase.total_amount || 0)}
            </div>
            <div className="text-sm text-slate-500">
              {purchase.currency || 'CNY'}
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* 基本信息 */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <div className="text-sm text-slate-500 mb-1">签约日期</div>
            <div className="text-sm text-white">
              {purchase.contract_date ? formatDate(purchase.contract_date) : '未知'}
            </div>
          </div>
          <div>
            <div className="text-sm text-slate-500 mb-1">开始日期</div>
            <div className="text-sm text-white">
              {purchase.start_date ? formatDate(purchase.start_date) : '未知'}
            </div>
          </div>
          <div>
            <div className="text-sm text-slate-500 mb-1">预计完成</div>
            <div className="text-sm text-white">
              {purchase.expected_completion_date ? formatDate(purchase.expected_completion_date) : '未知'}
            </div>
          </div>
          <div>
            <div className="text-sm text-slate-500 mb-1">交付周期</div>
            <div className="text-sm text-white">
              {purchase.delivery_period || 0} 天
            </div>
          </div>
        </div>

        <Separator className="bg-slate-700" />

        {/* 项目信息 */}
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-white">项目信息</h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-slate-500">设备类型:</span>
              <span className="text-white ml-2">{purchase.machine_type || '未指定'}</span>
            </div>
            <div>
              <span className="text-slate-500">项目阶段:</span>
              <span className="text-white ml-2">{purchase.project_stage || '未开始'}</span>
            </div>
            <div>
              <span className="text-slate-500">技术要求:</span>
              <span className="text-white ml-2">{purchase.tech_requirements || '无特殊要求'}</span>
            </div>
            <div>
              <span className="text-slate-500">验收标准:</span>
              <span className="text-white ml-2">{purchase.acceptance_criteria || '按标准验收'}</span>
            </div>
          </div>
        </div>

        {/* 商务信息 */}
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-white">商务信息</h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-slate-500">销售经理:</span>
              <span className="text-white ml-2">{purchase.sales_manager || '未分配'}</span>
            </div>
            <div>
              <span className="text-slate-500">项目经理:</span>
              <span className="text-white ml-2">{purchase.project_manager || '未分配'}</span>
            </div>
            <div>
              <span className="text-slate-500">付款方式:</span>
              <span className="text-white ml-2">{payment_terms[(payment_terms || []).find((t) => t.value === purchase.payment_terms)?.value] || '未指定'}</span>
            </div>
            <div>
              <span className="text-slate-500">质保期:</span>
              <span className="text-white ml-2">{purchase.warranty_period || 12} 个月</span>
            </div>
          </div>
        </div>

        {/* 项目描述 */}
        {purchase.description &&
        <div>
            <h3 className="text-sm font-medium text-white mb-2">项目描述</h3>
            <p className="text-sm text-slate-300 whitespace-pre-wrap">
              {purchase.description}
            </p>
        </div>
        }

        {/* 附件列表 */}
        {purchase.attachments && purchase.attachments?.length > 0 &&
        <div>
            <h3 className="text-sm font-medium text-white mb-2">相关附件</h3>
            <div className="space-y-2">
              {(purchase.attachments || []).map((attachment, index) =>
            <div
              key={index}
              className="flex items-center justify-between p-2 bg-slate-700/50 rounded text-sm">

                  <div className="flex items-center gap-2">
                    <span>📎</span>
                    <span className="text-slate-300">{attachment.name}</span>
                  </div>
                  <div className="text-slate-500">
                    {(attachment.size / 1024).toFixed(1)}KB
                  </div>
            </div>
            )}
            </div>
        </div>
        }
      </CardContent>
    </Card>);

}

// 付款方式选项
const payment_terms = {
  advance: "预付款",
  progress: "按进度付款",
  milestone: "里程碑付款",
  delivery: "交货付款",
  acceptance: "验收付款"
};

export default PurchaseHistory;