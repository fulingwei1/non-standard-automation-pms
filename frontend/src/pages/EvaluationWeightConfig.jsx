import React, { useState, useMemo, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  Settings,
  Save,
  RotateCcw,
  AlertCircle,
  CheckCircle2,
  Users,
  Briefcase,
  TrendingUp,
  Info,
  Percent,
  Edit3,
  History
} from 'lucide-react'
import { cn } from '../lib/utils'
import { performanceApi } from '../services/api'

const EvaluationWeightConfig = () => {
  // 默认权重配置
  const defaultWeights = {
    deptManager: 50,
    projectManager: 50
  }

  const [weights, setWeights] = useState(defaultWeights)
  const [isDirty, setIsDirty] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)

  // 配置历史记录
  const [configHistory, setConfigHistory] = useState([
    {
      id: 1,
      date: '2024-12-01',
      operator: '李HR',
      deptWeight: 50,
      projectWeight: 50,
      reason: '初始配置'
    },
    {
      id: 2,
      date: '2024-06-15',
      operator: '张HR',
      deptWeight: 40,
      projectWeight: 60,
      reason: '根据公司战略调整，加大项目评价权重'
    },
    {
      id: 3,
      date: '2024-01-10',
      operator: '王HR',
      deptWeight: 60,
      projectWeight: 40,
      reason: '年初配置，强化部门管理'
    }
  ])

  // 影响统计
  const [impactStatistics, setImpactStatistics] = useState({
    totalEmployees: 156,
    affectedEmployees: 89, // 参与项目的员工
    departments: 8,
    activeProjects: 12
  })

  // 加载当前权重配置
  useEffect(() => {
    loadWeightConfig()
  }, [])

  const loadWeightConfig = async () => {
    try {
      setIsLoading(true)
      setError(null)
      const response = await performanceApi.getWeightConfig()

      // 设置权重值
      setWeights({
        deptManager: response.data.dept_manager_weight || response.data.deptManagerWeight || 50,
        projectManager: response.data.project_manager_weight || response.data.projectManagerWeight || 50
      })

      // 设置配置历史
      if (response.data.history) {
        setConfigHistory(response.data.history.map(record => ({
          id: record.id,
          date: record.updated_at || record.updatedAt || record.date,
          operator: record.updated_by_name || record.updatedByName || record.operator || '系统',
          deptWeight: record.dept_manager_weight || record.deptManagerWeight || 50,
          projectWeight: record.project_manager_weight || record.projectManagerWeight || 50,
          reason: record.reason || record.description || '配置更新'
        })))
      }

      // 设置影响统计(如果API返回)
      if (response.data.statistics) {
        setImpactStatistics({
          totalEmployees: response.data.statistics.total_employees || response.data.statistics.totalEmployees || 156,
          affectedEmployees: response.data.statistics.affected_employees || response.data.statistics.affectedEmployees || 89,
          departments: response.data.statistics.departments || 8,
          activeProjects: response.data.statistics.active_projects || response.data.statistics.activeProjects || 12
        })
      }

    } catch (err) {
      console.error('加载权重配置失败:', err)
      setError(err.response?.data?.detail || '加载失败')
      // Fallback to default values (already set)
    } finally {
      setIsLoading(false)
    }
  }

  // 处理权重变化
  const handleWeightChange = (type, value) => {
    const numValue = Number(value)
    if (numValue < 0 || numValue > 100) return

    if (type === 'dept') {
      setWeights({
        deptManager: numValue,
        projectManager: 100 - numValue
      })
    } else {
      setWeights({
        deptManager: 100 - numValue,
        projectManager: numValue
      })
    }
    setIsDirty(true)
  }

  // 重置为默认值
  const handleReset = () => {
    if (!confirm('确认重置为默认权重配置吗？（部门50%、项目50%）')) {
      return
    }
    setWeights(defaultWeights)
    setIsDirty(true)
  }

  // 保存配置
  const handleSave = async () => {
    if (weights.deptManager + weights.projectManager !== 100) {
      alert('权重总和必须为100%')
      return
    }

    if (!confirm(`确认保存权重配置吗？\n\n部门经理权重：${weights.deptManager}%\n项目经理权重：${weights.projectManager}%\n\n此配置将影响所有员工的绩效计算`)) {
      return
    }

    setIsSaving(true)
    try {
      await performanceApi.updateWeightConfig({
        dept_manager_weight: weights.deptManager,
        project_manager_weight: weights.projectManager
      })
      setIsDirty(false)
      alert('权重配置保存成功！')
      // 重新加载配置以更新历史记录
      await loadWeightConfig()
    } catch (err) {
      console.error('保存权重配置失败:', err)
      alert('保存失败: ' + (err.response?.data?.detail || '请稍后重试'))
    } finally {
      setIsSaving(false)
    }
  }

  // 验证权重总和
  const totalWeight = weights.deptManager + weights.projectManager
  const isValidWeight = totalWeight === 100

  // 动画配置
  const fadeIn = {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.4 }
  }

  // 加载状态
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin h-12 w-12 border-2 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"></div>
          <p className="text-slate-400">加载配置中...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      <motion.div
        className="max-w-5xl mx-auto space-y-6"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5 }}
      >
        {/* 页面标题 */}
        <motion.div {...fadeIn}>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-white mb-2">绩效评价权重配置</h1>
              <p className="text-slate-400">调整部门经理和项目经理的评价权重分配</p>
            </div>
            <Settings className="h-12 w-12 text-blue-400" />
          </div>
        </motion.div>

        {/* 错误提示 */}
        {error && (
          <motion.div {...fadeIn}>
            <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4">
              <div className="flex items-center gap-3">
                <AlertCircle className="h-5 w-5 text-red-400" />
                <p className="text-red-300">{error}</p>
              </div>
            </div>
          </motion.div>
        )}

        {/* 当前配置卡片 */}
        <motion.div {...fadeIn} transition={{ delay: 0.1 }}>
          <div className="bg-gradient-to-r from-blue-500/10 to-purple-500/10 rounded-xl p-6 border border-blue-500/20">
            <div className="flex items-center gap-3 mb-6">
              <Info className="h-5 w-5 text-blue-400" />
              <h2 className="text-xl font-bold text-white">当前权重配置</h2>
              {isDirty && (
                <span className="px-3 py-1 bg-amber-500/20 text-amber-400 text-sm rounded-full">
                  未保存
                </span>
              )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* 部门经理权重 */}
              <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700/50">
                <div className="flex items-center gap-3 mb-4">
                  <div className="h-12 w-12 rounded-full bg-blue-500/20 flex items-center justify-center">
                    <Users className="h-6 w-6 text-blue-400" />
                  </div>
                  <div>
                    <h3 className="text-white font-medium">部门经理评价</h3>
                    <p className="text-sm text-slate-400">直属上级评价</p>
                  </div>
                </div>

                <div className="space-y-4">
                  <div className="flex items-center gap-4">
                    <input
                      type="number"
                      min="0"
                      max="100"
                      value={weights.deptManager}
                      onChange={(e) => handleWeightChange('dept', e.target.value)}
                      className="w-24 h-12 px-4 text-center text-2xl font-bold bg-slate-900/50 border-2 border-slate-700 rounded-lg text-white focus:outline-none focus:border-blue-500"
                    />
                    <Percent className="h-6 w-6 text-slate-400" />
                    <input
                      type="range"
                      min="0"
                      max="100"
                      value={weights.deptManager}
                      onChange={(e) => handleWeightChange('dept', e.target.value)}
                      className="flex-1 h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
                    />
                  </div>
                  <p className="text-sm text-slate-400">
                    部门经理根据员工日常表现、工作态度、部门贡献进行评价
                  </p>
                </div>
              </div>

              {/* 项目经理权重 */}
              <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700/50">
                <div className="flex items-center gap-3 mb-4">
                  <div className="h-12 w-12 rounded-full bg-purple-500/20 flex items-center justify-center">
                    <Briefcase className="h-6 w-6 text-purple-400" />
                  </div>
                  <div>
                    <h3 className="text-white font-medium">项目经理评价</h3>
                    <p className="text-sm text-slate-400">项目绩效评价</p>
                  </div>
                </div>

                <div className="space-y-4">
                  <div className="flex items-center gap-4">
                    <input
                      type="number"
                      min="0"
                      max="100"
                      value={weights.projectManager}
                      onChange={(e) => handleWeightChange('project', e.target.value)}
                      className="w-24 h-12 px-4 text-center text-2xl font-bold bg-slate-900/50 border-2 border-slate-700 rounded-lg text-white focus:outline-none focus:border-purple-500"
                    />
                    <Percent className="h-6 w-6 text-slate-400" />
                    <input
                      type="range"
                      min="0"
                      max="100"
                      value={weights.projectManager}
                      onChange={(e) => handleWeightChange('project', e.target.value)}
                      className="flex-1 h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-purple-500"
                    />
                  </div>
                  <p className="text-sm text-slate-400">
                    项目经理根据员工在项目中的表现、任务完成情况进行评价
                  </p>
                </div>
              </div>
            </div>

            {/* 权重总和验证 */}
            <div className={cn(
              'mt-6 p-4 rounded-lg border-2',
              isValidWeight
                ? 'bg-emerald-500/10 border-emerald-500/30'
                : 'bg-red-500/10 border-red-500/30'
            )}>
              <div className="flex items-center gap-3">
                {isValidWeight ? (
                  <CheckCircle2 className="h-5 w-5 text-emerald-400" />
                ) : (
                  <AlertCircle className="h-5 w-5 text-red-400" />
                )}
                <div className="flex-1">
                  <div className="flex items-center gap-4">
                    <span className={cn(
                      'font-medium',
                      isValidWeight ? 'text-emerald-400' : 'text-red-400'
                    )}>
                      权重总和: {totalWeight}%
                    </span>
                    {isValidWeight ? (
                      <span className="text-emerald-300 text-sm">✓ 配置正确</span>
                    ) : (
                      <span className="text-red-300 text-sm">✗ 总和必须为100%</span>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* 操作按钮 */}
            <div className="mt-6 flex items-center justify-between">
              <button
                onClick={handleReset}
                className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg font-medium transition-colors flex items-center gap-2"
              >
                <RotateCcw className="h-4 w-4" />
                重置为默认
              </button>

              <button
                onClick={handleSave}
                disabled={!isDirty || !isValidWeight || isSaving}
                className="px-6 py-2 bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 disabled:from-slate-700 disabled:to-slate-700 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-all flex items-center gap-2"
              >
                <Save className="h-4 w-4" />
                {isSaving ? '保存中...' : '保存配置'}
              </button>
            </div>
          </div>
        </motion.div>

        {/* 影响范围统计 */}
        <motion.div {...fadeIn} transition={{ delay: 0.2 }}>
          <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700/50">
            <div className="flex items-center gap-3 mb-6">
              <TrendingUp className="h-5 w-5 text-purple-400" />
              <h3 className="text-xl font-bold text-white">影响范围统计</h3>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-4 bg-slate-900/50 rounded-lg border border-slate-700/50">
                <p className="text-sm text-slate-400 mb-2">总员工数</p>
                <p className="text-3xl font-bold text-blue-400">{impactStatistics.totalEmployees}</p>
              </div>

              <div className="p-4 bg-slate-900/50 rounded-lg border border-slate-700/50">
                <p className="text-sm text-slate-400 mb-2">受影响员工</p>
                <p className="text-3xl font-bold text-purple-400">{impactStatistics.affectedEmployees}</p>
                <p className="text-xs text-slate-500 mt-1">参与项目的员工</p>
              </div>

              <div className="p-4 bg-slate-900/50 rounded-lg border border-slate-700/50">
                <p className="text-sm text-slate-400 mb-2">涉及部门</p>
                <p className="text-3xl font-bold text-emerald-400">{impactStatistics.departments}</p>
              </div>

              <div className="p-4 bg-slate-900/50 rounded-lg border border-slate-700/50">
                <p className="text-sm text-slate-400 mb-2">活跃项目</p>
                <p className="text-3xl font-bold text-amber-400">{impactStatistics.activeProjects}</p>
              </div>
            </div>

            <div className="mt-4 p-4 bg-blue-500/10 rounded-lg border border-blue-500/20">
              <div className="flex items-start gap-3">
                <Info className="h-5 w-5 text-blue-400 mt-0.5 flex-shrink-0" />
                <div className="text-sm text-slate-300">
                  <p className="font-medium text-white mb-1">说明</p>
                  <p>• 对于参与项目的员工，最终得分 = 部门经理评分 × 部门权重 + 项目经理评分 × 项目权重</p>
                  <p>• 对于未参与项目的员工，直接使用部门经理评分作为最终得分</p>
                  <p>• 参与多个项目的员工，项目经理评分为各项目评分的加权平均</p>
                </div>
              </div>
            </div>
          </div>
        </motion.div>

        {/* 配置示例 */}
        <motion.div {...fadeIn} transition={{ delay: 0.3 }}>
          <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700/50">
            <div className="flex items-center gap-3 mb-6">
              <Edit3 className="h-5 w-5 text-emerald-400" />
              <h3 className="text-xl font-bold text-white">计算示例</h3>
            </div>

            <div className="space-y-4">
              {/* 示例1：参与项目 */}
              <div className="p-4 bg-slate-900/30 rounded-lg border border-slate-700/50">
                <h4 className="text-white font-medium mb-3">示例1：员工参与1个项目</h4>
                <div className="space-y-2 text-sm text-slate-300">
                  <p>• 部门经理评分：85分（权重 {weights.deptManager}%）</p>
                  <p>• 项目经理评分：90分（权重 {weights.projectManager}%）</p>
                  <p className="pt-2 border-t border-slate-700/50 text-blue-400 font-medium">
                    最终得分 = 85 × {weights.deptManager}% + 90 × {weights.projectManager}%
                    = {(85 * weights.deptManager / 100 + 90 * weights.projectManager / 100).toFixed(1)}分
                  </p>
                </div>
              </div>

              {/* 示例2：参与多个项目 */}
              <div className="p-4 bg-slate-900/30 rounded-lg border border-slate-700/50">
                <h4 className="text-white font-medium mb-3">示例2：员工参与2个项目</h4>
                <div className="space-y-2 text-sm text-slate-300">
                  <p>• 部门经理评分：88分（权重 {weights.deptManager}%）</p>
                  <p>• 项目A经理评分：92分（项目权重 60%）</p>
                  <p>• 项目B经理评分：85分（项目权重 40%）</p>
                  <p className="text-slate-400">
                    → 项目经理综合评分 = 92 × 60% + 85 × 40% = {(92 * 0.6 + 85 * 0.4).toFixed(1)}分
                  </p>
                  <p className="pt-2 border-t border-slate-700/50 text-purple-400 font-medium">
                    最终得分 = 88 × {weights.deptManager}% + {(92 * 0.6 + 85 * 0.4).toFixed(1)} × {weights.projectManager}%
                    = {(88 * weights.deptManager / 100 + (92 * 0.6 + 85 * 0.4) * weights.projectManager / 100).toFixed(1)}分
                  </p>
                </div>
              </div>

              {/* 示例3：未参与项目 */}
              <div className="p-4 bg-slate-900/30 rounded-lg border border-slate-700/50">
                <h4 className="text-white font-medium mb-3">示例3：员工未参与项目</h4>
                <div className="space-y-2 text-sm text-slate-300">
                  <p>• 部门经理评分：82分</p>
                  <p>• 项目经理评分：无</p>
                  <p className="pt-2 border-t border-slate-700/50 text-emerald-400 font-medium">
                    最终得分 = 82分（直接使用部门经理评分）
                  </p>
                </div>
              </div>
            </div>
          </div>
        </motion.div>

        {/* 配置历史 */}
        <motion.div {...fadeIn} transition={{ delay: 0.4 }}>
          <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700/50 overflow-hidden">
            <div className="p-6 border-b border-slate-700/50">
              <div className="flex items-center gap-3">
                <History className="h-5 w-5 text-slate-400" />
                <h3 className="text-xl font-bold text-white">配置历史记录</h3>
              </div>
            </div>

            <div className="divide-y divide-slate-700/50">
              {configHistory.map((record, index) => (
                <motion.div
                  key={record.id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="p-6 hover:bg-slate-700/20 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-4 mb-2">
                        <span className="text-white font-medium">{record.date}</span>
                        <span className="text-slate-400">·</span>
                        <span className="text-slate-400">{record.operator}</span>
                      </div>
                      <div className="flex items-center gap-6 text-sm text-slate-300 mb-2">
                        <div className="flex items-center gap-2">
                          <Users className="h-4 w-4 text-blue-400" />
                          <span>部门经理 {record.deptWeight}%</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <Briefcase className="h-4 w-4 text-purple-400" />
                          <span>项目经理 {record.projectWeight}%</span>
                        </div>
                      </div>
                      <p className="text-sm text-slate-400">{record.reason}</p>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </motion.div>

        {/* 注意事项 */}
        <motion.div {...fadeIn} transition={{ delay: 0.5 }}>
          <div className="bg-amber-500/10 rounded-lg p-4 border border-amber-500/20">
            <div className="flex items-start gap-3">
              <AlertCircle className="h-5 w-5 text-amber-400 mt-0.5 flex-shrink-0" />
              <div className="text-sm text-slate-300 space-y-1">
                <p className="font-medium text-white mb-2">配置注意事项：</p>
                <p>• 权重配置会立即生效，影响所有员工的绩效计算</p>
                <p>• 建议在绩效评价周期开始前调整权重配置</p>
                <p>• 部门经理权重 + 项目经理权重必须等于100%</p>
                <p>• 权重调整应基于公司战略和管理需求，建议每季度评估一次</p>
                <p>• 所有配置变更都会记录在历史记录中，便于追溯</p>
              </div>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </div>
  )
}

export default EvaluationWeightConfig
