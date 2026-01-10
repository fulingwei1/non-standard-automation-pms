/**
 * Sales Project Track Page - Project progress tracking from sales perspective
 * Features: Project overview, milestone tracking, acceptance coordination
 */

import { useState, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  FolderKanban,
  Search,
  Filter,
  Calendar,
  DollarSign,
  Building2,
  User,
  Clock,
  CheckCircle2,
  AlertTriangle,
  ChevronRight,
  X,
  FileText,
  Milestone,
  Eye,
  Flag,
  Target,
  Truck,
  ClipboardCheck,
  Shield,
  Phone,
  MessageSquare,
} from 'lucide-react'
import { PageHeader } from '../components/layout'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Input,
  Progress,
} from '../components/ui'
import { cn } from '../lib/utils'
import { fadeIn, staggerContainer } from '../lib/animations'

// Stage configuration
const stageConfig = {
  solution: { label: '方案设计', color: 'bg-violet-500', textColor: 'text-violet-400', order: 1 },
  design: { label: '结构设计', color: 'bg-blue-500', textColor: 'text-blue-400', order: 2 },
  procurement: { label: '采购备料', color: 'bg-cyan-500', textColor: 'text-cyan-400', order: 3 },
  assembly: { label: '装配调试', color: 'bg-amber-500', textColor: 'text-amber-400', order: 4 },
  fat: { label: '出厂验收', color: 'bg-emerald-500', textColor: 'text-emerald-400', order: 5 },
  shipping: { label: '包装发运', color: 'bg-purple-500', textColor: 'text-purple-400', order: 6 },
  sat: { label: '现场调试', color: 'bg-pink-500', textColor: 'text-pink-400', order: 7 },
  warranty: { label: '质保结项', color: 'bg-slate-500', textColor: 'text-slate-400', order: 8 },
}

const healthConfig = {
  good: { label: '正常', color: 'bg-emerald-500', textColor: 'text-emerald-400' },
  warning: { label: '有风险', color: 'bg-amber-500', textColor: 'text-amber-400' },
  critical: { label: '阻塞', color: 'bg-red-500', textColor: 'text-red-400' },
}

