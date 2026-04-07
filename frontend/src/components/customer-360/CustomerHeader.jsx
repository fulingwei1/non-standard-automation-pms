/**
 * Customer Header Component
 * 客户信息头部组件
 * 展示客户基本信息和关键数据
 */

import { cn, formatDate, formatCurrency } from "../../lib/utils";
import {
  customer360TabConfigs,
  getCustomerTypeConfig,
  getCustomerStatusConfig,
  getCustomerIndustryConfig,
  getCustomerSourceConfig,
  getCustomerScoreConfig,
  getRiskLevelConfig,
  calculateCustomerValueScore,
  DEFAULT_CUSTOMER_360_DATA } from
"@/lib/constants/customer360";

/**
 * CustomerHeader - 客户头部信息组件
 * @param {Object} customer - 客户数据对象
 * @param {boolean} loading - 加载状态
 * @param {Function} onTabChange - 切换Tab回调
 */
export function CustomerHeader({ customer, loading = false, onTabChange }) {
  // 如果正在加载，显示骨架屏
  if (loading) {
    return (
      <div className="space-y-4">
        {/* 骨架屏 */}
        <div className="grid grid-cols-12 gap-4">
          <div className="col-span-4">
            <div className="animate-pulse h-32 bg-slate-800 rounded-lg" />
          </div>
          <div className="col-span-8 space-y-3">
            <div className="h-8 bg-slate-700 rounded w-3/4" />
            <div className="h-6 bg-slate-700 rounded w-1/2" />
            <div className="grid grid-cols-3 gap-2">
              <div className="h-4 bg-slate-700 rounded" />
              <div className="h-4 bg-slate-700 rounded" />
              <div className="h-4 bg-slate-700 rounded" />
            </div>
            <div className="h-20 bg-slate-700 rounded" />
          </div>
        </div>

        <div className="grid grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) =>
          <Card key={i}>
              <CardHeader className="pb-2">
                <div className="h-4 bg-slate-700 rounded w-20" />
              </CardHeader>
              <CardContent>
                <div className="h-8 bg-slate-700 rounded" />
              </CardContent>
          </Card>
          )}
        </div>
      </div>);

  }

  // 使用默认数据或传入的客户数据
  const customerData = { ...DEFAULT_CUSTOMER_360_DATA, ...customer };

  // 计算客户价值评分
  const valueScore = calculateCustomerValueScore(customerData);

  // 获取各类配置
  const typeConfig = getCustomerTypeConfig(customerData.customer_type);
  const statusConfig = getCustomerStatusConfig(customerData.status);
  const industryConfig = getCustomerIndustryConfig(customerData.industry);
  const sourceConfig = getCustomerSourceConfig(customerData.source);
  const scoreConfig = getCustomerScoreConfig(customerData.statistics?.customer_score || 0);
  const riskConfig = getRiskLevelConfig(customerData.statistics?.risk_level || 'LOW');

  return (
    <div className="space-y-6">
      {/* 主要信息区域 */}
      <div className="grid grid-cols-12 gap-6">
        {/* 左侧：客户基本信息 */}
        <div className="col-span-4 space-y-4">
          {/* 客户Logo/头像占位 */}
          <div className="h-32 bg-slate-800 rounded-lg flex items-center justify-center">
            <div className="text-4xl text-slate-500">🏢</div>
          </div>

          {/* 客户基本信息卡片 */}
          <Card className="border-slate-700 bg-slate-800/50">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm text-slate-400">基本信息</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {/* 客户名称 */}
              <div>
                <div className="text-sm text-slate-500 mb-1">客户名称</div>
                <div className="text-xl font-semibold text-white truncate">
                  {customerData.customer_name || '未知客户'}
                </div>
                <div className="text-xs text-slate-400 mt-1 font-mono">
                  {customerData.customer_code || '无编号'}
                </div>
              </div>

              {/* 客户类型和状态 */}
              <div className="flex items-center gap-2">
                <Badge className={cn(typeConfig.color, typeConfig.textColor, "text-xs")}>
                  {typeConfig.icon} {typeConfig.label}
                </Badge>
                <Badge className={cn(statusConfig.color, statusConfig.textColor, "text-xs")}>
                  {statusConfig.icon} {statusConfig.label}
                </Badge>
              </div>

              {/* 客户行业 */}
              <div>
                <div className="text-sm text-slate-500 mb-1">所属行业</div>
                <div className="flex items-center gap-2">
                  <span>{industryConfig.icon}</span>
                  <span className="text-white text-sm">{industryConfig.label}</span>
                </div>
              </div>

              {/* 客户来源 */}
              <div>
                <div className="text-sm text-slate-500 mb-1">客户来源</div>
                <div className="flex items-center gap-2">
                  <span>{sourceConfig.icon}</span>
                  <span className="text-white text-sm">{sourceConfig.label}</span>
                </div>
              </div>

              {/* 注册信息 */}
              <div className="grid grid-cols-2 gap-3 pt-2">
                <div>
                  <div className="text-xs text-slate-500 mb-1">成立时间</div>
                  <div className="text-sm text-white">
                    {customerData.established_date ? formatDate(customerData.established_date) : '未知'}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-slate-500 mb-1">员工规模</div>
                  <div className="text-sm text-white">
                    {customerData.business_info?.employee_count ?
                    `${customerData.business_info.employee_count}人` :
                    '未知'}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* 右侧：关键数据和评分 */}
        <div className="col-span-8 space-y-4">
          {/* 关键指标卡片 */}
          <div className="grid grid-cols-4 gap-4">
            {/* 总项目数 */}
            <Card className="border-slate-700 bg-slate-800/50">
              <CardHeader className="pb-2">
                <CardTitle className="text-xs text-slate-400">总项目数</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-white">
                  {customerData.statistics?.total_projects || 0}
                </div>
                <div className="text-xs text-slate-500 mt-1">个</div>
              </CardContent>
            </Card>

            {/* 总合同数 */}
            <Card className="border-slate-700 bg-slate-800/50">
              <CardHeader className="pb-2">
                <CardTitle className="text-xs text-slate-400">总合同数</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-white">
                  {customerData.statistics?.total_contracts || 0}
                </div>
                <div className="text-xs text-slate-500 mt-1">个</div>
              </CardContent>
            </Card>

            {/* 总金额 */}
            <Card className="border-slate-700 bg-slate-800/50">
              <CardHeader className="pb-2">
                <CardTitle className="text-xs text-slate-400">总合同金额</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-white">
                  {formatCurrency(customerData.statistics?.total_amount || 0)}
                </div>
                <div className="text-xs text-slate-500 mt-1">累计</div>
              </CardContent>
            </Card>

            {/* 客户评分 */}
            <Card className="border-slate-700 bg-slate-800/50">
              <CardHeader className="pb-2">
                <CardTitle className="text-xs text-slate-400">客户评分</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-baseline gap-2">
                  <div className="text-2xl font-bold text-white">
                    {customerData.statistics?.customer_score || 0}
                  </div>
                  <Badge className={cn(scoreConfig.color, scoreConfig.textColor, "text-xs")}>
                    {scoreConfig.label}
                  </Badge>
                </div>
                <Progress
                  value={customerData.statistics?.customer_score || 0}
                  className="mt-2 h-1 bg-slate-700" />

              </CardContent>
            </Card>
          </div>

          {/* 客户价值评分 */}
          <Card className="border-slate-700 bg-slate-800/50">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm text-slate-400 flex items-center justify-between">
                <span>客户价值评分</span>
                <span className="text-lg font-semibold text-white">
                  {valueScore.total_score}分
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-5 gap-3">
                {valueScore.breakdown && Object.entries(valueScore.breakdown).map(([key, value]) =>
                <div key={key} className="text-center">
                    <div className="text-xs text-slate-500 mb-1">
                      {key === 'revenue' ? '营收' :
                    key === 'projects' ? '项目' :
                    key === 'contracts' ? '合同' :
                    key === 'activity' ? '活跃度' : '满意度'}
                    </div>
                    <div className="text-sm font-semibold text-white">
                      {value}
                    </div>
                    <Progress value={value || "unknown"} className="mt-1 h-1 bg-slate-700" />
                </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* 联系信息和备注 */}
          <div className="grid grid-cols-2 gap-4">
            {/* 主要联系人 */}
            <Card className="border-slate-700 bg-slate-800/50">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm text-slate-400">主要联系人</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <div>
                  <div className="text-xs text-slate-500">姓名</div>
                  <div className="text-sm text-white">
                    {customerData.contact_person || customerData.legal_representative || '未设置'}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-slate-500">职位</div>
                  <div className="text-sm text-white">
                    {customerData.position || '未设置'}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-slate-500">电话</div>
                  <div className="text-sm text-white">
                    {customerData.phone || '未设置'}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-slate-500">邮箱</div>
                  <div className="text-sm text-white truncate">
                    {customerData.email || '未设置'}
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* 风险等级和最新动态 */}
            <Card className="border-slate-700 bg-slate-800/50">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm text-slate-400">风险评估</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-xs text-slate-500">风险等级</div>
                    <div className="flex items-center gap-2">
                      <span>{riskConfig.icon}</span>
                      <span className="text-sm font-semibold text-white">
                        {riskConfig.label}
                      </span>
                    </div>
                  </div>
                  <Badge className={cn(riskConfig.color, riskConfig.textColor, "text-xs")}>
                    {riskConfig.label}
                  </Badge>
                </div>

                <Separator className="bg-slate-700" />

                {/* 最新动态 */}
                <div>
                  <div className="text-xs text-slate-500 mb-2">最新动态</div>
                  {customerData.recent_activities && customerData.recent_activities?.length > 0 ?
                  <div className="space-y-2 max-h-20 overflow-y-auto">
                      {customerData.recentActivities.slice(0, 3).map((activity, index) =>
                    <div key={index} className="text-xs text-slate-300">
                          <div className="flex items-start gap-2">
                            <span className="text-slate-500">•</span>
                            <span className="flex-1">{activity.description}</span>
                            <span className="text-slate-500 text-xs">
                              {formatDate(activity.date)}
                            </span>
                          </div>
                    </div>
                    )}
                  </div> :

                  <div className="text-xs text-slate-500">暂无动态记录</div>
                  }
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>

      {/* Tab 导航 */}
      <Card className="border-slate-700 bg-slate-800/50">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm text-slate-400">详细信息</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {(customer360TabConfigs || []).map((tab) =>
            <button
              key={tab.value}
              onClick={() => onTabChange && onTabChange(tab.value)}
              className={cn(
                "px-4 py-2 rounded-lg text-sm font-medium transition-all",
                "hover:bg-slate-700/50 border border-slate-600",
                "flex items-center gap-2"
              )}>

                <span>{tab.icon}</span>
                <span>{tab.label}</span>
            </button>
            )}
          </div>
        </CardContent>
      </Card>
    </div>);

}

