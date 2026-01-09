/**
 * Work Log Page - 工作日志页面
 * Features: 每日工作日志提交，@提及项目/设备/人员，自动关联到项目进展
 */
import { useState, useEffect } from 'react'
import {
  FileText,
  AtSign,
  Save,
  Edit,
  Trash2,
} from 'lucide-react'
import { PageHeader } from '../components/layout'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import { Badge } from '../components/ui/badge'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select'

import { Textarea } from '../components/ui/textarea'
import { cn, formatDate } from '../lib/utils'
import { workLogApi } from '../services/api'

export default function WorkLog() {
  const [loading, setLoading] = useState(false)
  const [workLogs, setWorkLogs] = useState([])
  const [mentionOptions, setMentionOptions] = useState({
    projects: [],
    machines: [],
    users: [],
  })
  
  // 表单数据
  const [workDate, setWorkDate] = useState(new Date().toISOString().split('T')[0])
  const [content, setContent] = useState('')
  const [mentionedProjects, setMentionedProjects] = useState([])
  const [mentionedMachines, setMentionedMachines] = useState([])
  const [mentionedUsers, setMentionedUsers] = useState([])
  const [status, setStatus] = useState('SUBMITTED')
  
  // 编辑相关
  const [editingId, setEditingId] = useState(null)
  
  // 分页
  const [page, setPage] = useState(1)
  const [pageSize] = useState(20)
  const [total, setTotal] = useState(0)
  
  // 筛选
  const [filterStartDate, setFilterStartDate] = useState('')
  const [filterEndDate, setFilterEndDate] = useState('')
  
  useEffect(() => {
    fetchMentionOptions()
    fetchWorkLogs()
  }, [page, filterStartDate, filterEndDate])
  
  const fetchMentionOptions = async () => {
    try {
      const res = await workLogApi.getMentionOptions()
      const data = res.data?.data || res.data || {}
      setMentionOptions({
        projects: data.projects || [],
        machines: data.machines || [],
        users: data.users || [],
      })
    } catch (error) {
      console.error('操作失败:', error)
    }
  }
  
  const fetchWorkLogs = async () => {
    try {
      setLoading(true)
      const params = {
        page,
        page_size: pageSize,
      }
      if (filterStartDate) params.start_date = filterStartDate
      if (filterEndDate) params.end_date = filterEndDate
      
      const res = await workLogApi.list(params)
      const data = res.data?.data || res.data || {}
      setWorkLogs(data.items || [])
      setTotal(data.total || 0)
    } catch (error) {
      console.error('操作失败:', error)
    } finally {
      setLoading(false)
    }
  }
  
  const handleSubmit = async () => {
    if (!content.trim()) {
      alert('请填写工作内容')
      return
    }
    
    if (content.length > 300) {
      alert('工作内容不能超过300字')
      return
    }
    
    try {
      const data = {
        work_date: workDate,
        content: content.trim(),
        mentioned_projects: mentionedProjects,
        mentioned_machines: mentionedMachines,
        mentioned_users: mentionedUsers,
        status,
      }
      
      if (editingId) {
        await workLogApi.update(editingId, data)
        alert('工作日志更新成功')
      } else {
        await workLogApi.create(data)
        alert('工作日志提交成功')
      }
      
      // 重置表单
      resetForm()
      fetchWorkLogs()
    } catch (error) {
      alert('提交失败: ' + (error.response?.data?.detail || error.message))
    }
  }
  
  const handleEdit = (workLog) => {
    if (workLog.status !== 'DRAFT') {
      alert('只能编辑草稿状态的工作日志')
      return
    }
    
    setEditingId(workLog.id)
    setWorkDate(workLog.work_date)
    setContent(workLog.content)
    setStatus(workLog.status)
    
    // 设置提及
    const projects = workLog.mentions?.filter(m => m.mention_type === 'PROJECT').map(m => m.mention_id) || []
    const machines = workLog.mentions?.filter(m => m.mention_type === 'MACHINE').map(m => m.mention_id) || []
    const users = workLog.mentions?.filter(m => m.mention_type === 'USER').map(m => m.mention_id) || []
    
    setMentionedProjects(projects)
    setMentionedMachines(machines)
    setMentionedUsers(users)
    
    setShowEditDialog(true)
  }
  
  const handleDelete = async (id) => {
    if (!confirm('确定要删除这条工作日志吗？')) return
    
    try {
      await workLogApi.delete(id)
      alert('删除成功')
      fetchWorkLogs()
    } catch (error) {
      alert('删除失败: ' + (error.response?.data?.detail || error.message))
    }
  }
  
  const resetForm = () => {
    setEditingId(null)
    setWorkDate(new Date().toISOString().split('T')[0])
    setContent('')
    setMentionedProjects([])
    setMentionedMachines([])
    setMentionedUsers([])
    setStatus('SUBMITTED')

  }
  
  const getStatusBadge = (status) => {
    if (status === 'SUBMITTED') {
      return <Badge className="bg-green-500">已提交</Badge>
    }
    return <Badge variant="outline">草稿</Badge>
  }
  
  const wordCount = content.length
  const maxWords = 300
  
  return (
    <div className="space-y-6 p-6">
      <PageHeader
        title="工作日志"
        description="记录每日工作内容，@提及项目、设备或人员，自动关联到项目进展"
      />
      
      {/* 提交表单 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            提交工作日志
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">
                工作日期 <span className="text-red-500">*</span>
              </label>
              <Input
                type="date"
                value={workDate}
                onChange={(e) => setWorkDate(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">状态</label>
              <Select value={status} onValueChange={setStatus}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="DRAFT">草稿</SelectItem>
                  <SelectItem value="SUBMITTED">已提交</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-2">
              工作内容 <span className="text-red-500">*</span>
              <span className="text-sm text-gray-500 ml-2">
                ({wordCount}/{maxWords} 字)
              </span>
            </label>
            <Textarea
              value={content}
              onChange={(e) => {
                const value = e.target.value
                if (value.length <= maxWords) {
                  setContent(value)
                }
              }}
              placeholder="请输入工作内容（不超过300字）..."
              rows={6}
              className={cn(
                wordCount > maxWords && "border-red-500"
              )}
            />
            {wordCount > maxWords && (
              <p className="text-sm text-red-500 mt-1">
                字数超出限制，请删除多余内容
              </p>
            )}
          </div>
          
          {/* @提及 */}
          <div className="space-y-3">
            <label className="block text-sm font-medium flex items-center gap-2">
              <AtSign className="h-4 w-4" />
              @提及（可选）
            </label>
            
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-xs text-gray-500 mb-1">项目</label>
                <Select
                  value={mentionedProjects[0]?.toString() || '__none__'}
                  onValueChange={(value) => {
                    if (value && value !== '__none__') {
                      setMentionedProjects([parseInt(value)])
                    } else {
                      setMentionedProjects([])
                    }
                  }}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="选择项目" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__none__">无</SelectItem>
                    {mentionOptions.projects.map((project) => (
                      <SelectItem key={project.id} value={project.id.toString()}>
                        {project.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              <div>
                <label className="block text-xs text-gray-500 mb-1">设备</label>
                <Select
                  value={mentionedMachines[0]?.toString() || '__none__'}
                  onValueChange={(value) => {
                    if (value && value !== '__none__') {
                      setMentionedMachines([parseInt(value)])
                    } else {
                      setMentionedMachines([])
                    }
                  }}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="选择设备" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__none__">无</SelectItem>
                    {mentionOptions.machines.map((machine) => (
                      <SelectItem key={machine.id} value={machine.id.toString()}>
                        {machine.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              <div>
                <label className="block text-xs text-gray-500 mb-1">人员</label>
                <Select
                  value={mentionedUsers[0]?.toString() || '__none__'}
                  onValueChange={(value) => {
                    if (value && value !== '__none__') {
                      setMentionedUsers([parseInt(value)])
                    } else {
                      setMentionedUsers([])
                    }
                  }}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="选择人员" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__none__">无</SelectItem>
                    {mentionOptions.users.map((user) => (
                      <SelectItem key={user.id} value={user.id.toString()}>
                        {user.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>
          
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={resetForm}>
              重置
            </Button>
            <Button onClick={handleSubmit} disabled={!content.trim() || wordCount > maxWords}>
              <Save className="h-4 w-4 mr-2" />
              {editingId ? '更新' : '提交'}
            </Button>
          </div>
        </CardContent>
      </Card>
      
      {/* 历史日志列表 */}
      <Card>
        <CardHeader>
          <CardTitle>历史日志</CardTitle>
        </CardHeader>
        <CardContent>
          {/* 筛选 */}
          <div className="flex gap-4 mb-4">
            <Input
              type="date"
              placeholder="开始日期"
              value={filterStartDate}
              onChange={(e) => setFilterStartDate(e.target.value)}
              className="w-40"
            />
            <Input
              type="date"
              placeholder="结束日期"
              value={filterEndDate}
              onChange={(e) => setFilterEndDate(e.target.value)}
              className="w-40"
            />
            <Button
              variant="outline"
              onClick={() => {
                setFilterStartDate('')
                setFilterEndDate('')
              }}
            >
              清除筛选
            </Button>
          </div>
          
          {loading ? (
            <div className="text-center py-8">加载中...</div>
          ) : workLogs.length === 0 ? (
            <div className="text-center py-8 text-gray-500">暂无工作日志</div>
          ) : (
            <div className="space-y-3">
              {workLogs.map((log) => (
                <div
                  key={log.id}
                  className="p-4 border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="font-medium">{log.user_name || '未知用户'}</span>
                        {getStatusBadge(log.status)}
                        <span className="text-sm text-gray-500">
                          {formatDate(log.work_date)}
                        </span>
                      </div>
                      
                      <p className="text-sm text-gray-700 dark:text-gray-300 mb-2">
                        {log.content}
                      </p>
                      
                      {log.mentions && log.mentions.length > 0 && (
                        <div className="flex flex-wrap gap-2 mt-2">
                          {log.mentions.map((mention, idx) => (
                            <Badge key={idx} variant="outline" className="text-xs">
                              <AtSign className="h-3 w-3 mr-1" />
                              {mention.mention_name}
                            </Badge>
                          ))}
                        </div>
                      )}
                    </div>
                    
                    <div className="flex gap-2">
                      {log.status === 'DRAFT' && (
                        <>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleEdit(log)}
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDelete(log.id)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              ))}
              
              {/* 分页 */}
              {total > pageSize && (
                <div className="flex justify-center gap-2 mt-4">
                  <Button
                    variant="outline"
                    disabled={page === 1}
                    onClick={() => setPage(page - 1)}
                  >
                    上一页
                  </Button>
                  <span className="flex items-center px-4">
                    第 {page} 页，共 {Math.ceil(total / pageSize)} 页
                  </span>
                  <Button
                    variant="outline"
                    disabled={page >= Math.ceil(total / pageSize)}
                    onClick={() => setPage(page + 1)}
                  >
                    下一页
                  </Button>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
