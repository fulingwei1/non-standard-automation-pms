/**
 * 项目快速操作面板组件
 * 
 * Issue 3.3: 阶段推进、状态更新、常用操作快捷入口
 */

import { useState } from 'react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
  Button,
  Badge,
} from '../ui'
import {
  MoreHorizontal,
  ArrowRight,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  FileText,
  Download,
  Settings,
  Loader2,
} from 'lucide-react'
import { projectApi } from '../../services/api'
import { toast } from '../ui/toast'
import { useNavigate } from 'react-router-dom'

export default function QuickActionPanel({ project, onRefresh }) {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  
  // 检查是否可以推进阶段
  const canAdvanceStage = () => {
    if (!project?.stage) return false
    const stageOrder = parseInt(project.stage.replace('S', ''))
    return stageOrder < 9
  }
  
  // 检查自动流转
  const handleCheckAutoTransition = async () => {
    if (!project?.id) return
    
    setLoading(true)
    try {
      const response = await projectApi.checkAutoTransition(project.id, true)
      if (response.data?.auto_advanced) {
        toast.success(`项目已推进至 ${response.data.current_stage} 阶段`)
        if (onRefresh) {
          onRefresh()
        }
      } else {
        toast.info(response.data?.message || '当前不满足自动流转条件')
      }
    } catch (err) {
      console.error('Failed to check auto transition:', err)
      toast.error(err.response?.data?.detail || '无法检查自动流转')
    } finally {
      setLoading(false)
    }
  }
  
  // 更新项目状态
  const handleUpdateStatus = (status) => {
    // 可以打开状态更新对话框
    toast.info('状态更新功能即将上线')
  }
  
  // 导出项目数据
  const handleExport = () => {
    toast.info('数据导出功能即将上线')
  }
  
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="secondary" size="icon" disabled={loading}>
          <MoreHorizontal className="h-4 w-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        <DropdownMenuLabel>快速操作</DropdownMenuLabel>
        <DropdownMenuSeparator />
        
        {/* 阶段推进 */}
        {canAdvanceStage() && (
          <>
            <DropdownMenuItem
              onClick={handleCheckAutoTransition}
              disabled={loading}
            >
              <ArrowRight className="h-4 w-4 mr-2" />
              检查自动流转
            </DropdownMenuItem>
            <DropdownMenuSeparator />
          </>
        )}
        
        {/* 状态更新 */}
        <DropdownMenuItem onClick={() => handleUpdateStatus('ST08')}>
          <CheckCircle2 className="h-4 w-4 mr-2" />
          更新状态
        </DropdownMenuItem>
        
        {/* 刷新数据 */}
        <DropdownMenuItem onClick={onRefresh} disabled={loading}>
          {loading ? (
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
          ) : (
            <RefreshCw className="h-4 w-4 mr-2" />
          )}
          刷新数据
        </DropdownMenuItem>
        
        <DropdownMenuSeparator />
        
        {/* 其他操作 */}
        <DropdownMenuItem onClick={() => navigate(`/projects/${project.id}/documents`)}>
          <FileText className="h-4 w-4 mr-2" />
          查看文档
        </DropdownMenuItem>
        
        <DropdownMenuItem onClick={handleExport}>
          <Download className="h-4 w-4 mr-2" />
          导出数据
        </DropdownMenuItem>
        
        <DropdownMenuItem onClick={() => navigate(`/projects/${project.id}/settings`)}>
          <Settings className="h-4 w-4 mr-2" />
          项目设置
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
