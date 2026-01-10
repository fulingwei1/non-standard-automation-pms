import { useState, useEffect, useMemo, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { cn } from '../lib/utils'
import { PROJECT_STAGES, HEALTH_CONFIG } from '../lib/constants'
import { useRoleFilter } from '../hooks/useRoleFilter'
import { projectApi } from '../services/api'
import { PageHeader } from '../components/layout/PageHeader'
import { BoardColumn, BoardFilters, ProjectCard } from '../components/board'
import { Card, Skeleton, ApiIntegrationError } from '../components/ui'
import {
  Layers,
  AlertCircle,
  TrendingUp,
  Clock,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react'

// 模拟用户数据（后续从 auth context 获取）
// Mock data - 已移除，使用真实API
// Mock data removed - using real API only

export default function ProjectBoard() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [projects, setProjects] = useState([])
  const [user] = useState(mockUser)
  
  // 筛选状态
  const [viewMode, setViewMode] = useState('kanban')
  const [filterMode, setFilterMode] = useState('my')
  const [statusFilter, setStatusFilter] = useState('all')
  const [healthFilter, setHealthFilter] = useState('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [collapsedStages, setCollapsedStages] = useState({})
  
  // 使用角色筛选 Hook
  const {
    relevantStages,
    isProjectRelevant,
    isStageRelevant,
    filterProjects,
    groupByStage,
    stageStats,
  } = useRoleFilter(user, projects)

  // 加载数据
  const fetchData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await projectApi.list()
      // API返回分页格式：{ items: [], total: 0, page: 1, page_size: 20, pages: 0 }
      const items = response.data?.items || response.data || []
      setProjects(Array.isArray(items) ? items : [])
    } catch (err) {
      console.error('Failed to fetch projects:', err)
      setError(err)
      setProjects([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  // 筛选后的项目
  const filteredProjects = useMemo(() => {
    let result = projects

    // 智能筛选模式
    if (filterMode === 'my') {
      result = filterProjects(result, 'my')
    }

    // 状态筛选
    if (statusFilter !== 'all') {
      result = result.filter(p => p.status === statusFilter)
    }

    // 健康度筛选
    if (healthFilter !== 'all') {
      result = result.filter(p => p.health === healthFilter)
    }

    // 搜索
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      result = result.filter(p =>
        p.project_code?.toLowerCase().includes(query) ||
        p.name?.toLowerCase().includes(query) ||
        p.customer_name?.toLowerCase().includes(query)
      )
    }

    return result
  }, [projects, filterMode, statusFilter, healthFilter, searchQuery, filterProjects])

  // 按阶段分组的项目
  const projectsByStage = useMemo(() => {
    return groupByStage(filteredProjects)
  }, [filteredProjects, groupByStage])

  // 统计信息
  const stats = useMemo(() => {
    const healthCounts = { H1: 0, H2: 0, H3: 0, H4: 0 }
    filteredProjects.forEach(p => {
      const h = p.health || 'H1'
      healthCounts[h]++
    })
    
    return {
      total: projects.length,
      filtered: filteredProjects.length,
      myCount: filterProjects(projects, 'my').length,
      ...healthCounts,
    }
  }, [projects, filteredProjects, filterProjects])

  // 处理阶段折叠
  const handleToggleCollapse = (stageKey, collapsed) => {
    setCollapsedStages(prev => ({
      ...prev,
      [stageKey]: collapsed,
    }))
  }

  // 处理项目点击
  const handleProjectClick = (project) => {
    navigate(`/projects/${project.id}`)
  }

  // 滚动看板
  const scrollBoard = (direction) => {
    const container = document.getElementById('board-container')
    if (container) {
      const scrollAmount = 320
      container.scrollBy({
        left: direction === 'left' ? -scrollAmount : scrollAmount,
        behavior: 'smooth',
      })
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="min-h-screen"
    >
      {/* 页面头部 */}
      <PageHeader
        title="项目看板"
        description="多维度可视化项目状态，快速定位关注项目"
        breadcrumb={[
          { label: '首页', href: '/' },
          { label: '项目看板' },
        ]}
      />

      {/* 筛选器 */}
      <BoardFilters
        viewMode={viewMode}
        onViewModeChange={setViewMode}
        filterMode={filterMode}
        onFilterModeChange={setFilterMode}
        statusFilter={statusFilter}
        onStatusFilterChange={setStatusFilter}
        healthFilter={healthFilter}
        onHealthFilterChange={setHealthFilter}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        onRefresh={fetchData}
        isLoading={loading}
        stats={stats}
      />

      {/* 错误状态 */}
      {error && !loading && (
        <ApiIntegrationError
          error={error}
          apiEndpoint="/api/v1/projects"
          onRetry={fetchData}
        />
      )}

      {/* 加载状态 */}
      {loading && (
        <div className="flex gap-4 overflow-hidden">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="min-w-[280px]">
              <Skeleton className="h-16 mb-2" />
              <Skeleton className="h-32 mb-2" />
              <Skeleton className="h-32 mb-2" />
              <Skeleton className="h-32" />
            </div>
          ))}
        </div>
      )}

      {/* 看板视图 */}
      {!loading && !error && viewMode === 'kanban' && (
        <div className="relative">
          {/* 左滚动按钮 */}
          <button
            onClick={() => scrollBoard('left')}
            className="absolute left-0 top-1/2 -translate-y-1/2 z-10 w-10 h-10 rounded-full bg-surface-2/90 border border-white/10 flex items-center justify-center text-white hover:bg-surface-1 transition-colors shadow-lg"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>

          {/* 看板容器 */}
          <div
            id="board-container"
            className="flex gap-4 overflow-x-auto pb-4 px-12 scroll-smooth custom-scrollbar"
            style={{ scrollbarWidth: 'thin' }}
          >
            {PROJECT_STAGES.map((stage) => (
              <BoardColumn
                key={stage.key}
                stage={stage}
                projects={projectsByStage[stage.key] || []}
                isRelevant={isStageRelevant(stage.key)}
                onProjectClick={handleProjectClick}
                isProjectRelevant={isProjectRelevant}
                collapsed={collapsedStages[stage.key]}
                onToggleCollapse={handleToggleCollapse}
              />
            ))}
          </div>

          {/* 右滚动按钮 */}
          <button
            onClick={() => scrollBoard('right')}
            className="absolute right-0 top-1/2 -translate-y-1/2 z-10 w-10 h-10 rounded-full bg-surface-2/90 border border-white/10 flex items-center justify-center text-white hover:bg-surface-1 transition-colors shadow-lg"
          >
            <ChevronRight className="w-5 h-5" />
          </button>
        </div>
      )}

      {/* 矩阵视图 */}
      {!loading && !error && viewMode === 'matrix' && (
        <MatrixView
          projects={filteredProjects}
          stages={PROJECT_STAGES}
          onProjectClick={handleProjectClick}
        />
      )}

      {/* 列表视图 */}
      {!loading && !error && viewMode === 'list' && (
        <ListView
          projects={filteredProjects}
          onProjectClick={handleProjectClick}
          isProjectRelevant={isProjectRelevant}
        />
      )}

      {/* 空状态 */}
      {!loading && filteredProjects.length === 0 && (
        <div className="flex flex-col items-center justify-center py-20">
          <Layers className="w-16 h-16 text-slate-600 mb-4" />
          <h3 className="text-lg font-medium text-white mb-2">暂无项目</h3>
          <p className="text-slate-400">
            {searchQuery ? '没有找到匹配的项目' : '当前筛选条件下没有项目'}
          </p>
        </div>
      )}
    </motion.div>
  )
}

// 矩阵视图组件
function MatrixView({ projects, stages, onProjectClick }) {
  // 按阶段和健康度分组
  const matrix = useMemo(() => {
    const result = {}
    stages.forEach(stage => {
      result[stage.key] = { H1: [], H2: [], H3: [], H4: [] }
    })
    
    projects.forEach(project => {
      // API返回的是 stage 字段，不是 current_stage
      const stageKey = project.stage || project.current_stage || 'S1'
      const healthKey = project.health || 'H1'
      if (result[stageKey]) {
        result[stageKey][healthKey].push(project)
      }
    })
    
    return result
  }, [projects, stages])

  const healthKeys = ['H3', 'H2', 'H1', 'H4'] // 预警优先

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse">
        <thead>
          <tr>
            <th className="p-2 text-left text-xs text-slate-500 font-normal">健康度 / 阶段</th>
            {stages.map(stage => (
              <th key={stage.key} className="p-2 text-center">
                <div className="text-xs text-slate-400">{stage.key}</div>
                <div className="text-sm text-white">{stage.shortName}</div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {healthKeys.map(healthKey => (
            <tr key={healthKey} className="border-t border-white/5">
              <td className="p-2">
                <div className={cn(
                  'flex items-center gap-2 px-2 py-1 rounded',
                  HEALTH_CONFIG[healthKey].bgClass
                )}>
                  <span className={cn('w-2 h-2 rounded-full', HEALTH_CONFIG[healthKey].dotClass)} />
                  <span className={cn('text-sm', HEALTH_CONFIG[healthKey].textClass)}>
                    {HEALTH_CONFIG[healthKey].label}
                  </span>
                </div>
              </td>
              {stages.map(stage => {
                const cellProjects = matrix[stage.key]?.[healthKey] || []
                return (
                  <td key={stage.key} className="p-2 text-center align-top">
                    {cellProjects.length > 0 ? (
                      <div className="space-y-1">
                        {cellProjects.slice(0, 3).map(project => (
                          <motion.div
                            key={project.id}
                            whileHover={{ scale: 1.05 }}
                            onClick={() => onProjectClick(project)}
                            className={cn(
                              'cursor-pointer px-2 py-1 rounded text-xs truncate',
                              'bg-surface-1 hover:bg-surface-2 border border-white/5',
                              HEALTH_CONFIG[healthKey].borderClass,
                              'border-l-2'
                            )}
                          >
                            {project.project_code}
                          </motion.div>
                        ))}
                        {cellProjects.length > 3 && (
                          <div className="text-xs text-slate-500">
                            +{cellProjects.length - 3} 更多
                          </div>
                        )}
                      </div>
                    ) : (
                      <span className="text-slate-600">-</span>
                    )}
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// 列表视图组件
function ListView({ projects, onProjectClick, isProjectRelevant }) {
  return (
    <div className="space-y-2">
      {projects.map((project, index) => (
        <motion.div
          key={project.id}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.02 }}
        >
          <Card
            className={cn(
              'hover:bg-surface-2/50 cursor-pointer transition-colors',
              isProjectRelevant(project.id) && 'ring-1 ring-primary/30'
            )}
            onClick={() => onProjectClick(project)}
          >
            <div className="p-4 flex items-center gap-4">
              {/* 健康度指示 */}
              <div className={cn(
                'w-1 h-12 rounded-full',
                HEALTH_CONFIG[project.health || 'H1'].dotClass
              )} />
              
              {/* 项目信息 */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs font-mono text-slate-400">
                    {project.project_code}
                  </span>
                  <span className={cn(
                    'text-xs px-2 py-0.5 rounded',
                    HEALTH_CONFIG[project.health || 'H1'].bgClass,
                    HEALTH_CONFIG[project.health || 'H1'].textClass
                  )}>
                    {HEALTH_CONFIG[project.health || 'H1'].label}
                  </span>
                </div>
                <h4 className="text-white font-medium truncate">{project.name}</h4>
              </div>
              
              {/* 阶段 */}
              <div className="text-center px-4">
                <div className="text-xs text-slate-500">阶段</div>
                <div className="text-sm text-white">
                  {PROJECT_STAGES.find(s => (s.key || s.code) === (project.stage || project.current_stage))?.shortName || '-'}
                </div>
              </div>
              
              {/* 客户 */}
              <div className="text-center px-4 min-w-[100px]">
                <div className="text-xs text-slate-500">客户</div>
                <div className="text-sm text-white truncate">{project.customer_name || '-'}</div>
              </div>
              
              {/* 负责人 */}
              <div className="text-center px-4">
                <div className="text-xs text-slate-500">负责人</div>
                <div className="text-sm text-white">{project.pm_name || '-'}</div>
              </div>
              
              {/* 进度 */}
              <div className="text-center px-4 min-w-[80px]">
                <div className="text-xs text-slate-500">进度</div>
                <div className="text-sm text-white">{project.progress || 0}%</div>
              </div>
              
              {/* 截止日期 */}
              <div className="text-center px-4">
                <div className="text-xs text-slate-500">截止</div>
                <div className="text-sm text-white">{project.planned_end_date || '-'}</div>
              </div>
            </div>
          </Card>
        </motion.div>
      ))}
    </div>
  )
}

