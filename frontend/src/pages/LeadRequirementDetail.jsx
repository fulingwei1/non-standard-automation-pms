/**
 * Lead Requirement Detail Page - 线索需求详情页面
 * 结构化表单编辑需求信息
 */

import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Save, FileText, CheckCircle2, Lock, ExternalLink } from 'lucide-react'
import { PageHeader } from '../components/layout'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Input,
  Label,
  Textarea,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '../components/ui'
import { leadApi, technicalAssessmentApi } from '../services/api'

export default function LeadRequirementDetail() {
  const { leadId } = useParams()
  const navigate = useNavigate()
  
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [requirementDetail, setRequirementDetail] = useState(null)
  const [requirementData, setRequirementData] = useState({
    customer_factory_location: '',
    target_object_type: '',
    application_scenario: '',
    delivery_mode: '',
    expected_delivery_date: '',
    requirement_source: '',
    requirement_maturity: 3,
    has_sow: false,
    has_interface_doc: false,
    has_drawing_doc: false,
    cycle_time_seconds: '',
    workstation_count: '',
    acceptance_method: '',
    acceptance_basis: '',
  })

  useEffect(() => {
    loadRequirement()
  }, [leadId])

  const loadRequirement = async () => {
    try {
      setLoading(true)
      const response = await technicalAssessmentApi.getRequirementDetail(parseInt(leadId))
      if (response.data) {
        setRequirementDetail(response.data)
        setRequirementData({
          customer_factory_location: response.data.customer_factory_location || '',
          target_object_type: response.data.target_object_type || '',
          application_scenario: response.data.application_scenario || '',
          delivery_mode: response.data.delivery_mode || '',
          expected_delivery_date: response.data.expected_delivery_date || '',
          requirement_source: response.data.requirement_source || '',
          requirement_maturity: response.data.requirement_maturity || 3,
          has_sow: response.data.has_sow || false,
          has_interface_doc: response.data.has_interface_doc || false,
          has_drawing_doc: response.data.has_drawing_doc || false,
          cycle_time_seconds: response.data.cycle_time_seconds || '',
          workstation_count: response.data.workstation_count || '',
          acceptance_method: response.data.acceptance_method || '',
          acceptance_basis: response.data.acceptance_basis || '',
        })
      }
    } catch (error) {
      if (error.response?.status === 404) {
        // 需求详情不存在，使用默认值
      } else {
      }
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    try {
      setSaving(true)
      try {
        // 先尝试更新
        await technicalAssessmentApi.updateRequirementDetail(parseInt(leadId), requirementData)
      } catch (error) {
        if (error.response?.status === 404) {
          // 不存在则创建
          await technicalAssessmentApi.createRequirementDetail(parseInt(leadId), requirementData)
        } else {
          throw error
        }
      }
      alert('需求详情已保存')
      await loadRequirement() // 重新加载
    } catch (error) {
      alert('保存失败: ' + (error.response?.data?.detail || error.message))
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return <div className="p-6">加载中...</div>
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      <PageHeader
        title="需求详情"
        breadcrumbs={[
          { label: '销售管理', path: '/sales' },
          { label: '线索管理', path: '/sales/leads' },
          { label: '需求详情', path: '' },
        ]}
      />

      <div className="mt-6">
        <Card className="bg-gray-800 border-gray-700">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>需求信息</CardTitle>
              <div className="flex gap-2">
                {requirementDetail?.is_frozen && (
                  <Badge className="bg-orange-500">
                    <Lock className="w-3 h-3 mr-1" />
                    已冻结 {requirementDetail.requirement_version}
                  </Badge>
                )}
                <Button 
                  onClick={() => navigate(`/sales/lead/${leadId}/requirement-freezes`)} 
                  variant="outline"
                  className="border-blue-500 text-blue-400 hover:bg-blue-500/10"
                >
                  <Lock className="w-4 h-4 mr-2" />
                  冻结管理
                </Button>
                <Button onClick={() => navigate(-1)} variant="outline">
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  返回
                </Button>
                <Button 
                  onClick={handleSave} 
                  disabled={saving || requirementDetail?.is_frozen} 
                  className="bg-blue-600 hover:bg-blue-700"
                  title={requirementDetail?.is_frozen ? '需求已冻结，无法修改' : ''}
                >
                  <Save className="w-4 h-4 mr-2" />
                  {saving ? '保存中...' : '保存'}
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="basic" className="w-full">
              <TabsList className="grid w-full grid-cols-4">
                <TabsTrigger value="basic">基础信息</TabsTrigger>
                <TabsTrigger value="capacity">产能节拍</TabsTrigger>
                <TabsTrigger value="acceptance">验收标准</TabsTrigger>
                <TabsTrigger value="interface">接口I/O</TabsTrigger>
              </TabsList>
              
              <TabsContent value="basic" className="mt-4 space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>客户工厂/地点</Label>
                    <Input
                      value={requirementData.customer_factory_location}
                      onChange={(e) => setRequirementData({...requirementData, customer_factory_location: e.target.value})}
                      placeholder="请输入客户工厂/地点"
                    />
                  </div>
                  <div>
                    <Label>被测对象类型</Label>
                    <Input
                      value={requirementData.target_object_type}
                      onChange={(e) => setRequirementData({...requirementData, target_object_type: e.target.value})}
                      placeholder="BMS/电机/动力电池等"
                    />
                  </div>
                  <div>
                    <Label>应用场景</Label>
                    <Input
                      value={requirementData.application_scenario}
                      onChange={(e) => setRequirementData({...requirementData, application_scenario: e.target.value})}
                      placeholder="量产/实验室/售后维修等"
                    />
                  </div>
                  <div>
                    <Label>计划交付模式</Label>
                    <Input
                      value={requirementData.delivery_mode}
                      onChange={(e) => setRequirementData({...requirementData, delivery_mode: e.target.value})}
                      placeholder="整机/线体/工位分段交付"
                    />
                  </div>
                </div>
                
                <div className="space-y-2">
                  <Label>需求成熟度 (1-5级)</Label>
                  <Input
                    type="number"
                    min="1"
                    max="5"
                    value={requirementData.requirement_maturity}
                    onChange={(e) => setRequirementData({...requirementData, requirement_maturity: parseInt(e.target.value)})}
                  />
                </div>
                
                <div className="space-y-2">
                  <Label>文档完整性</Label>
                  <div className="flex gap-4">
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={requirementData.has_sow}
                        onChange={(e) => setRequirementData({...requirementData, has_sow: e.target.checked})}
                      />
                      <span>有SOW/URS</span>
                    </label>
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={requirementData.has_interface_doc}
                        onChange={(e) => setRequirementData({...requirementData, has_interface_doc: e.target.checked})}
                      />
                      <span>有接口协议文档</span>
                    </label>
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={requirementData.has_drawing_doc}
                        onChange={(e) => setRequirementData({...requirementData, has_drawing_doc: e.target.checked})}
                      />
                      <span>有图纸/原理/IO清单</span>
                    </label>
                  </div>
                </div>
              </TabsContent>
              
              <TabsContent value="capacity" className="mt-4 space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>节拍要求 (秒)</Label>
                    <Input
                      type="number"
                      value={requirementData.cycle_time_seconds}
                      onChange={(e) => setRequirementData({...requirementData, cycle_time_seconds: e.target.value})}
                      placeholder="请输入节拍时间"
                    />
                  </div>
                  <div>
                    <Label>工位数/并行数</Label>
                    <Input
                      type="number"
                      value={requirementData.workstation_count}
                      onChange={(e) => setRequirementData({...requirementData, workstation_count: e.target.value})}
                      placeholder="请输入工位数"
                    />
                  </div>
                </div>
              </TabsContent>
              
              <TabsContent value="acceptance" className="mt-4 space-y-4">
                <div>
                  <Label>验收方式</Label>
                  <Input
                    value={requirementData.acceptance_method}
                    onChange={(e) => setRequirementData({...requirementData, acceptance_method: e.target.value})}
                    placeholder="FAT/SAT/阶段验收"
                  />
                </div>
                <div>
                  <Label>验收依据</Label>
                  <Textarea
                    value={requirementData.acceptance_basis}
                    onChange={(e) => setRequirementData({...requirementData, acceptance_basis: e.target.value})}
                    placeholder="客户标准/企业标准/国标/双方确认的测试用例"
                    rows={4}
                  />
                </div>
              </TabsContent>
              
              <TabsContent value="interface" className="mt-4 space-y-4">
                <div>
                  <Label>接口类型</Label>
                  <Textarea
                    placeholder="被测对象接口类型（JSON Array）"
                    rows={3}
                  />
                </div>
                <div>
                  <Label>通讯协议</Label>
                  <Textarea
                    placeholder="通讯协议（JSON Array）"
                    rows={3}
                  />
                </div>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

