import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { cn } from '../lib/utils'
import {
  projectApi,
  machineApi,
  stageApi,
  milestoneApi,
  memberApi,
  costApi,
  documentApi,
} from '../services/api'
import { formatDate, formatCurrency, getStageName } from '../lib/utils'
import { PageHeader } from '../components/layout/PageHeader'
import {
  Card,
  CardContent,
  Button,
  Badge,
  HealthBadge,
  Progress,
  CircularProgress,
  Skeleton,
  UserAvatar,
  AvatarGroup,
} from '../components/ui'
import ProjectLeadsPanel from '../components/project/ProjectLeadsPanel'
import GateCheckPanel from '../components/project/GateCheckPanel'
import ProjectTimeline from '../components/project/ProjectTimeline'
import QuickActionPanel from '../components/project/QuickActionPanel'
import {
  ArrowLeft,
  Edit2,
  MoreHorizontal,
  Briefcase,
  Box,
  CheckCircle2,
  Circle,
  Users,
  UserCog,
  DollarSign,
  FileText,
  Calendar,
  Clock,
  Plus,
  Activity,
  Target,
  TrendingUp,
  AlertTriangle,
} from 'lucide-react'

// Tab data
const tabs = [
  { id: 'overview', name: '概览', icon: Activity },
  { id: 'stages', name: '进度计划', icon: Clock },
  { id: 'machines', name: '设备列表', icon: Box },
  { id: 'team', name: '项目团队', icon: Users },
  { id: 'leads', name: '负责人', icon: UserCog },
  { id: 'finance', name: '财务/成本', icon: DollarSign },
  { id: 'docs', name: '文档中心', icon: FileText },
  { id: 'timeline', name: '时间线', icon: Calendar }, // Sprint 3.3: 新增时间线标签
]

// Animation variants
const fadeIn = {
  initial: { opacity: 0, y: 10 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -10 },
}

