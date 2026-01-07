/**
 * Material Transfer New - 新建物料调拨申请
 * 创建物料调拨申请，支持项目间调拨
 */

import { useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  ArrowLeft,
  ArrowRightLeft,
  Save,
  X,
  Search,
  AlertTriangle,
} from 'lucide-react'
import { PageHeader } from '../components/layout'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
  Button,
  Input,
  Label,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Textarea,
} from '../components/ui'
import { fadeIn } from '../lib/animations'
import { shortageApi, projectApi, materialApi } from '../services/api'

const urgentLevels = [
  { value: 'NORMAL', label: '普通' },
  { value: 'URGENT', label: '紧急' },
  { value: 'CRITICAL', label: '特急' },
]

export default function TransferNew() {
  const navigate = useNavigate()
  const location = useLocation()
  const [loading, setLoading] = useState(false)
  const [projects, setProjects] = useState([])
  const [materials, setMaterials] = useState([])
  const [searchKeyword, setSearchKeyword] = useState('')
  const [formData, setFormData] = useState({
    shortage_report_id: location.state?.shortage_report_id || '',
    from_project_id: '',
    from_location: '',
    to_project_id: location.state?.project_id || '',
    to_location: '',
    material_id: location.state?.material_id || '',
    transfer_qty: '',
    transfer_reason: '',
    urgent_level: 'NORMAL',
    remark: '',
  })
  const [errors, setErrors] = useState({})

  useEffect(() => {
    loadProjects()
    loadMaterials()
  }, [])

  const loadProjects = async () => {
    try {
      const res = await projectApi.list({ page: 1, page_size: 100 })
      setProjects(res.data.items || [])
    } catch (error) {
      console.error('加载项目列表失败', error)
    }
  }

  const loadMaterials = async () => {
    try {
      const res = await materialApi.list({ page: 1, page_size: 200, is_active: true })
      setMaterials(res.data.items || res.data || [])
    } catch (error) {
      console.error('加载物料列表失败', error)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    // 验证
    const newErrors = {}
    if (!formData.to_project_id) newErrors.to_project_id = '请选择调入项目'
    if (!formData.material_id) newErrors.material_id = '请选择物料'
    if (!formData.transfer_qty || parseFloat(formData.transfer_qty) <= 0) {
      newErrors.transfer_qty = '请输入有效的调拨数量'
    }
    if (!formData.transfer_reason.trim()) {
      newErrors.transfer_reason = '请输入调拨原因'
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors)
      return
    }

    setLoading(true)
    try {
      const submitData = {
        ...formData,
        shortage_report_id: formData.shortage_report_id ? parseInt(formData.shortage_report_id) : null,
        from_project_id: formData.from_project_id ? parseInt(formData.from_project_id) : null,
        to_project_id: parseInt(formData.to_project_id),
        material_id: parseInt(formData.material_id),
        transfer_qty: parseFloat(formData.transfer_qty),
      }
      
      const res = await shortageApi.transfers.create(submitData)
      alert('物料调拨申请创建成功！')
      navigate(`/shortage/transfers/${res.data.id}`)
    } catch (error) {
      console.error('创建物料调拨申请失败', error)
      alert('创建失败：' + (error.response?.data?.detail || error.message))
    } finally {
      setLoading(false)
    }
  }

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: null }))
    }
  }

  const filteredMaterials = materials.filter(m => 
    !searchKeyword || 
    m.material_code?.toLowerCase().includes(searchKeyword.toLowerCase()) ||
    m.material_name?.toLowerCase().includes(searchKeyword.toLowerCase())
  )

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={() => navigate('/shortage')}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          返回
        </Button>
        <PageHeader
          title="新建物料调拨申请"
          description="填写调拨信息并提交申请"
        />
      </div>

      <motion.form
        variants={fadeIn}
        initial="hidden"
        animate="visible"
        onSubmit={handleSubmit}
        className="max-w-4xl"
      >
        <Card>
          <CardHeader>
            <CardTitle>调拨信息</CardTitle>
            <CardDescription>选择调出和调入项目</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="from_project_id">调出项目（可选）</Label>
                <Select
                  value={formData.from_project_id}
                  onValueChange={(value) => handleChange('from_project_id', value)}
                >
                  <SelectTrigger id="from_project_id">
                    <SelectValue placeholder="留空表示从总库存调拨" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">总库存</SelectItem>
                    {projects.map((project) => (
                      <SelectItem key={project.id} value={String(project.id)}>
                        {project.project_name} ({project.project_code})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {formData.from_project_id && (
                  <Input
                    className="mt-2"
                    placeholder="调出位置（可选）"
                    value={formData.from_location}
                    onChange={(e) => handleChange('from_location', e.target.value)}
                  />
                )}
              </div>

              <div>
                <Label htmlFor="to_project_id" className="required">
                  调入项目 <span className="text-red-400">*</span>
                </Label>
                <Select
                  value={formData.to_project_id}
                  onValueChange={(value) => handleChange('to_project_id', value)}
                >
                  <SelectTrigger id="to_project_id" className={errors.to_project_id ? 'border-red-400' : ''}>
                    <SelectValue placeholder="请选择调入项目" />
                  </SelectTrigger>
                  <SelectContent>
                    {projects.map((project) => (
                      <SelectItem key={project.id} value={String(project.id)}>
                        {project.project_name} ({project.project_code})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {errors.to_project_id && (
                  <div className="text-sm text-red-400 mt-1">{errors.to_project_id}</div>
                )}
                <Input
                  className="mt-2"
                  placeholder="调入位置（可选）"
                  value={formData.to_location}
                  onChange={(e) => handleChange('to_location', e.target.value)}
                />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>物料信息</CardTitle>
            <CardDescription>选择调拨物料并填写数量</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="material_id" className="required">
                物料 <span className="text-red-400">*</span>
              </Label>
              <div className="space-y-2">
                <Input
                  placeholder="搜索物料编码或名称..."
                  value={searchKeyword}
                  onChange={(e) => setSearchKeyword(e.target.value)}
                  className="mb-2"
                />
                <Select
                  value={formData.material_id}
                  onValueChange={(value) => handleChange('material_id', value)}
                >
                  <SelectTrigger id="material_id" className={errors.material_id ? 'border-red-400' : ''}>
                    <SelectValue placeholder="请选择物料" />
                  </SelectTrigger>
                  <SelectContent>
                    {filteredMaterials.map((material) => (
                      <SelectItem key={material.id} value={String(material.id)}>
                        {material.material_code} - {material.material_name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {errors.material_id && (
                  <div className="text-sm text-red-400 mt-1">{errors.material_id}</div>
                )}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="transfer_qty" className="required">
                  调拨数量 <span className="text-red-400">*</span>
                </Label>
                <Input
                  id="transfer_qty"
                  type="number"
                  step="0.01"
                  min="0"
                  placeholder="0.00"
                  value={formData.transfer_qty}
                  onChange={(e) => handleChange('transfer_qty', e.target.value)}
                  className={errors.transfer_qty ? 'border-red-400' : ''}
                />
                {errors.transfer_qty && (
                  <div className="text-sm text-red-400 mt-1">{errors.transfer_qty}</div>
                )}
              </div>

              <div>
                <Label htmlFor="urgent_level">紧急程度</Label>
                <Select
                  value={formData.urgent_level}
                  onValueChange={(value) => handleChange('urgent_level', value)}
                >
                  <SelectTrigger id="urgent_level">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {urgentLevels.map((level) => (
                      <SelectItem key={level.value} value={level.value}>
                        {level.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>调拨原因</CardTitle>
            <CardDescription>说明调拨的原因和必要性</CardDescription>
          </CardHeader>
          <CardContent>
            <Textarea
              placeholder="请详细说明为什么需要调拨此物料..."
              value={formData.transfer_reason}
              onChange={(e) => handleChange('transfer_reason', e.target.value)}
              rows={4}
              className={errors.transfer_reason ? 'border-red-400' : ''}
            />
            {errors.transfer_reason && (
              <div className="text-sm text-red-400 mt-1">{errors.transfer_reason}</div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>备注</CardTitle>
          </CardHeader>
          <CardContent>
            <Textarea
              placeholder="其他需要说明的信息..."
              value={formData.remark}
              onChange={(e) => handleChange('remark', e.target.value)}
              rows={3}
            />
          </CardContent>
        </Card>

        <div className="flex items-center justify-end gap-4">
          <Button
            type="button"
            variant="outline"
            onClick={() => navigate('/shortage')}
            disabled={loading}
          >
            <X className="h-4 w-4 mr-2" />
            取消
          </Button>
          <Button type="submit" disabled={loading}>
            <Save className="h-4 w-4 mr-2" />
            {loading ? '提交中...' : '提交申请'}
          </Button>
        </div>
      </motion.form>
    </div>
  )
}



