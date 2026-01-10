import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { TrendingUp, Users, DollarSign, BarChart3, AlertTriangle } from 'lucide-react'
import { PageHeader } from '../components/layout'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import { Label } from '../components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs'
import { presalesIntegrationApi } from '../services/api'
import { fadeIn } from '../lib/animations'

export default function PresalesIntegration() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [dashboardData, setDashboardData] = useState(null)
  const [winRatePrediction, setWinRatePrediction] = useState(null)
  const [resourceWaste, setResourceWaste] = useState(null)

  useEffect(() => {
    loadDashboard()
  }, [])

  const loadDashboard = async () => {
    try {
      setLoading(true)
      const response = await presalesIntegrationApi.getDashboard()
      const data = response.data?.data || response.data || response
      setDashboardData(data)
    } catch (err) {
      console.error('Failed to load dashboard:', err)
      setError(err.response?.data?.detail || err.message || '加载数据失败')
    } finally {
      setLoading(false)
    }
  }

  const handlePredictWinRate = async () => {
    // 这里需要用户输入数据，简化处理
    setError('此功能需要输入线索评估数据')
  }

  const handleLoadResourceWaste = async (period) => {
    try {
      setLoading(true)
      const response = await presalesIntegrationApi.getResourceWasteAnalysis(period)
      const data = response.data?.data || response.data || response
      setResourceWaste(data)
    } catch (err) {
      console.error('Failed to load resource waste:', err)
      setError(err.response?.data?.detail || err.message || '加载数据失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={fadeIn}
      className="space-y-6"
    >
      <PageHeader title="售前系统集成" />

      {/* 错误提示 */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {/* 仪表板概览 */}
      {dashboardData && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">年度线索总数</p>
                  <p className="text-2xl font-bold">{dashboardData.total_leads_ytd || 0}</p>
                </div>
                <BarChart3 className="h-8 w-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">中标线索</p>
                  <p className="text-2xl font-bold">{dashboardData.won_leads_ytd || 0}</p>
                </div>
                <TrendingUp className="h-8 w-8 text-green-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">整体中标率</p>
                  <p className="text-2xl font-bold">
                    {dashboardData.overall_win_rate
                      ? `${(dashboardData.overall_win_rate * 100).toFixed(1)}%`
                      : '0%'}
                  </p>
                </div>
                <DollarSign className="h-8 w-8 text-purple-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">浪费工时</p>
                  <p className="text-2xl font-bold">{dashboardData.total_wasted_hours || 0}</p>
                </div>
                <AlertTriangle className="h-8 w-8 text-red-500" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      <Tabs defaultValue="dashboard" className="space-y-4">
        <TabsList>
          <TabsTrigger value="dashboard">仪表板</TabsTrigger>
          <TabsTrigger value="winrate">中标率预测</TabsTrigger>
          <TabsTrigger value="waste">资源浪费分析</TabsTrigger>
        </TabsList>

        {/* 仪表板 */}
        <TabsContent value="dashboard">
          {dashboardData && (
            <Card>
              <CardHeader>
                <CardTitle>月度统计</CardTitle>
              </CardHeader>
              <CardContent>
                {dashboardData.monthly_stats && dashboardData.monthly_stats.length > 0 ? (
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b">
                          <th className="text-left p-2">月份</th>
                          <th className="text-left p-2">总数</th>
                          <th className="text-left p-2">中标</th>
                          <th className="text-left p-2">失败</th>
                          <th className="text-left p-2">中标率</th>
                        </tr>
                      </thead>
                      <tbody>
                        {dashboardData.monthly_stats.map((stat, idx) => (
                          <tr key={idx} className="border-b hover:bg-gray-50">
                            <td className="p-2">{stat.month}</td>
                            <td className="p-2">{stat.total}</td>
                            <td className="p-2 text-green-600">{stat.won}</td>
                            <td className="p-2 text-red-600">{stat.lost}</td>
                            <td className="p-2 font-semibold">
                              {(stat.win_rate * 100).toFixed(1)}%
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500">暂无数据</div>
                )}
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* 中标率预测 */}
        <TabsContent value="winrate">
          <Card>
            <CardHeader>
              <CardTitle>中标率预测</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8 text-gray-500">
                此功能需要从售前评估系统获取数据
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 资源浪费分析 */}
        <TabsContent value="waste">
          <Card>
            <CardHeader>
              <CardTitle>资源浪费分析</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label>分析周期</Label>
                <div className="flex gap-2 mt-2">
                  <Input
                    type="text"
                    placeholder="YYYY-MM 或 YYYY"
                    id="waste-period"
                    className="max-w-xs"
                  />
                  <Button
                    onClick={() => {
                      const period = document.getElementById('waste-period').value
                      if (period) handleLoadResourceWaste(period)
                    }}
                  >
                    查询
                  </Button>
                </div>
              </div>

              {resourceWaste && (
                <div className="space-y-4 mt-4">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                      <div className="text-sm text-gray-600">总线索数</div>
                      <div className="text-xl font-bold">{resourceWaste.total_leads || 0}</div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-600">中标数</div>
                      <div className="text-xl font-bold text-green-600">
                        {resourceWaste.won_leads || 0}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-600">失败数</div>
                      <div className="text-xl font-bold text-red-600">
                        {resourceWaste.lost_leads || 0}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-600">浪费率</div>
                      <div className="text-xl font-bold text-orange-600">
                        {resourceWaste.waste_rate
                          ? `${(resourceWaste.waste_rate * 100).toFixed(1)}%`
                          : '0%'}
                      </div>
                    </div>
                  </div>

                  <div>
                    <div className="text-sm font-semibold mb-2">浪费工时</div>
                    <div className="text-2xl font-bold text-red-600">
                      {resourceWaste.wasted_hours || 0} 小时
                    </div>
                    <div className="text-sm text-gray-600 mt-1">
                      浪费成本: ¥{resourceWaste.wasted_cost || 0}
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </motion.div>
  )
}
