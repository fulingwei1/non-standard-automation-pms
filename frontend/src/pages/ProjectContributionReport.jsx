import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { projectContributionApi } from '../services/api'
import { PageHeader } from '../components/layout/PageHeader'
import { Card, CardContent, CardHeader, CardTitle, Skeleton } from '../components/ui'
import ContributionChart from '../components/project/ContributionChart'
import { formatCurrency, formatDate } from '../lib/utils'
import { Award, TrendingUp, Clock, CheckCircle2 } from 'lucide-react'

export default function ProjectContributionReport() {
  const { id } = useParams()
  const [loading, setLoading] = useState(true)
  const [report, setReport] = useState(null)
  const [period, setPeriod] = useState(() => {
    const now = new Date()
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
  })

  useEffect(() => {
    fetchReport()
  }, [id, period])

  const fetchReport = async () => {
    try {
      setLoading(true)
      const response = await projectContributionApi.getReport(id, { period })
      setReport(response.data)
    } catch (error) {
      console.error('Failed to load contribution report:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="p-6">
        <Skeleton className="h-12 w-64 mb-6" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
      </div>
    )
  }

  if (!report) {
    return (
      <div className="p-6">
        <PageHeader title="项目贡献度报告" />
        <Card>
          <CardContent className="p-6 text-center text-gray-500">
            无法加载报告数据
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      <PageHeader
        title="项目贡献度报告"
        description={`统计周期: ${period}`}
      />

      {/* 统计概览 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-gray-500">团队成员</p>
            <p className="text-2xl font-bold">{report.total_members}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-gray-500">总任务数</p>
            <p className="text-2xl font-bold">{report.total_task_count}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-gray-500">总工时</p>
            <p className="text-2xl font-bold">{report.total_hours.toFixed(1)}h</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-gray-500">总奖金</p>
            <p className="text-2xl font-bold">{formatCurrency(report.total_bonus)}</p>
          </CardContent>
        </Card>
      </div>

      {/* 贡献度图表 */}
      <ContributionChart contributions={report.contributions || []} />

      {/* TOP贡献者 */}
      {report.top_contributors && report.top_contributors.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>TOP 贡献者</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {report.top_contributors.map((contributor, index) => (
                <div
                  key={contributor.user_id}
                  className="flex items-center justify-between p-3 border rounded-lg"
                >
                  <div className="flex items-center gap-4">
                    <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center text-primary font-bold">
                      {index + 1}
                    </div>
                    <div>
                      <p className="font-medium">{contributor.user_name}</p>
                      <p className="text-sm text-gray-500">
                        贡献度: {contributor.contribution_score.toFixed(1)}
                      </p>
                    </div>
                  </div>
                  <Award className="h-5 w-5 text-yellow-500" />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* 详细贡献列表 */}
      <Card>
        <CardHeader>
          <CardTitle>成员贡献详情</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-3">成员</th>
                  <th className="text-left p-3">任务数</th>
                  <th className="text-left p-3">工时</th>
                  <th className="text-left p-3">交付物</th>
                  <th className="text-left p-3">解决问题</th>
                  <th className="text-left p-3">奖金</th>
                  <th className="text-left p-3">贡献度</th>
                  <th className="text-left p-3">PM评分</th>
                </tr>
              </thead>
              <tbody>
                {report.contributions?.map((contrib) => (
                  <tr key={contrib.user_id} className="border-b hover:bg-gray-50">
                    <td className="p-3 font-medium">{contrib.user_name}</td>
                    <td className="p-3">{contrib.task_count}</td>
                    <td className="p-3">{contrib.actual_hours.toFixed(1)}h</td>
                    <td className="p-3">{contrib.deliverable_count}</td>
                    <td className="p-3">{contrib.issue_resolved}</td>
                    <td className="p-3">{formatCurrency(contrib.bonus_amount)}</td>
                    <td className="p-3 font-semibold">{contrib.contribution_score.toFixed(1)}</td>
                    <td className="p-3">
                      {contrib.pm_rating ? (
                        <span className="text-yellow-500">⭐ {contrib.pm_rating}/5</span>
                      ) : (
                        <span className="text-gray-400">未评分</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
