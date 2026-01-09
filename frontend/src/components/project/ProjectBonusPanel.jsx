import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle, Badge, Button } from '../ui'
import { Award, TrendingUp, DollarSign, Clock } from 'lucide-react'
import { formatCurrency } from '../../lib/utils'
import { projectWorkspaceApi } from '../../services/api'

export default function ProjectBonusPanel({ projectId }) {
  const [loading, setLoading] = useState(true)
  const [bonusData, setBonusData] = useState(null)

  useEffect(() => {
    fetchBonusData()
  }, [projectId])

  const fetchBonusData = async () => {
    try {
      setLoading(true)
      const response = await projectWorkspaceApi.getBonuses(projectId)
      setBonusData(response.data)
    } catch (error) {
      console.error('Failed to load bonus data:', error)
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

  if (!bonusData) {
    return (
      <Card>
        <CardContent className="p-6 text-center text-gray-500">
          无法加载奖金数据
        </CardContent>
      </Card>
    )
  }

  const { rules, calculations, statistics, member_summary } = bonusData

  return (
    <div className="space-y-6">
      {/* 统计概览 */}
      {statistics && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">总计算金额</p>
                  <p className="text-2xl font-bold">
                    {formatCurrency(statistics.total_calculated)}
                  </p>
                </div>
                <TrendingUp className="h-8 w-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">总发放金额</p>
                  <p className="text-2xl font-bold">
                    {formatCurrency(statistics.total_distributed)}
                  </p>
                </div>
                <DollarSign className="h-8 w-8 text-green-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">待发放金额</p>
                  <p className="text-2xl font-bold text-orange-500">
                    {formatCurrency(statistics.pending_amount)}
                  </p>
                </div>
                <Clock className="h-8 w-8 text-orange-500" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* 奖金规则 */}
      {rules && rules.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Award className="h-5 w-5" />
              适用奖金规则
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {rules.map((rule) => (
                <div
                  key={rule.id}
                  className="flex items-center justify-between p-3 border rounded-lg"
                >
                  <div>
                    <p className="font-medium">{rule.rule_name}</p>
                    <p className="text-sm text-gray-500">{rule.bonus_type}</p>
                  </div>
                  {rule.coefficient && (
                    <Badge variant="outline">系数: {rule.coefficient}</Badge>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* 成员奖金分配 */}
      {member_summary && member_summary.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>成员奖金分配</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {member_summary.map((member) => (
                <div
                  key={member.user_id}
                  className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <div className="flex-1">
                    <p className="font-medium">{member.user_name}</p>
                    <div className="flex items-center gap-4 mt-1 text-sm text-gray-500">
                      <span>{member.calculation_count} 次计算</span>
                      <span>{member.distribution_count} 次发放</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-lg">
                      {formatCurrency(member.total_calculated)}
                    </p>
                    <p className="text-sm text-gray-500">
                      已发放: {formatCurrency(member.total_distributed)}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* 计算记录 */}
      {calculations && calculations.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>奖金计算记录</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {calculations.slice(0, 10).map((calc) => (
                <div
                  key={calc.id}
                  className="flex items-center justify-between p-3 border rounded-lg"
                >
                  <div>
                    <p className="font-medium">{calc.user_name}</p>
                    <p className="text-sm text-gray-500">{calc.calculation_code}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-bold">{formatCurrency(calc.calculated_amount)}</p>
                    <Badge variant={calc.status === 'APPROVED' ? 'default' : 'secondary'}>
                      {calc.status}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