// Mock project data for sales view
// Mock data - 已移除，使用真实API
export default function SalesProjectTrack() {
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedStage, setSelectedStage] = useState('all')
  const [selectedHealth, setSelectedHealth] = useState('all')
  const [selectedProject, setSelectedProject] = useState(null)

  // Filter projects
  const filteredProjects = useMemo(() => {
    return mockProjects.filter(project => {
      const matchesSearch = !searchTerm || 
        project.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        project.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
        project.customerShort.toLowerCase().includes(searchTerm.toLowerCase())
      
      const matchesStage = selectedStage === 'all' || project.stage === selectedStage
      const matchesHealth = selectedHealth === 'all' || project.health === selectedHealth

      return matchesSearch && matchesStage && matchesHealth
    })
  }, [searchTerm, selectedStage, selectedHealth])

  // Stats
  const stats = useMemo(() => {
    return {
      total: mockProjects.length,
      inProgress: mockProjects.filter(p => !['warranty'].includes(p.stage)).length,
      nearDelivery: mockProjects.filter(p => {
        const delivery = new Date(p.expectedDelivery)
        const now = new Date()
        const diff = (delivery - now) / (1000 * 60 * 60 * 24)
        return diff <= 14 && diff > 0
      }).length,
      hasIssue: mockProjects.filter(p => p.health !== 'good').length,
    }
  }, [])

  const handleProjectClick = (project) => {
    setSelectedProject(project)
  }

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {/* Page Header */}
      <PageHeader
        title="项目跟踪"
        description="跟踪我负责的项目进度和关键节点"
      />

      {/* Stats Row */}
      <motion.div variants={fadeIn} className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <Card className="bg-surface-100/50">
          <CardContent className="p-4 flex items-center gap-4">
            <div className="p-2 bg-blue-500/20 rounded-lg">
              <FolderKanban className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <p className="text-2xl font-bold text-white">{stats.total}</p>
              <p className="text-xs text-slate-400">我的项目</p>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-surface-100/50">
          <CardContent className="p-4 flex items-center gap-4">
            <div className="p-2 bg-emerald-500/20 rounded-lg">
              <Target className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <p className="text-2xl font-bold text-white">{stats.inProgress}</p>
              <p className="text-xs text-slate-400">进行中</p>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-surface-100/50">
          <CardContent className="p-4 flex items-center gap-4">
            <div className="p-2 bg-amber-500/20 rounded-lg">
              <Truck className="w-5 h-5 text-amber-400" />
            </div>
            <div>
              <p className="text-2xl font-bold text-white">{stats.nearDelivery}</p>
              <p className="text-xs text-slate-400">近期交付</p>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-surface-100/50">
          <CardContent className="p-4 flex items-center gap-4">
            <div className="p-2 bg-red-500/20 rounded-lg">
              <AlertTriangle className="w-5 h-5 text-red-400" />
            </div>
            <div>
              <p className="text-2xl font-bold text-white">{stats.hasIssue}</p>
              <p className="text-xs text-slate-400">需关注</p>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Filters */}
      <motion.div variants={fadeIn} className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div className="flex flex-wrap gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <Input
              placeholder="搜索项目..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 w-56"
            />
          </div>
          <select
            value={selectedStage}
            onChange={(e) => setSelectedStage(e.target.value)}
            className="px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <option value="all">全部阶段</option>
            {Object.entries(stageConfig).map(([key, val]) => (
              <option key={key} value={key}>{val.label}</option>
            ))}
          </select>
          <select
            value={selectedHealth}
            onChange={(e) => setSelectedHealth(e.target.value)}
            className="px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <option value="all">全部状态</option>
            {Object.entries(healthConfig).map(([key, val]) => (
              <option key={key} value={key}>{val.label}</option>
            ))}
          </select>
        </div>

        <span className="text-sm text-slate-400">
          共 {filteredProjects.length} 个项目
        </span>
      </motion.div>

      {/* Project List */}
      <motion.div variants={fadeIn} className="space-y-4">
        {filteredProjects.map((project) => {
          const stageConf = stageConfig[project.stage]
          const healthConf = healthConfig[project.health]
          const paymentProgress = project.contractAmount > 0 
            ? (project.paidAmount / project.contractAmount * 100) 
            : 0

          return (
            <Card
              key={project.id}
              onClick={() => handleProjectClick(project)}
              className="cursor-pointer hover:border-primary/30 transition-colors"
            >
              <CardContent className="p-4">
                <div className="flex flex-col lg:flex-row lg:items-center gap-4">
                  {/* Project Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-2">
                      <div className={cn('w-3 h-3 rounded-full', healthConf.color)} />
                      <h3 className="font-semibold text-white truncate">{project.name}</h3>
                      <Badge variant="secondary" className={cn('text-xs', stageConf.textColor)}>
                        {stageConf.label}
                      </Badge>
                      {project.issues.length > 0 && (
                        <AlertTriangle className="w-4 h-4 text-amber-500" />
                      )}
                    </div>
                    <div className="flex flex-wrap items-center gap-4 text-sm text-slate-400">
                      <span className="flex items-center gap-1">
                        <Building2 className="w-4 h-4" />
                        {project.customerShort}
                      </span>
                      <span className="flex items-center gap-1">
                        <FileText className="w-4 h-4" />
                        {project.contractNo}
                      </span>
                      <span className="flex items-center gap-1">
                        <User className="w-4 h-4" />
                        PM: {project.pm}
                      </span>
                    </div>
                  </div>

                  {/* Progress */}
                  <div className="w-full lg:w-48">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs text-slate-400">项目进度</span>
                      <span className="text-xs text-white">{project.progress}%</span>
                    </div>
                    <Progress value={project.progress} className="h-2" />
                  </div>

                  {/* Dates */}
                  <div className="flex flex-col gap-1 text-sm">
                    <div className="flex items-center gap-2">
                      <Truck className="w-4 h-4 text-slate-500" />
                      <span className="text-slate-400">交付:</span>
                      <span className="text-white">{project.expectedDelivery}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <ClipboardCheck className="w-4 h-4 text-slate-500" />
                      <span className="text-slate-400">验收:</span>
                      <span className="text-white">{project.acceptanceDate}</span>
                    </div>
                  </div>

                  {/* Amount */}
                  <div className="text-right">
                    <div className="text-lg font-semibold text-amber-400">
                      ¥{(project.contractAmount / 10000).toFixed(0)}万
                    </div>
                    <div className="text-xs text-slate-400">
                      已收 {paymentProgress.toFixed(0)}%
                    </div>
                  </div>

                  <ChevronRight className="w-5 h-5 text-slate-500" />
                </div>

                {/* Milestone Progress */}
                <div className="mt-4 pt-4 border-t border-white/5">
                  <div className="flex items-center gap-1">
                    {project.milestones.map((milestone, index) => {
                      const isCompleted = milestone.status === 'completed'
                      const isCurrent = milestone.status === 'in_progress'
                      
                      return (
                        <div key={index} className="flex items-center">
                          <div
                            className={cn(
                              'w-6 h-6 rounded-full flex items-center justify-center text-xs',
                              isCompleted ? 'bg-emerald-500 text-white' :
                              isCurrent ? 'bg-primary text-white' :
                              'bg-surface-50 text-slate-500 border border-slate-600'
                            )}
                            title={`${milestone.name}: ${milestone.date}`}
                          >
                            {isCompleted ? '✓' : index + 1}
                          </div>
                          {index < project.milestones.length - 1 && (
                            <div className={cn(
                              'w-8 h-0.5',
                              isCompleted ? 'bg-emerald-500' : 'bg-slate-600'
                            )} />
                          )}
                        </div>
                      )
                    })}
                  </div>
                  <div className="flex justify-between mt-2 text-xs text-slate-500">
                    <span>{project.milestones[0]?.name}</span>
                    <span>{project.milestones[project.milestones.length - 1]?.name}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          )
        })}

        {filteredProjects.length === 0 && (
          <div className="text-center py-16">
            <FolderKanban className="w-12 h-12 mx-auto text-slate-600 mb-4" />
            <h3 className="text-lg font-medium text-white mb-2">暂无项目</h3>
            <p className="text-slate-400">没有找到符合条件的项目</p>
          </div>
        )}
      </motion.div>

      {/* Project Detail Panel */}
      <AnimatePresence>
        {selectedProject && (
          <ProjectDetailPanel
            project={selectedProject}
            onClose={() => setSelectedProject(null)}
          />
        )}
      </AnimatePresence>
    </motion.div>
  )
}

