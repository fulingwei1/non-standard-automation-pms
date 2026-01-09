import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle, Badge, Button, Tabs, TabsContent, TabsList, TabsTrigger } from '../ui'
import { AlertCircle, CheckCircle2, XCircle, Clock, Search } from 'lucide-react'
import { formatDate } from '../../lib/utils'
import { projectWorkspaceApi } from '../../services/api'

export default function ProjectIssuePanel({ projectId }) {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [issues, setIssues] = useState([])
  const [solutions, setSolutions] = useState(null)
  const [activeTab, setActiveTab] = useState('all')

  useEffect(() => {
    fetchIssueData()
  }, [projectId])

  const fetchIssueData = async () => {
    try {
      setLoading(true)
      const [issuesRes, solutionsRes] = await Promise.all([
        projectWorkspaceApi.getIssues(projectId),
        projectWorkspaceApi.getSolutions(projectId),
      ])
      setIssues(issuesRes.data?.issues || [])
      setSolutions(solutionsRes.data)
    } catch (error) {
      console.error('Failed to load issue data:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="text-center text-gray-500">加载中...</div>
        </CardContent>
      </Card>
    )
  }

  const openIssues = issues.filter((i) => i.status === 'OPEN' || i.status === 'IN_PROGRESS')
  const resolvedIssues = issues.filter(
    (i) => i.status === 'RESOLVED' || i.status === 'CLOSED' || i.status === 'VERIFIED'
  )

  const filteredIssues =
    activeTab === 'all'
      ? issues
      : activeTab === 'open'
      ? openIssues
      : activeTab === 'resolved'
      ? resolvedIssues
      : issues.filter((i) => i.has_solution)

  return (
    <div className="space-y-6">
      {/* 问题统计 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-gray-500">问题总数</p>
            <p className="text-2xl font-bold">{issues.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-gray-500">待处理</p>
            <p className="text-2xl font-bold text-orange-600">{openIssues.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-gray-500">已解决</p>
            <p className="text-2xl font-bold text-green-600">{resolvedIssues.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-gray-500">解决率</p>
            <p className="text-2xl font-bold">
              {issues.length > 0
                ? ((resolvedIssues.length / issues.length) * 100).toFixed(1)
                : 0}
              %
            </p>
          </CardContent>
        </Card>
      </div>

      {/* 问题列表 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5" />
            项目问题
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="all">全部</TabsTrigger>
              <TabsTrigger value="open">待处理</TabsTrigger>
              <TabsTrigger value="resolved">已解决</TabsTrigger>
              <TabsTrigger value="with-solution">有解决方案</TabsTrigger>
            </TabsList>

            <TabsContent value={activeTab} className="mt-4">
              {filteredIssues.length > 0 ? (
                <div className="space-y-2">
                  {filteredIssues.map((issue) => (
                    <div
                      key={issue.id}
                      className="p-4 border rounded-lg hover:bg-gray-50 transition-colors cursor-pointer"
                      onClick={() => navigate(`/issues/${issue.id}`)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <p className="font-medium">{issue.title}</p>
                            <Badge variant="outline" className="text-xs">
                              {issue.issue_no}
                            </Badge>
                          </div>
                          <div className="flex items-center gap-2">
                            <Badge
                              variant={
                                issue.severity === 'CRITICAL'
                                  ? 'destructive'
                                  : issue.severity === 'MAJOR'
                                  ? 'default'
                                  : 'secondary'
                              }
                            >
                              {issue.severity}
                            </Badge>
                            <Badge variant="outline">{issue.priority}</Badge>
                            {issue.has_solution && (
                              <Badge variant="secondary">
                                <CheckCircle2 className="h-3 w-3 mr-1" />
                                已解决
                              </Badge>
                            )}
                            <span className="text-sm text-gray-500">
                              {issue.assignee_name}
                            </span>
                            <span className="text-sm text-gray-500">
                              {formatDate(issue.report_date)}
                            </span>
                          </div>
                        </div>
                        <Badge
                          variant={
                            issue.status === 'RESOLVED' || issue.status === 'CLOSED'
                              ? 'default'
                              : 'secondary'
                          }
                        >
                          {issue.status}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 text-gray-500">暂无问题</div>
              )}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      {/* 解决方案库 */}
      {solutions && solutions.solutions && solutions.solutions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle2 className="h-5 w-5" />
              解决方案库
            </CardTitle>
          </CardHeader>
          <CardContent>
            {solutions.statistics && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <div className="p-4 border rounded-lg">
                  <p className="text-sm text-gray-500">已解决问题</p>
                  <p className="text-2xl font-bold">
                    {solutions.statistics.resolved_issues}
                  </p>
                </div>
                <div className="p-4 border rounded-lg">
                  <p className="text-sm text-gray-500">有解决方案</p>
                  <p className="text-2xl font-bold text-green-600">
                    {solutions.statistics.issues_with_solution}
                  </p>
                </div>
                <div className="p-4 border rounded-lg">
                  <p className="text-sm text-gray-500">解决覆盖率</p>
                  <p className="text-2xl font-bold">
                    {solutions.statistics.solution_coverage?.toFixed(1)}%
                  </p>
                </div>
              </div>
            )}

            <div className="space-y-2">
              {solutions.solutions.slice(0, 10).map((solution) => (
                <div
                  key={solution.issue_id}
                  className="p-4 border rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center justify-between mb-2">
                    <div>
                      <p className="font-medium">{solution.title}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <Badge variant="outline">{solution.issue_type}</Badge>
                        <Badge variant="outline">{solution.category}</Badge>
                        <span className="text-sm text-gray-500">
                          {formatDate(solution.resolved_at)}
                        </span>
                        <span className="text-sm text-gray-500">
                          {solution.resolved_by}
                        </span>
                      </div>
                    </div>
                  </div>
                  {solution.solution && (
                    <div className="mt-2 p-3 bg-gray-50 rounded text-sm">
                      {solution.solution.substring(0, 200)}
                      {solution.solution.length > 200 && '...'}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
