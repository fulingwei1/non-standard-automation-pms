/**
 * 装配技工专用任务中心
 * 核心功能：
 * 1. 工时填报
 * 2. 装配缺料反馈
 * 3. 零部件质量反馈
 * 4. 装配图纸查看
 * 5. 任务完成确认（含工时填报）
 */
import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Wrench,
  Clock,
  AlertTriangle,
  FileWarning,
  FileImage,
  CheckCircle2,
  Circle,
  PlayCircle,
  PauseCircle,
  Package,
  ChevronRight,
  ChevronDown,
  Flag,
  Calendar,
  Timer,
  MapPin,
  User,
  Camera,
  Send,
  X,
  Plus,
  Minus,
  Eye,
  Download,
  ZoomIn,
  ZoomOut,
  RotateCw,
  MessageSquare,
  ClipboardCheck,
} from 'lucide-react'
import { PageHeader } from '../components/layout'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Input,
  Badge,
  Progress,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '../components/ui'
import { cn } from '../lib/utils'
import { fadeIn, staggerContainer } from '../lib/animations'

// 模拟装配任务数据
const mockAssemblyTasks = [
  {
    id: 'AT001',
    title: '框架底座装配',
    projectId: 'PJ250108001',
    projectName: 'BMS老化测试设备',
    machineNo: '1号机',
    workstation: 'A区-工位3',
    status: 'in_progress',
    priority: 'high',
    dueDate: '2026-01-05',
    estimatedHours: 8,
    actualHours: 5.5,
    progress: 50,
    assignee: '赵师傅',  // 任务负责人
    materials: [
      { id: 'M001', name: '铝型材框架 40x40', spec: '2000mm', qty: 12, received: 12, status: 'ok' },
      { id: 'M002', name: '角码连接件', spec: 'L型', qty: 24, received: 24, status: 'ok' },
      { id: 'M003', name: '脚轮组件', spec: '4寸万向轮', qty: 4, received: 4, status: 'ok' },
      { id: 'M004', name: '调平脚', spec: 'M12', qty: 4, received: 4, status: 'ok' },
    ],
    steps: [
      { id: 'S1', title: '检查物料清单，确认零件齐全', completed: true },
      { id: 'S2', title: '按图纸搭建框架底座', completed: true },
      { id: 'S3', title: '安装脚轮和调平脚', completed: false },
      { id: 'S4', title: '调整水平，锁紧螺栓', completed: false },
    ],
    drawings: [
      { id: 'D001', name: '框架装配图', type: 'assembly', url: '/drawings/frame-assembly.pdf' },
      { id: 'D002', name: '脚轮安装图', type: 'detail', url: '/drawings/caster-install.pdf' },
    ],
    notes: '注意框架方正度，误差控制在±1mm',
    tools: ['内六角扳手套装', '气动螺丝刀', '水平仪'],
  },
  {
    id: 'AT002',
    title: '传动机构安装',
    projectId: 'PJ250108001',
    projectName: 'BMS老化测试设备',
    machineNo: '1号机',
    workstation: 'A区-工位3',
    status: 'pending',
    priority: 'high',
    dueDate: '2026-01-06',
    estimatedHours: 6,
    actualHours: 0,
    progress: 0,
    assignee: '赵师傅',
    materials: [
      { id: 'M005', name: '滚珠丝杆 1605', spec: '500mm', qty: 2, received: 2, status: 'ok' },
      { id: 'M006', name: '直线导轨 HGH20', spec: '600mm', qty: 4, received: 4, status: 'ok' },
      { id: 'M007', name: '联轴器', spec: 'φ8-φ10', qty: 2, received: 2, status: 'ok' },
    ],
    steps: [
      { id: 'S1', title: '安装直线导轨，检查平行度', completed: false },
      { id: 'S2', title: '安装丝杆支撑座', completed: false },
      { id: 'S3', title: '装配丝杆和滑块', completed: false },
      { id: 'S4', title: '测试运动顺畅度', completed: false },
    ],
    drawings: [
      { id: 'D003', name: '传动机构装配图', type: 'assembly', url: '/drawings/transmission.pdf' },
    ],
    notes: '丝杆安装需确保同心度',
    tools: ['扭力扳手', '百分表', '塞尺'],
    blockedBy: 'AT001',
  },
  {
    id: 'AT003',
    title: '电气接线',
    projectId: 'PJ250105002',
    projectName: 'EOL功能测试设备',
    machineNo: '2号机',
    workstation: 'B区-工位1',
    status: 'in_progress',
    priority: 'medium',
    dueDate: '2026-01-05',
    estimatedHours: 4,
    actualHours: 1.5,
    progress: 50,
    assignee: '赵师傅',
    materials: [
      { id: 'M008', name: '控制柜', spec: '800x600', qty: 1, received: 1, status: 'ok' },
      { id: 'M009', name: '线缆套装', spec: '1.5mm²', qty: 1, received: 1, status: 'ok' },
      { id: 'M010', name: '端子排', spec: 'UK5N', qty: 10, received: 8, status: 'shortage' },
    ],
    steps: [
      { id: 'S1', title: '安装控制柜', completed: true },
      { id: 'S2', title: '布线走线槽', completed: true },
      { id: 'S3', title: '接线端子', completed: false },
      { id: 'S4', title: '线号标识', completed: false },
    ],
    drawings: [
      { id: 'D004', name: '电气接线图', type: 'wiring', url: '/drawings/wiring.pdf' },
    ],
    notes: '注意接线顺序，参照电气图纸',
    tools: ['剥线钳', '压线钳', '万用表'],
  },
  {
    id: 'AT004',
    title: '气路安装调试',
    projectId: 'PJ250106003',
    projectName: 'ICT测试设备',
    machineNo: '3号机',
    workstation: 'C区-工位2',
    status: 'blocked',
    priority: 'medium',
    dueDate: '2026-01-08',
    estimatedHours: 3,
    actualHours: 0,
    progress: 0,
    assignee: '赵师傅',
    materials: [
      { id: 'M011', name: '气缸 SC50x100', spec: 'SMC', qty: 4, received: 0, status: 'shortage' },
      { id: 'M012', name: 'PU气管', spec: '8mm', qty: 20, received: 20, status: 'ok' },
    ],
    steps: [
      { id: 'S1', title: '安装气缸支架', completed: false },
      { id: 'S2', title: '连接气路管道', completed: false },
      { id: 'S3', title: '调节节流阀', completed: false },
      { id: 'S4', title: '气密性测试', completed: false },
    ],
    drawings: [
      { id: 'D005', name: '气路图', type: 'pneumatic', url: '/drawings/pneumatic.pdf' },
    ],
    notes: '气缸未到货，预计1月7日到',
    tools: ['切管器', '气动快插接头'],
    blockReason: '气缸未到货，预计1月7日到',
  },
  {
    id: 'AT005',
    title: '设备清洁打标',
    projectId: 'PJ250104004',
    projectName: '烧录测试设备',
    machineNo: '4号机',
    workstation: 'D区-工位4',
    status: 'completed',
    priority: 'low',
    dueDate: '2026-01-03',
    completedDate: '2026-01-03',
    estimatedHours: 2,
    actualHours: 1.5,
    progress: 100,
    assignee: '赵师傅',
    materials: [],
    steps: [
      { id: 'S1', title: '清洁设备表面', completed: true },
      { id: 'S2', title: '粘贴标识标签', completed: true },
      { id: 'S3', title: '拍照存档', completed: true },
    ],
    drawings: [],
    notes: '设备已出货',
    tools: ['清洁剂', '标签打印机'],
  },
]