export default function ProjectDetail() {
  const { id } = useParams()
  const navigate = useNavigate()

  const [loading, setLoading] = useState(true)
  const [project, setProject] = useState(null)
  const [stages, setStages] = useState([])
  const [machines, setMachines] = useState([])
  const [members, setMembers] = useState([])
  const [milestones, setMilestones] = useState([])
  const [costs, setCosts] = useState([])
  const [documents, setDocuments] = useState([])
  const [statusLogs, setStatusLogs] = useState([]) // Sprint 3.3: 状态变更日志
  const [activeTab, setActiveTab] = useState('overview')

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true)
        const [
          projRes,
          stagesRes,
          machinesRes,
          membersRes,
          milestonesRes,
          costsRes,
          docsRes,
          logsRes,
        ] = await Promise.all([
          projectApi.get(id),
          stageApi.list(id),
          machineApi.list({ project_id: id }),
          memberApi.list(id),
          milestoneApi.list(id),
          costApi.list(id),
          documentApi.list(id),
          projectApi.getStatusLogs(id, { limit: 50 }), // Sprint 3.3: 加载状态日志
        ])

        setProject(projRes.data)
        setStages(stagesRes.data || [])
        setMachines(machinesRes.data || [])
        setMembers(membersRes.data || [])
        setMilestones(milestonesRes.data || [])
        setCosts(costsRes.data || [])
        setDocuments(docsRes.data || [])
        setStatusLogs(logsRes.data?.items || logsRes.data || []) // Sprint 3.3
      } catch (err) {
        console.error('Failed to fetch project details:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [id])

  if (loading) {
    return (
      <div className="animate-pulse space-y-6">
        <div className="flex items-center gap-4">
          <Skeleton className="h-12 w-12 rounded-xl" />
          <div className="space-y-2">
            <Skeleton className="h-6 w-48" />
            <Skeleton className="h-4 w-32" />
          </div>
        </div>
        <div className="grid grid-cols-4 gap-4">
          {Array(4)
            .fill(null)
            .map((_, i) => (
              <Skeleton key={i} className="h-24 rounded-2xl" />
            ))}
        </div>
        <Skeleton className="h-96 rounded-2xl" />
      </div>
    )
  }

  if (!project) {
    return (
      <div className="text-center py-20">
        <h2 className="text-xl font-semibold text-white mb-2">未找到项目</h2>
        <p className="text-slate-400 mb-6">该项目可能已被删除或不存在</p>
        <Button onClick={() => navigate('/projects')}>返回项目列表</Button>
      </div>
    )
  }

  // Stats cards data
  const statCards = [
    {
      label: '整体进度',
      value: `${project.progress_pct || 0}%`,
      icon: TrendingUp,
      color: 'primary',
    },
    {
      label: '当前阶段',
      value: project.stage || 'S1',
      subtext: getStageName(project.stage),
      icon: Target,
      color: 'emerald',
    },
    {
      label: '机台总数',
      value: machines.length,
      subtext: `已完成 ${machines.filter((m) => m.progress_pct === 100).length} 个`,
      icon: Box,
      color: 'indigo',
    },
    {
      label: '交付日期',
      value: project.planned_end_date
        ? formatDate(project.planned_end_date)
        : '未设置',
      icon: Calendar,
      color: 'amber',
    },
  ]

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      {/* Header */}
      <div className="flex items-start gap-4 mb-8">
        <button
          onClick={() => navigate('/projects')}
          className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-white/5 transition-colors"
        >
          <ArrowLeft className="h-5 w-5" />
        </button>

        <div className="flex-1">
          <div className="flex items-center gap-3 mb-1">
            <h1 className="text-2xl font-bold text-white">
              {project.project_name}
            </h1>
            <HealthBadge health={project.health || 'H1'} />
          </div>
          <div className="flex items-center gap-4 text-sm text-slate-400">
            <span>{project.project_code}</span>
            <span>•</span>
            <span>客户: {project.customer_name}</span>
            <span>•</span>
            <span>负责人: {project.pm_name || '未指定'}</span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Sprint 3.3: 快速操作面板 */}
          <QuickActionPanel
            project={project}
            onRefresh={() => {
              // 重新加载数据
              projectApi.get(id).then((res) => setProject(res.data))
            }}
          />
          <Button variant="secondary" size="icon">
            <Edit2 className="h-4 w-4" />
          </Button>
          <Button variant="secondary" size="icon">
            <MoreHorizontal className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {statCards.map((stat, i) => (
          <Card key={i} className="p-4">
            <div className="flex items-center justify-between mb-3">
              <div
                className={cn(
                  'p-2 rounded-lg',
                  stat.color === 'primary' && 'bg-primary/20',
                  stat.color === 'emerald' && 'bg-emerald-500/20',
                  stat.color === 'indigo' && 'bg-indigo-500/20',
                  stat.color === 'amber' && 'bg-amber-500/20'
                )}
              >
                <stat.icon
                  className={cn(
                    'h-4 w-4',
                    stat.color === 'primary' && 'text-primary',
                    stat.color === 'emerald' && 'text-emerald-400',
                    stat.color === 'indigo' && 'text-indigo-400',
                    stat.color === 'amber' && 'text-amber-400'
                  )}
                />
              </div>
            </div>
            <p className="text-xs text-slate-400 mb-1">{stat.label}</p>
            <p className="text-xl font-semibold text-white">{stat.value}</p>
            {stat.subtext && (
              <p className="text-xs text-slate-500 mt-1">{stat.subtext}</p>
            )}
          </Card>
        ))}
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 p-1 rounded-xl bg-white/[0.03] border border-white/5 mb-6">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={cn(
              'flex items-center justify-center gap-2 flex-1 px-4 py-2.5 rounded-lg',
              'text-sm font-medium transition-all duration-200',
              activeTab === tab.id
                ? 'bg-primary text-white shadow-lg shadow-primary/30'
                : 'text-slate-400 hover:text-white hover:bg-white/[0.05]'
            )}
          >
            <tab.icon className="h-4 w-4" />
            <span className="hidden sm:inline">{tab.name}</span>
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <AnimatePresence mode="wait">
        <motion.div key={activeTab} {...fadeIn} transition={{ duration: 0.2 }}>
          {/* Overview Tab */}
          {activeTab === 'overview' && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2 space-y-6">
                {/* Progress Overview */}
                <Card>
                  <CardContent>
                    <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                      <Activity className="h-5 w-5 text-primary" />
                      进度概览
                    </h3>
                    <div className="flex items-center gap-8">
                      <CircularProgress value={project.progress_pct || 0} size={100} />
                      <div className="flex-1">
                        <div className="grid grid-cols-2 gap-4">
                          <div className="p-3 rounded-xl bg-white/[0.03]">
                            <p className="text-xs text-slate-400 mb-1">已完成阶段</p>
                            <p className="text-lg font-semibold text-white">
                              {stages.filter((s) => s.status === 'COMPLETED').length} / {stages.length}
                            </p>
                          </div>
                          <div className="p-3 rounded-xl bg-white/[0.03]">
                            <p className="text-xs text-slate-400 mb-1">已完成机台</p>
                            <p className="text-lg font-semibold text-white">
                              {machines.filter((m) => m.progress_pct === 100).length} / {machines.length}
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Milestones */}
                <Card>
                  <CardContent>
                    <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                      <Target className="h-5 w-5 text-primary" />
                      关键里程碑
                    </h3>
                    {milestones.length > 0 ? (
                      <div className="space-y-3">
                        {milestones.map((m) => (
                          <div
                            key={m.id}
                            className="flex items-center gap-4 p-3 rounded-xl bg-white/[0.02] hover:bg-white/[0.04] transition-colors"
                          >
                            <div
                              className={cn(
                                'p-2 rounded-lg',
                                m.is_completed ? 'bg-emerald-500/20' : 'bg-slate-500/20'
                              )}
                            >
                              {m.is_completed ? (
                                <CheckCircle2 className="h-5 w-5 text-emerald-400" />
                              ) : (
                                <Circle className="h-5 w-5 text-slate-400" />
                              )}
                            </div>
                            <div className="flex-1">
                              <p className="font-medium text-white">{m.milestone_name}</p>
                              <p className="text-xs text-slate-500">
                                计划: {m.planned_date}
                              </p>
                            </div>
                            <Badge variant="secondary">{m.milestone_type}</Badge>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-center py-8 text-slate-500">暂无里程碑</div>
                    )}
                  </CardContent>
                </Card>
              </div>

              {/* Sidebar */}
              <div className="space-y-6">
                {/* Sprint 3.3: 阶段门校验面板 */}
                <GateCheckPanel
                  projectId={parseInt(id)}
                  currentStage={project.stage}
                  onAdvance={() => {
                    // 重新加载项目数据
                    projectApi.get(id).then((res) => setProject(res.data))
                  }}
                />

                {/* Project Info */}
                <Card>
                  <CardContent>
                    <h3 className="text-sm font-medium text-slate-400 mb-4">项目信息</h3>
                    <div className="space-y-4">
                      <div className="flex justify-between">
                        <span className="text-sm text-slate-500">项目经理</span>
                        <span className="text-sm text-white">{project.pm_name || '未指定'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-slate-500">合同编号</span>
                        <span className="text-sm text-white">{project.contract_no || '无'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-slate-500">预算金额</span>
                        <span className="text-sm text-primary font-medium">
                          {project.budget_amount ? formatCurrency(project.budget_amount) : '未设置'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-slate-500">创建日期</span>
                        <span className="text-sm text-white">
                          {project.created_at ? formatDate(project.created_at) : '-'}
                        </span>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Team */}
                <Card>
                  <CardContent>
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-sm font-medium text-slate-400">项目团队</h3>
                      <span className="text-xs text-slate-500">{members.length} 人</span>
                    </div>
                    {members.length > 0 ? (
                      <AvatarGroup users={members.map((m) => ({ ...m, name: m.name || m.member_name }))} max={5} />
                    ) : (
                      <p className="text-sm text-slate-500">暂无成员</p>
                    )}
                  </CardContent>
                </Card>
              </div>
            </div>
          )}

          {/* Stages Tab */}
          {activeTab === 'stages' && (
            <Card>
              <CardContent>
                <div className="relative">
                  {/* Timeline line */}
                  <div className="absolute left-[19px] top-0 bottom-0 w-0.5 bg-white/10" />

                  <div className="space-y-4">
                    {stages.map((stage, idx) => (
                      <div key={stage.id} className="relative flex gap-4">
                        {/* Dot */}
                        <div
                          className={cn(
                            'relative z-10 w-10 h-10 rounded-full flex items-center justify-center',
                            stage.status === 'COMPLETED'
                              ? 'bg-primary'
                              : stage.status === 'IN_PROGRESS'
                              ? 'bg-primary/30 border-2 border-primary'
                              : 'bg-white/5 border border-white/10'
                          )}
                        >
                          {stage.status === 'COMPLETED' ? (
                            <CheckCircle2 className="h-5 w-5 text-white" />
                          ) : (
                            <span className="text-sm font-medium">{stage.stage_code}</span>
                          )}
                        </div>

                        {/* Content */}
                        <div
                          className={cn(
                            'flex-1 p-4 rounded-xl',
                            'bg-white/[0.03] border border-white/5',
                            stage.status === 'IN_PROGRESS' && 'border-primary/30'
                          )}
                        >
                          <div className="flex items-center justify-between mb-2">
                            <h4 className="font-semibold text-white">{stage.stage_name}</h4>
                            <span className="text-xs text-slate-500">
                              {stage.planned_start_date && formatDate(stage.planned_start_date)} ~{' '}
                              {stage.planned_end_date && formatDate(stage.planned_end_date)}
                            </span>
                          </div>
                          {stage.description && (
                            <p className="text-sm text-slate-400 mb-3">{stage.description}</p>
                          )}
                          <div className="flex items-center gap-4">
                            <div className="flex-1">
                              <Progress value={stage.progress_pct || 0} size="sm" />
                            </div>
                            <span className="text-sm font-medium text-white">{stage.progress_pct || 0}%</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Machines Tab */}
          {activeTab === 'machines' && (
            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white">
                  设备列表 ({machines.length})
                </h3>
                <Button size="sm">
                  <Plus className="h-4 w-4" />
                  添加设备
                </Button>
              </div>

              {machines.length > 0 ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  {machines.map((machine) => (
                    <Card key={machine.id} className="overflow-hidden">
                      <CardContent className="p-4">
                        <div className="flex items-start justify-between mb-3">
                          <div className="p-2 rounded-lg bg-indigo-500/20">
                            <Box className="h-5 w-5 text-indigo-400" />
                          </div>
                          <Badge variant="secondary">{machine.stage}</Badge>
                        </div>
                        <h4 className="font-semibold text-white mb-1">{machine.machine_name}</h4>
                        <p className="text-xs text-slate-500 mb-3">{machine.machine_code}</p>
                        <div className="flex items-center justify-between text-sm mb-2">
                          <span className="text-slate-400">进度</span>
                          <span className="text-white">{machine.progress_pct || 0}%</span>
                        </div>
                        <Progress value={machine.progress_pct || 0} size="sm" color="primary" />
                      </CardContent>
                    </Card>
                  ))}
                </div>
              ) : (
                <Card className="p-12 text-center">
                  <Box className="h-12 w-12 text-slate-600 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-white mb-2">暂无设备</h3>
                  <p className="text-slate-400 mb-6">点击上方按钮添加设备</p>
                  <Button>
                    <Plus className="h-4 w-4" />
                    添加设备
                  </Button>
                </Card>
              )}
            </div>
          )}

          {/* Team Tab */}
          {activeTab === 'team' && (
            <Card>
              <CardContent>
                {members.length > 0 ? (
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    {members.map((member) => (
                      <div
                        key={member.id}
                        className="flex items-center gap-3 p-4 rounded-xl bg-white/[0.02] hover:bg-white/[0.04] transition-colors"
                      >
                        <UserAvatar user={{ name: member.name || member.member_name }} size="lg" />
                        <div>
                          <p className="font-medium text-white">{member.name || member.member_name}</p>
                          <p className="text-sm text-slate-500">{member.role || '团队成员'}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12 text-slate-500">暂无团队成员</div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Leads Tab - 项目负责人配置 */}
          {activeTab === 'leads' && (
            <ProjectLeadsPanel projectId={parseInt(id)} />
          )}

          {/* Finance Tab */}
          {activeTab === 'finance' && (
            <Card>
              <CardContent>
                {costs.length > 0 ? (
                  <div className="space-y-4">
                    {costs.map((cost) => (
                      <div
                        key={cost.id}
                        className="flex items-center justify-between p-4 rounded-xl bg-white/[0.02]"
                      >
                        <div>
                          <p className="font-medium text-white">{cost.cost_type}</p>
                          <p className="text-sm text-slate-500">{cost.description}</p>
                        </div>
                        <p className="text-lg font-semibold text-primary">
                          {formatCurrency(cost.amount)}
                        </p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12 text-slate-500">暂无财务数据</div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Documents Tab */}
          {activeTab === 'docs' && (
            <Card>
              <CardContent>
                {documents.length > 0 ? (
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    {documents.map((doc) => (
                      <div
                        key={doc.id}
                        className="flex items-center gap-3 p-4 rounded-xl bg-white/[0.02] hover:bg-white/[0.04] transition-colors cursor-pointer"
                      >
                        <div className="p-2 rounded-lg bg-blue-500/20">
                          <FileText className="h-5 w-5 text-blue-400" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-white truncate">{doc.document_name}</p>
                          <p className="text-xs text-slate-500">{doc.document_type}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12 text-slate-500">暂无文档</div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Sprint 3.3: Timeline Tab */}
          {activeTab === 'timeline' && (
            <ProjectTimeline
              projectId={parseInt(id)}
              statusLogs={statusLogs}
              milestones={milestones}
              documents={documents}
            />
          )}
        </motion.div>
      </AnimatePresence>
    </motion.div>
  )
}