// Project Detail Panel
function ProjectDetailPanel({ project, onClose }) {
  const stageConf = stageConfig[project.stage]
  const healthConf = healthConfig[project.health]
  const paymentProgress = project.contractAmount > 0 
    ? (project.paidAmount / project.contractAmount * 100) 
    : 0

  return (
    <motion.div
      initial={{ x: '100%' }}
      animate={{ x: 0 }}
      exit={{ x: '100%' }}
      transition={{ type: 'spring', damping: 25, stiffness: 200 }}
      className="fixed right-0 top-0 h-full w-full md:w-[500px] bg-surface-100/95 backdrop-blur-xl border-l border-white/5 shadow-2xl z-50 flex flex-col"
    >
      {/* Header */}
      <div className="p-4 border-b border-white/5">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <div className={cn('w-3 h-3 rounded-full', healthConf.color)} />
              <h2 className="text-lg font-semibold text-white">{project.name}</h2>
            </div>
            <p className="text-sm text-slate-400">{project.id} · {project.contractNo}</p>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="w-5 h-5" />
          </Button>
        </div>
        <div className="flex items-center gap-2 mt-3">
          <Badge variant="secondary" className={cn('text-xs', stageConf.textColor)}>
            {stageConf.label}
          </Badge>
          <Badge variant="secondary" className={cn('text-xs', healthConf.textColor)}>
            {healthConf.label}
          </Badge>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {/* Progress & Amount */}
        <div className="grid grid-cols-2 gap-4">
          <div className="p-4 bg-surface-50 rounded-xl">
            <div className="text-sm text-slate-400 mb-2">项目进度</div>
            <div className="text-2xl font-bold text-white mb-2">{project.progress}%</div>
            <Progress value={project.progress} className="h-2" />
          </div>
          <div className="p-4 bg-gradient-to-br from-amber-500/10 to-orange-500/5 border border-amber-500/20 rounded-xl">
            <div className="text-sm text-slate-400 mb-2">合同金额</div>
            <div className="text-2xl font-bold text-amber-400">
              ¥{(project.contractAmount / 10000).toFixed(0)}万
            </div>
            <div className="text-xs text-slate-400 mt-1">
              已收 {paymentProgress.toFixed(0)}% (¥{(project.paidAmount / 10000).toFixed(0)}万)
            </div>
          </div>
        </div>

        {/* Basic Info */}
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-slate-400">项目信息</h3>
          <div className="space-y-2 text-sm">
            <div className="flex items-center gap-3">
              <Building2 className="w-4 h-4 text-slate-500" />
              <span className="text-slate-400">客户:</span>
              <span className="text-white">{project.customerShort}</span>
            </div>
            <div className="flex items-center gap-3">
              <User className="w-4 h-4 text-slate-500" />
              <span className="text-slate-400">项目经理:</span>
              <span className="text-white">{project.pm}</span>
            </div>
            <div className="flex items-center gap-3">
              <Calendar className="w-4 h-4 text-slate-500" />
              <span className="text-slate-400">启动日期:</span>
              <span className="text-white">{project.startDate}</span>
            </div>
            <div className="flex items-center gap-3">
              <Truck className="w-4 h-4 text-slate-500" />
              <span className="text-slate-400">预计交付:</span>
              <span className="text-white">{project.expectedDelivery}</span>
            </div>
            <div className="flex items-center gap-3">
              <ClipboardCheck className="w-4 h-4 text-slate-500" />
              <span className="text-slate-400">验收日期:</span>
              <span className="text-white">{project.acceptanceDate}</span>
            </div>
            <div className="flex items-center gap-3">
              <Clock className="w-4 h-4 text-slate-500" />
              <span className="text-slate-400">最近更新:</span>
              <span className="text-white">{project.lastUpdate}</span>
            </div>
          </div>
        </div>

        {/* Milestones */}
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-slate-400">里程碑</h3>
          <div className="space-y-2">
            {project.milestones.map((milestone, index) => {
              const isCompleted = milestone.status === 'completed'
              const isCurrent = milestone.status === 'in_progress'
              const isDelayed = milestone.actual && milestone.actual > milestone.date

              return (
                <div 
                  key={index}
                  className={cn(
                    'p-3 rounded-lg border',
                    isCompleted ? 'bg-emerald-500/10 border-emerald-500/20' :
                    isCurrent ? 'bg-primary/10 border-primary/20' :
                    'bg-surface-50 border-white/5'
                  )}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {isCompleted ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                      ) : isCurrent ? (
                        <Flag className="w-4 h-4 text-primary" />
                      ) : (
                        <Clock className="w-4 h-4 text-slate-400" />
                      )}
                      <span className="text-sm text-white">{milestone.name}</span>
                      {isDelayed && (
                        <Badge variant="destructive" className="text-xs">延期</Badge>
                      )}
                    </div>
                    <span className="text-xs text-slate-400">
                      {isCompleted ? milestone.actual : milestone.date}
                    </span>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Issues */}
        {project.issues.length > 0 && (
          <div className="space-y-3">
            <h3 className="text-sm font-medium text-slate-400">问题与风险</h3>
            {project.issues.map((issue, index) => (
              <div 
                key={index}
                className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg"
              >
                <div className="flex items-center gap-2 text-amber-400 text-sm">
                  <AlertTriangle className="w-4 h-4" />
                  {issue.content}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Quick Actions */}
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-slate-400">快捷操作</h3>
          <div className="grid grid-cols-2 gap-2">
            <Button variant="outline" size="sm" className="justify-start">
              <Phone className="w-4 h-4 mr-2 text-blue-400" />
              联系客户
            </Button>
            <Button variant="outline" size="sm" className="justify-start">
              <MessageSquare className="w-4 h-4 mr-2 text-green-400" />
              联系PM
            </Button>
            <Button variant="outline" size="sm" className="justify-start">
              <DollarSign className="w-4 h-4 mr-2 text-amber-400" />
              查看回款
            </Button>
            <Button variant="outline" size="sm" className="justify-start">
              <FileText className="w-4 h-4 mr-2 text-purple-400" />
              查看合同
            </Button>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-white/5 flex gap-2">
        <Button variant="outline" className="flex-1" onClick={onClose}>
          关闭
        </Button>
        <Button className="flex-1">
          <Eye className="w-4 h-4 mr-2" />
          查看详情
        </Button>
      </div>
    </motion.div>
  )
}