/**
 * CustomerSummaryStats - 客户汇总统计组件
 * @param {Object} statistics - 统计数据
 */
export function CustomerSummaryStats({ statistics }) {
  const stats = statistics || {};

  return (
    <div className="grid grid-cols-12 gap-4 mb-6">
      <div className="col-span-3">
        <div className="text-xs text-slate-500">年度营收</div>
        <div className="text-xl font-bold text-emerald-400">
          {formatCurrency(stats.annual_revenue || 0)}
        </div>
      </div>
      <div className="col-span-3">
        <div className="text-xs text-slate-500">平均合同额</div>
        <div className="text-xl font-bold text-blue-400">
          {formatCurrency(stats.avg_contract_amount || 0)}
        </div>
      </div>
      <div className="col-span-3">
        <div className="text-xs text-slate-500">最后联系</div>
        <div className="text-xl font-bold text-purple-400">
          {stats.last_contact_date ? formatDate(stats.last_contact_date) : '未联系'}
        </div>
      </div>
      <div className="col-span-3">
        <div className="text-xs text-slate-500">下次联系</div>
        <div className="text-xl font-bold text-amber-400">
          {stats.next_contact_date ? formatDate(stats.next_contact_date) : '未计划'}
        </div>
      </div>
    </div>);

}

export default CustomerHeader;