// 状态配置
const statusConfigs = {
  pending: { label: '待开始', icon: Circle, color: 'text-slate-400', bgColor: 'bg-slate-500/10' },
  in_progress: { label: '进行中', icon: PlayCircle, color: 'text-blue-400', bgColor: 'bg-blue-500/10' },
  blocked: { label: '阻塞', icon: PauseCircle, color: 'text-red-400', bgColor: 'bg-red-500/10' },
  completed: { label: '已完成', icon: CheckCircle2, color: 'text-emerald-400', bgColor: 'bg-emerald-500/10' },
}

const priorityConfigs = {
  low: { label: '低', color: 'text-slate-400', bgColor: 'bg-slate-500/10' },
  medium: { label: '中', color: 'text-blue-400', bgColor: 'bg-blue-500/10' },
  high: { label: '高', color: 'text-amber-400', bgColor: 'bg-amber-500/10' },
}

// ============ 缺料反馈对话框组件 ============
function MaterialShortageDialog({ open, onClose, task, material }) {
  const [description, setDescription] = useState('')
  const [urgency, setUrgency] = useState('normal')
  const [quantity, setQuantity] = useState(material?.qty - material?.received || 0)

  const handleSubmit = () => {
    console.log('提交缺料反馈:', { task, material, description, urgency, quantity })
    // TODO: 调用API提交
    onClose()
  }

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-400" />
            缺料反馈
          </DialogTitle>
          <DialogDescription>
            反馈物料短缺情况，系统将通知仓库和采购
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* 任务信息 */}
          <div className="p-3 rounded-lg bg-surface-2/50 text-sm">
            <p className="text-slate-400">任务：{task?.title}</p>
            <p className="text-slate-400">设备：{task?.machineNo} · {task?.workstation}</p>
          </div>

          {/* 物料信息 */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-white">缺料物料</label>
            <div className="p-3 rounded-lg border border-border bg-surface-1">
              <p className="font-medium text-white">{material?.name}</p>
              <p className="text-xs text-slate-400">规格：{material?.spec}</p>
              <div className="flex items-center justify-between mt-2 text-sm">
                <span className="text-slate-400">需求：{material?.qty}</span>
                <span className="text-red-400">已到：{material?.received}</span>
              </div>
            </div>
          </div>

          {/* 缺料数量 */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-white">缺料数量</label>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setQuantity(Math.max(1, quantity - 1))}
              >
                <Minus className="w-4 h-4" />
              </Button>
              <Input
                type="number"
                value={quantity}
                onChange={(e) => setQuantity(parseInt(e.target.value) || 0)}
                className="w-24 text-center"
              />
              <Button
                variant="outline"
                size="sm"
                onClick={() => setQuantity(quantity + 1)}
              >
                <Plus className="w-4 h-4" />
              </Button>
            </div>
          </div>

          {/* 紧急程度 */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-white">紧急程度</label>
            <div className="flex gap-2">
              {[
                { value: 'normal', label: '一般', color: 'bg-slate-500' },
                { value: 'urgent', label: '紧急', color: 'bg-amber-500' },
                { value: 'critical', label: '非常紧急', color: 'bg-red-500' },
              ].map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => setUrgency(opt.value)}
                  className={cn(
                    'flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-all',
                    urgency === opt.value
                      ? `${opt.color} text-white`
                      : 'bg-surface-2 text-slate-400 hover:bg-surface-3'
                  )}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {/* 备注说明 */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-white">备注说明</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="请描述缺料影响和备选方案..."
              className={cn(
                'w-full h-24 px-3 py-2 rounded-lg resize-none',
                'bg-surface-2 border border-border',
                'text-white placeholder:text-slate-500',
                'focus:outline-none focus:ring-2 focus:ring-primary/50'
              )}
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="ghost" onClick={onClose}>取消</Button>
          <Button onClick={handleSubmit}>
            <Send className="w-4 h-4 mr-1" />
            提交反馈
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ============ 质量反馈对话框组件 ============
function QualityFeedbackDialog({ open, onClose, task, material }) {
  const [issueType, setIssueType] = useState('dimension')
  const [description, setDescription] = useState('')
  const [severity, setSeverity] = useState('minor')
  const [photos, setPhotos] = useState([])

  const issueTypes = [
    { value: 'dimension', label: '尺寸偏差' },
    { value: 'surface', label: '表面缺陷' },
    { value: 'function', label: '功能异常' },
    { value: 'damage', label: '运输损坏' },
    { value: 'mismatch', label: '型号不符' },
    { value: 'other', label: '其他问题' },
  ]

  const handleSubmit = () => {
    console.log('提交质量反馈:', { task, material, issueType, description, severity, photos })
    // TODO: 调用API提交
    onClose()
  }

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FileWarning className="w-5 h-5 text-red-400" />
            质量问题反馈
          </DialogTitle>
          <DialogDescription>
            反馈零部件质量问题，系统将通知质检和供应商
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* 物料信息 */}
          {material && (
            <div className="p-3 rounded-lg bg-surface-2/50 text-sm">
              <p className="font-medium text-white">{material.name}</p>
              <p className="text-slate-400">规格：{material.spec}</p>
            </div>
          )}

          {/* 问题类型 */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-white">问题类型</label>
            <div className="grid grid-cols-3 gap-2">
              {issueTypes.map((type) => (
                <button
                  key={type.value}
                  onClick={() => setIssueType(type.value)}
                  className={cn(
                    'py-2 px-3 rounded-lg text-xs font-medium transition-all',
                    issueType === type.value
                      ? 'bg-primary text-white'
                      : 'bg-surface-2 text-slate-400 hover:bg-surface-3'
                  )}
                >
                  {type.label}
                </button>
              ))}
            </div>
          </div>

          {/* 严重程度 */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-white">严重程度</label>
            <div className="flex gap-2">
              {[
                { value: 'minor', label: '轻微', desc: '可继续使用', color: 'bg-yellow-500' },
                { value: 'major', label: '严重', desc: '影响使用', color: 'bg-orange-500' },
                { value: 'critical', label: '致命', desc: '无法使用', color: 'bg-red-500' },
              ].map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => setSeverity(opt.value)}
                  className={cn(
                    'flex-1 py-2 px-2 rounded-lg transition-all text-center',
                    severity === opt.value
                      ? `${opt.color} text-white`
                      : 'bg-surface-2 text-slate-400 hover:bg-surface-3'
                  )}
                >
                  <div className="text-sm font-medium">{opt.label}</div>
                  <div className="text-[10px] opacity-80">{opt.desc}</div>
                </button>
              ))}
            </div>
          </div>

          {/* 问题描述 */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-white">问题描述</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="请详细描述质量问题..."
              className={cn(
                'w-full h-24 px-3 py-2 rounded-lg resize-none',
                'bg-surface-2 border border-border',
                'text-white placeholder:text-slate-500',
                'focus:outline-none focus:ring-2 focus:ring-primary/50'
              )}
            />
          </div>

          {/* 拍照上传 */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-white">拍照取证</label>
            <div className="flex gap-2">
              <button
                className={cn(
                  'w-20 h-20 rounded-lg border-2 border-dashed border-border',
                  'flex flex-col items-center justify-center gap-1',
                  'text-slate-400 hover:text-white hover:border-primary/50',
                  'transition-all'
                )}
              >
                <Camera className="w-6 h-6" />
                <span className="text-[10px]">拍照</span>
              </button>
              {photos.map((photo, i) => (
                <div key={i} className="relative w-20 h-20 rounded-lg overflow-hidden">
                  <img src={photo} alt="" className="w-full h-full object-cover" />
                  <button className="absolute top-1 right-1 p-0.5 rounded-full bg-black/50">
                    <X className="w-3 h-3" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button variant="ghost" onClick={onClose}>取消</Button>
          <Button onClick={handleSubmit} className="bg-red-500 hover:bg-red-600">
            <Send className="w-4 h-4 mr-1" />
            提交反馈
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ============ 图纸查看对话框组件 ============
function DrawingViewerDialog({ open, onClose, task }) {
  const [selectedDrawing, setSelectedDrawing] = useState(null)
  const [zoom, setZoom] = useState(100)

  useEffect(() => {
    if (task?.drawings?.length > 0 && !selectedDrawing) {
      setSelectedDrawing(task.drawings[0])
    }
  }, [task, selectedDrawing])

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FileImage className="w-5 h-5 text-blue-400" />
            装配图纸 - {task?.title}
          </DialogTitle>
        </DialogHeader>

        <div className="flex gap-4 h-[60vh]">
          {/* 图纸列表 */}
          <div className="w-48 flex-shrink-0 space-y-2 overflow-y-auto">
            <p className="text-xs text-slate-400 font-medium uppercase tracking-wider mb-2">
              图纸清单
            </p>
            {task?.drawings?.map((drawing) => (
              <button
                key={drawing.id}
                onClick={() => setSelectedDrawing(drawing)}
                className={cn(
                  'w-full p-3 rounded-lg text-left transition-all',
                  selectedDrawing?.id === drawing.id
                    ? 'bg-primary/20 border border-primary/50'
                    : 'bg-surface-2 hover:bg-surface-3 border border-transparent'
                )}
              >
                <p className="text-sm font-medium text-white truncate">{drawing.name}</p>
                <p className="text-xs text-slate-400 capitalize">{drawing.type}</p>
              </button>
            ))}

            {(!task?.drawings || task.drawings.length === 0) && (
              <div className="text-center py-8 text-slate-500">
                <FileImage className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">暂无图纸</p>
              </div>
            )}
          </div>

          {/* 图纸预览区 */}
          <div className="flex-1 flex flex-col rounded-lg border border-border overflow-hidden">
            {/* 工具栏 */}
            <div className="flex items-center justify-between p-2 border-b border-border bg-surface-2/50">
              <span className="text-sm text-slate-400">
                {selectedDrawing?.name || '请选择图纸'}
              </span>
              <div className="flex items-center gap-1">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setZoom(Math.max(50, zoom - 25))}
                >
                  <ZoomOut className="w-4 h-4" />
                </Button>
                <span className="text-xs text-slate-400 w-12 text-center">{zoom}%</span>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setZoom(Math.min(200, zoom + 25))}
                >
                  <ZoomIn className="w-4 h-4" />
                </Button>
                <Button variant="ghost" size="sm">
                  <RotateCw className="w-4 h-4" />
                </Button>
                <Button variant="ghost" size="sm">
                  <Download className="w-4 h-4" />
                </Button>
              </div>
            </div>

            {/* 图纸内容 */}
            <div className="flex-1 overflow-auto bg-slate-900 flex items-center justify-center p-4">
              {selectedDrawing ? (
                <div
                  className="bg-white rounded shadow-lg"
                  style={{ transform: `scale(${zoom / 100})` }}
                >
                  {/* 模拟图纸预览 */}
                  <div className="w-[600px] h-[400px] flex items-center justify-center text-slate-600">
                    <div className="text-center">
                      <FileImage className="w-16 h-16 mx-auto mb-4 opacity-50" />
                      <p className="font-medium">{selectedDrawing.name}</p>
                      <p className="text-sm text-slate-400 mt-1">
                        图纸文件: {selectedDrawing.url}
                      </p>
                      <p className="text-xs text-slate-400 mt-4">
                        (实际应用中将显示PDF/图片预览)
                      </p>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center text-slate-500">
                  <FileImage className="w-16 h-16 mx-auto mb-4 opacity-50" />
                  <p>请从左侧选择要查看的图纸</p>
                </div>
              )}
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button variant="ghost" onClick={onClose}>关闭</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ============ 任务完成确认对话框（含工时填报）============
function TaskCompleteDialog({ open, onClose, task, onComplete }) {
  const [hours, setHours] = useState(task?.actualHours || 0)
  const [notes, setNotes] = useState('')
  const [issues, setIssues] = useState([])

  const remainingSteps = task?.steps?.filter(s => !s.completed) || []

  const handleSubmit = () => {
    console.log('确认完成:', { task, hours, notes, issues })
    onComplete && onComplete(task.id, hours)
    onClose()
  }

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <ClipboardCheck className="w-5 h-5 text-emerald-400" />
            确认完成任务
          </DialogTitle>
          <DialogDescription>
            确认任务完成并填报工时
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* 任务信息 */}
          <div className="p-3 rounded-lg bg-surface-2/50">
            <p className="font-medium text-white">{task?.title}</p>
            <p className="text-sm text-slate-400">
              {task?.machineNo} · {task?.workstation}
            </p>
          </div>

          {/* 未完成步骤警告 */}
          {remainingSteps.length > 0 && (
            <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/30">
              <p className="text-sm font-medium text-amber-400 mb-2">
                ⚠️ 以下步骤尚未完成：
              </p>
              <ul className="text-xs text-amber-300/80 space-y-1">
                {remainingSteps.map(step => (
                  <li key={step.id}>• {step.title}</li>
                ))}
              </ul>
            </div>
          )}

          {/* 工时填报 */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-white">实际工时</label>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setHours(Math.max(0.5, hours - 0.5))}
                >
                  <Minus className="w-4 h-4" />
                </Button>
                <div className="w-20 text-center">
                  <span className="text-2xl font-bold text-white">{hours}</span>
                  <span className="text-slate-400 ml-1">小时</span>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setHours(hours + 0.5)}
                >
                  <Plus className="w-4 h-4" />
                </Button>
              </div>
              <div className="text-xs text-slate-400">
                预估 {task?.estimatedHours}h
                {hours > task?.estimatedHours && (
                  <span className="text-amber-400 ml-1">
                    (+{(hours - task.estimatedHours).toFixed(1)}h)
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* 完工备注 */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-white">完工备注</label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="记录完工情况、遇到的问题等..."
              className={cn(
                'w-full h-20 px-3 py-2 rounded-lg resize-none',
                'bg-surface-2 border border-border',
                'text-white placeholder:text-slate-500',
                'focus:outline-none focus:ring-2 focus:ring-primary/50'
              )}
            />
          </div>

          {/* 遗留问题 */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-white">遗留问题 (可选)</label>
            <div className="flex flex-wrap gap-2">
              {['需要复检', '有轻微偏差', '待补充物料', '建议优化工艺'].map((issue) => (
                <button
                  key={issue}
                  onClick={() => {
                    if (issues.includes(issue)) {
                      setIssues(issues.filter(i => i !== issue))
                    } else {
                      setIssues([...issues, issue])
                    }
                  }}
                  className={cn(
                    'px-3 py-1 rounded-full text-xs font-medium transition-all',
                    issues.includes(issue)
                      ? 'bg-primary text-white'
                      : 'bg-surface-2 text-slate-400 hover:bg-surface-3'
                  )}
                >
                  {issue}
                </button>
              ))}
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button variant="ghost" onClick={onClose}>取消</Button>
          <Button onClick={handleSubmit} className="bg-emerald-500 hover:bg-emerald-600">
            <CheckCircle2 className="w-4 h-4 mr-1" />
            确认完成
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ============ 任务卡片组件 ============
function AssemblyTaskCard({ task, onAction }) {
  const [expanded, setExpanded] = useState(false)
  const [materialsExpanded, setMaterialsExpanded] = useState(false)
  const status = statusConfigs[task.status]
  const priority = priorityConfigs[task.priority]
  const StatusIcon = status.icon

  const hasShortage = task.materials?.some(m => m.status === 'shortage')
  const completedSteps = task.steps?.filter(s => s.completed).length || 0
  const totalSteps = task.steps?.length || 0

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        'rounded-xl border overflow-hidden',
        task.status === 'blocked'
          ? 'bg-red-500/5 border-red-500/30'
          : hasShortage
          ? 'bg-amber-500/5 border-amber-500/30'
          : 'bg-surface-1 border-border'
      )}
    >
      <div className="p-4">
        {/* 头部信息 */}
        <div className="flex items-start gap-3 mb-3">
          <div className={cn('p-2 rounded-lg', status.bgColor)}>
            <StatusIcon className={cn('w-5 h-5', status.color)} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <Badge className={cn('text-xs', priority.bgColor, priority.color)}>
                {priority.label}优先级
              </Badge>
              <Badge variant="outline" className="text-xs">
                {task.machineNo}
              </Badge>
            </div>
            <h3 className="font-semibold text-white text-lg">{task.title}</h3>
            <p className="text-sm text-slate-400">
              {task.projectName} · {task.workstation}
            </p>
          </div>
        </div>

        {/* 阻塞原因 */}
        {task.blockReason && (
          <div className="mb-3 p-2 rounded-lg bg-red-500/10 text-sm text-red-300 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 flex-shrink-0" />
            {task.blockReason}
          </div>
        )}

        {/* 进度信息 */}
        {task.status !== 'completed' && (
          <div className="mb-3">
            <div className="flex items-center justify-between text-sm mb-1">
              <span className="text-slate-400">进度</span>
              <span className="text-white">{completedSteps}/{totalSteps} 步骤</span>
            </div>
            <Progress value={(completedSteps / totalSteps) * 100} className="h-2" />
          </div>
        )}

        {/* 元信息 */}
        <div className="flex items-center flex-wrap gap-x-4 gap-y-1 text-xs text-slate-400 mb-3">
          <span className="flex items-center gap-1">
            <User className="w-3.5 h-3.5 text-primary" />
            <span className="text-white font-medium">{task.assignee}</span>
          </span>
          <span className="flex items-center gap-1">
            <Calendar className="w-3.5 h-3.5" />
            截止: {task.dueDate}
          </span>
          <span className="flex items-center gap-1">
            <Timer className="w-3.5 h-3.5" />
            {task.actualHours}/{task.estimatedHours}h
          </span>
          <span className="flex items-center gap-1">
            <MapPin className="w-3.5 h-3.5" />
            {task.workstation}
          </span>
        </div>

        {/* 物料准备 */}
        {task.materials?.length > 0 && (
          <div className="mb-3">
            <button
              onClick={() => setMaterialsExpanded(!materialsExpanded)}
              className="w-full flex items-center justify-between py-2 text-sm"
            >
              <span className="flex items-center gap-2">
                <Package className={cn('w-4 h-4', hasShortage ? 'text-amber-400' : 'text-emerald-400')} />
                <span className="text-slate-300">
                  物料准备 ({task.materials.filter(m => m.status === 'ok').length}/{task.materials.length})
                </span>
                {hasShortage && (
                  <Badge className="text-[10px] bg-amber-500/20 text-amber-400">
                    有缺料
                  </Badge>
                )}
              </span>
              <ChevronRight className={cn(
                'w-4 h-4 text-slate-400 transition-transform',
                materialsExpanded && 'rotate-90'
              )} />
            </button>

            <AnimatePresence>
              {materialsExpanded && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="overflow-hidden"
                >
                  <div className="space-y-2 pt-2">
                    {task.materials.map((material) => (
                      <div
                        key={material.id}
                        className={cn(
                          'flex items-center justify-between p-2 rounded-lg',
                          material.status === 'shortage' ? 'bg-amber-500/10' : 'bg-surface-2/50'
                        )}
                      >
                        <div className="flex items-center gap-2">
                          {material.status === 'ok' ? (
                            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                          ) : (
                            <AlertTriangle className="w-4 h-4 text-amber-400" />
                          )}
                          <div>
                            <p className="text-sm text-white">{material.name}</p>
                            <p className="text-xs text-slate-400">
                              {material.spec} × {material.received}/{material.qty}
                            </p>
                          </div>
                        </div>
                        {material.status === 'shortage' && (
                          <div className="flex gap-1">
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-7 text-xs text-amber-400"
                              onClick={() => onAction('shortage', task, material)}
                            >
                              反馈缺料
                            </Button>
                          </div>
                        )}
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-7 w-7 p-0 text-slate-400"
                          onClick={() => onAction('quality', task, material)}
                        >
                          <FileWarning className="w-4 h-4" />
                        </Button>
                      </div>
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        )}

        {/* 作业步骤 */}
        {task.steps?.length > 0 && (
          <div className="mb-3">
            <button
              onClick={() => setExpanded(!expanded)}
              className="w-full flex items-center justify-between py-2 text-sm"
            >
              <span className="flex items-center gap-2">
                <Wrench className="w-4 h-4 text-blue-400" />
                <span className="text-slate-300">作业步骤</span>
              </span>
              <ChevronRight className={cn(
                'w-4 h-4 text-slate-400 transition-transform',
                expanded && 'rotate-90'
              )} />
            </button>

            <AnimatePresence>
              {expanded && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="overflow-hidden"
                >
                  <div className="space-y-2 pt-2">
                    {task.steps.map((step, index) => (
                      <button
                        key={step.id}
                        className={cn(
                          'w-full flex items-center gap-3 p-2 rounded-lg text-left',
                          'transition-all hover:bg-surface-2',
                          step.completed ? 'opacity-60' : ''
                        )}
                      >
                        <div className={cn(
                          'w-6 h-6 rounded-full border-2 flex items-center justify-center flex-shrink-0',
                          step.completed
                            ? 'bg-emerald-500 border-emerald-500'
                            : 'border-slate-500'
                        )}>
                          {step.completed ? (
                            <CheckCircle2 className="w-4 h-4 text-white" />
                          ) : (
                            <span className="text-xs text-slate-400">{index + 1}</span>
                          )}
                        </div>
                        <span className={cn(
                          'text-sm',
                          step.completed ? 'text-slate-500 line-through' : 'text-slate-200'
                        )}>
                          {step.title}
                        </span>
                      </button>
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        )}

        {/* 注意事项 */}
        {task.notes && (
          <div className="mb-3 p-2 rounded-lg bg-blue-500/10 text-sm text-blue-300 flex items-start gap-2">
            <MessageSquare className="w-4 h-4 flex-shrink-0 mt-0.5" />
            {task.notes}
          </div>
        )}

        {/* 所需工具 */}
        {task.tools?.length > 0 && (
          <p className="text-xs text-slate-500 mb-3">
            所需工具：{task.tools.join('、')}
          </p>
        )}

        {/* 操作按钮 */}
        <div className="flex items-center gap-2 pt-3 border-t border-border/50">
          <Button
            variant="outline"
            size="sm"
            className="flex-1"
            onClick={() => onAction('drawing', task)}
          >
            <FileImage className="w-4 h-4 mr-1" />
            查看图纸
          </Button>

          {task.status === 'in_progress' && (
            <Button
              size="sm"
              className="flex-1 bg-emerald-500 hover:bg-emerald-600"
              onClick={() => onAction('complete', task)}
            >
              <CheckCircle2 className="w-4 h-4 mr-1" />
              确认完成
            </Button>
          )}

          {task.status === 'pending' && !task.blockedBy && (
            <Button
              size="sm"
              className="flex-1"
              onClick={() => onAction('start', task)}
            >
              <PlayCircle className="w-4 h-4 mr-1" />
              开始任务
            </Button>
          )}
        </div>
      </div>
    </motion.div>
  )
}

// ============ 主组件 ============
export default function AssemblerTaskCenter() {
  const [tasks, setTasks] = useState(mockAssemblyTasks)
  const [statusFilter, setStatusFilter] = useState('all')
  const [shortageDialog, setShortageDialog] = useState({ open: false, task: null, material: null })
  const [qualityDialog, setQualityDialog] = useState({ open: false, task: null, material: null })
  const [drawingDialog, setDrawingDialog] = useState({ open: false, task: null })
  const [completeDialog, setCompleteDialog] = useState({ open: false, task: null })

  // 过滤任务
  const filteredTasks = tasks.filter((task) => {
    if (statusFilter === 'all') return true
    return task.status === statusFilter
  })

  // 统计
  const stats = {
    total: tasks.length,
    in_progress: tasks.filter(t => t.status === 'in_progress').length,
    pending: tasks.filter(t => t.status === 'pending').length,
    blocked: tasks.filter(t => t.status === 'blocked').length,
    completed: tasks.filter(t => t.status === 'completed').length,
    shortage: tasks.filter(t => t.materials?.some(m => m.status === 'shortage')).length,
  }

  // 处理操作
  const handleAction = (action, task, material = null) => {
    switch (action) {
      case 'shortage':
        setShortageDialog({ open: true, task, material })
        break
      case 'quality':
        setQualityDialog({ open: true, task, material })
        break
      case 'drawing':
        setDrawingDialog({ open: true, task })
        break
      case 'complete':
        setCompleteDialog({ open: true, task })
        break
      case 'start':
        setTasks(prev => prev.map(t =>
          t.id === task.id ? { ...t, status: 'in_progress' } : t
        ))
        break
    }
  }

  // 完成任务
  const handleComplete = (taskId, hours) => {
    setTasks(prev => prev.map(t =>
      t.id === taskId
        ? { ...t, status: 'completed', actualHours: hours, progress: 100, completedDate: new Date().toISOString().split('T')[0] }
        : t
    ))
  }

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      <PageHeader
        title="我的装配任务"
        description={`今日待完成 ${stats.in_progress} 项，共 ${stats.total} 项任务`}
        actions={
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => setShortageDialog({ open: true, task: null, material: null })}>
              <AlertTriangle className="w-4 h-4 mr-1" />
              反馈缺料
            </Button>
            <Button variant="outline" onClick={() => setQualityDialog({ open: true, task: null, material: null })}>
              <FileWarning className="w-4 h-4 mr-1" />
              质量反馈
            </Button>
          </div>
        }
      />

      {/* 统计卡片 */}
      <motion.div variants={fadeIn} className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {[
          { key: 'in_progress', label: '进行中', icon: PlayCircle, color: 'text-blue-400', value: stats.in_progress },
          { key: 'pending', label: '待开始', icon: Circle, color: 'text-slate-400', value: stats.pending },
          { key: 'blocked', label: '已阻塞', icon: PauseCircle, color: 'text-red-400', value: stats.blocked },
          { key: 'completed', label: '已完成', icon: CheckCircle2, color: 'text-emerald-400', value: stats.completed },
          { key: 'shortage', label: '缺料任务', icon: AlertTriangle, color: 'text-amber-400', value: stats.shortage },
        ].map((stat) => (
          <Card key={stat.key} className="bg-surface-1/50">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400">{stat.label}</p>
                  <p className="text-2xl font-bold text-white mt-1">{stat.value}</p>
                </div>
                <stat.icon className={cn('w-6 h-6', stat.color)} />
              </div>
            </CardContent>
          </Card>
        ))}
      </motion.div>

      {/* 筛选按钮 */}
      <motion.div variants={fadeIn} className="flex gap-2 flex-wrap">
        {[
          { value: 'all', label: '全部任务' },
          { value: 'in_progress', label: '进行中' },
          { value: 'pending', label: '待开始' },
          { value: 'blocked', label: '已阻塞' },
          { value: 'completed', label: '已完成' },
        ].map((filter) => (
          <Button
            key={filter.value}
            variant={statusFilter === filter.value ? 'default' : 'ghost'}
            size="sm"
            onClick={() => setStatusFilter(filter.value)}
          >
            {filter.label}
          </Button>
        ))}
      </motion.div>

      {/* 任务列表 */}
      <motion.div variants={fadeIn} className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {filteredTasks.map((task) => (
          <AssemblyTaskCard
            key={task.id}
            task={task}
            onAction={handleAction}
          />
        ))}
      </motion.div>

      {/* 空状态 */}
      {filteredTasks.length === 0 && (
        <motion.div variants={fadeIn} className="text-center py-16">
          <Wrench className="w-16 h-16 mx-auto text-slate-600 mb-4" />
          <h3 className="text-lg font-medium text-slate-400">暂无任务</h3>
          <p className="text-sm text-slate-500 mt-1">
            {statusFilter !== 'all' ? '没有符合条件的任务' : '当前没有分配给您的装配任务'}
          </p>
        </motion.div>
      )}

      {/* 对话框 */}
      <MaterialShortageDialog
        open={shortageDialog.open}
        onClose={() => setShortageDialog({ open: false, task: null, material: null })}
        task={shortageDialog.task}
        material={shortageDialog.material}
      />

      <QualityFeedbackDialog
        open={qualityDialog.open}
        onClose={() => setQualityDialog({ open: false, task: null, material: null })}
        task={qualityDialog.task}
        material={qualityDialog.material}
      />

      <DrawingViewerDialog
        open={drawingDialog.open}
        onClose={() => setDrawingDialog({ open: false, task: null })}
        task={drawingDialog.task}
      />

      <TaskCompleteDialog
        open={completeDialog.open}
        onClose={() => setCompleteDialog({ open: false, task: null })}
        task={completeDialog.task}
        onComplete={handleComplete}
      />
    </motion.div>
  )
}

