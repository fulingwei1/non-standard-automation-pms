/**
 * Work Log Config Page - 工作日志配置页面（管理员）
 * Features: 配置哪些人需要提交工作日志
 */
import { useState, useEffect } from 'react'
import {
  Settings,
  Plus,
  Edit,
  Trash2,
  Save,
  X,
  Users,
  Building,
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
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter,
} from '../components/ui/dialog'
import { Switch } from '../components/ui/switch'
import { workLogApi, userApi, departmentApi } from '../services/api'

export default function WorkLogConfig() {
  const [loading, setLoading] = useState(false)
  const [configs, setConfigs] = useState([])
  const [users, setUsers] = useState([])
  const [departments, setDepartments] = useState([])
  
  // 表单
  const [showFormDialog, setShowFormDialog] = useState(false)
  const [editingId, setEditingId] = useState(null)
  const [formData, setFormData] = useState({
    user_id: null,
    department_id: null,
    is_required: true,
    is_active: true,
    remind_time: '18:00',
  })
  
  useEffect(() => {
    fetchConfigs()
    fetchUsers()
    fetchDepartments()
  }, [])
  
  const fetchConfigs = async () => {
    try {
      setLoading(true)
      const res = await workLogApi.listConfigs()
      const data = res.data?.data || res.data || {}
      setConfigs(data.items || [])
    } catch (error) {
      console.error('Failed to fetch configs:', error)
    } finally {
      setLoading(false)
    }
  }
  
  const fetchUsers = async () => {
    try {
      const res = await userApi.list()
      const data = res.data?.data || res.data || {}
      setUsers(data.items || data || [])
    } catch (error) {
      console.error('Failed to fetch users:', error)
    }
  }
  
  const fetchDepartments = async () => {
    try {
      const res = await departmentApi.list()
      const data = res.data?.data || res.data || {}
      setDepartments(data.items || data || [])
    } catch (error) {
      console.error('Failed to fetch departments:', error)
    }
  }
  
  const handleCreate = () => {
    setEditingId(null)
    setFormData({
      user_id: null,
      department_id: null,
      is_required: true,
      is_active: true,
      remind_time: '18:00',
    })
    setShowFormDialog(true)
  }
  
  const handleEdit = (config) => {
    setEditingId(config.id)
    setFormData({
      user_id: config.user_id || null,
      department_id: config.department_id || null,
      is_required: config.is_required,
      is_active: config.is_active,
      remind_time: config.remind_time,
    })
    setShowFormDialog(true)
  }
  
  const handleSubmit = async () => {
    try {
      const data = {
        ...formData,
        user_id: formData.user_id || undefined,
        department_id: formData.department_id || undefined,
      }
      
      if (editingId) {
        await workLogApi.updateConfig(editingId, data)
        alert('配置更新成功')
      } else {
        await workLogApi.createConfig(data)
        alert('配置创建成功')
      }
      
      setShowFormDialog(false)
      fetchConfigs()
    } catch (error) {
      console.error('Failed to save config:', error)
      alert('保存失败: ' + (error.response?.data?.detail || error.message))
    }
  }
  
  const getScopeLabel = (config) => {
    if (config.user_id) {
      const user = users.find(u => u.id === config.user_id)
      return user ? `用户: ${user.real_name || user.username}` : `用户ID: ${config.user_id}`
    }
    if (config.department_id) {
      const dept = departments.find(d => d.id === config.department_id)
      return dept ? `部门: ${dept.name}` : `部门ID: ${config.department_id}`
    }
    return '全员'
  }
  
  return (
    <div className="space-y-6 p-6">
      <PageHeader
        title="工作日志配置"
        description="配置哪些人需要提交工作日志"
      />
      
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Settings className="h-5 w-5" />
              配置列表
            </CardTitle>
            <Button onClick={handleCreate}>
              <Plus className="h-4 w-4 mr-2" />
              新建配置
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8">加载中...</div>
          ) : configs.length === 0 ? (
            <div className="text-center py-8 text-gray-500">暂无配置</div>
          ) : (
            <div className="space-y-3">
              {configs.map((config) => (
                <div
                  key={config.id}
                  className="p-4 border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="font-medium">{getScopeLabel(config)}</span>
                        {config.is_active ? (
                          <Badge className="bg-green-500">启用</Badge>
                        ) : (
                          <Badge variant="outline">禁用</Badge>
                        )}
                        {config.is_required && (
                          <Badge variant="outline">必须提交</Badge>
                        )}
                      </div>
                      <div className="text-sm text-gray-500">
                        提醒时间: {config.remind_time}
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleEdit(config)}
                      >
                        <Edit className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
      
      {/* 表单对话框 */}
      <Dialog open={showFormDialog} onOpenChange={setShowFormDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>
              {editingId ? '编辑配置' : '新建配置'}
            </DialogTitle>
          </DialogHeader>
          <DialogBody className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">适用范围</label>
              <div className="space-y-3">
                <div>
                  <label className="block text-xs text-gray-500 mb-1">用户（可选）</label>
                  <Select
                    value={$?.toString() || '__none__'}
                    onValueChange={(value) => {
                      setFormData({
                        ...formData,
                        user_id: value ? parseInt(value) : null,
                        department_id: value ? null : formData.department_id,
                      })
                    }}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="选择用户（留空表示不限制用户）" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="__none__">无（不限制用户）</SelectItem>
                      {users.map((user) => (
                        <SelectItem key={user.id} value={user.id.toString()}>
                          {user.real_name || user.username}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                
                <div>
                  <label className="block text-xs text-gray-500 mb-1">部门（可选）</label>
                  <Select
                    value={$?.toString() || '__none__'}
                    onValueChange={(value) => {
                      setFormData({
                        ...formData,
                        department_id: value ? parseInt(value) : null,
                        user_id: value ? null : formData.user_id,
                      })
                    }}
                    disabled={!!formData.user_id}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="选择部门（留空表示全员）" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="__none__">无（全员）</SelectItem>
                      {departments.map((dept) => (
                        <SelectItem key={dept.id} value={dept.id.toString()}>
                          {dept.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                
                {!formData.user_id && !formData.department_id && (
                  <div className="text-sm text-gray-500">
                    未选择用户和部门，表示适用于全员
                  </div>
                )}
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-2">提醒时间</label>
              <Input
                type="time"
                value={formData.remind_time}
                onChange={(e) => setFormData({ ...formData, remind_time: e.target.value })}
              />
            </div>
            
            <div className="flex items-center justify-between">
              <div>
                <label className="block text-sm font-medium mb-2">必须提交</label>
                <p className="text-xs text-gray-500">是否要求必须提交工作日志</p>
              </div>
              <Switch
                checked={formData.is_required}
                onCheckedChange={(checked) => setFormData({ ...formData, is_required: checked })}
              />
            </div>
            
            <div className="flex items-center justify-between">
              <div>
                <label className="block text-sm font-medium mb-2">启用</label>
                <p className="text-xs text-gray-500">是否启用此配置</p>
              </div>
              <Switch
                checked={formData.is_active}
                onCheckedChange={(checked) => setFormData({ ...formData, is_active: checked })}
              />
            </div>
          </DialogBody>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowFormDialog(false)}>
              取消
            </Button>
            <Button onClick={handleSubmit}>
              <Save className="h-4 w-4 mr-2" />
              保存
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
