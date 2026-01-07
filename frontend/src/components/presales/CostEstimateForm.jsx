/**
 * 成本估算表单组件
 * 售前技术工程师填写成本估算
 */
import React, { useState } from 'react'
import { motion } from 'framer-motion'
import {
  Calculator,
  DollarSign,
  FileText,
  X,
  Save,
  Send,
  AlertCircle,
  CheckCircle,
  TrendingUp,
  Package,
  Wrench,
  Zap,
  Code,
  Truck,
  Users,
} from 'lucide-react'
import { Button } from '../ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card'
import { Input } from '../ui/input'
import { Badge } from '../ui/badge'
import { cn } from '../../lib/utils'

// 成本分类配置
const costCategories = [
  { id: 'mechanical', name: '机械部分', icon: Wrench, color: 'text-blue-400', bgColor: 'bg-blue-500/10' },
  { id: 'electrical', name: '电气部分', icon: Zap, color: 'text-amber-400', bgColor: 'bg-amber-500/10' },
  { id: 'software', name: '软件部分', icon: Code, color: 'text-purple-400', bgColor: 'bg-purple-500/10' },
  { id: 'standard', name: '标准件/外购件', icon: Package, color: 'text-cyan-400', bgColor: 'bg-cyan-500/10' },
  { id: 'labor', name: '人工成本', icon: Users, color: 'text-emerald-400', bgColor: 'bg-emerald-500/10' },
  { id: 'other', name: '其他费用', icon: Truck, color: 'text-slate-400', bgColor: 'bg-slate-500/10' },
]

export default function CostEstimateForm({ bidding, onSave, onCancel }) {
  const [costs, setCosts] = useState({
    mechanical: { amount: 0, percentage: 0, notes: '' },
    electrical: { amount: 0, percentage: 0, notes: '' },
    software: { amount: 0, percentage: 0, notes: '' },
    standard: { amount: 0, percentage: 0, notes: '' },
    labor: { amount: 0, percentage: 0, notes: '' },
    other: { amount: 0, percentage: 0, notes: '' },
  })
  const [totalAmount, setTotalAmount] = useState(0)
  const [grossMargin, setGrossMargin] = useState(0)
  const [suggestedPrice, setSuggestedPrice] = useState(0)
  const [notes, setNotes] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  // 计算总金额和百分比
  const calculateTotals = (newCosts) => {
    const total = Object.values(newCosts).reduce((sum, item) => sum + (item.amount || 0), 0)
    setTotalAmount(total)
    
    // 更新百分比
    const updatedCosts = { ...newCosts }
    Object.keys(updatedCosts).forEach((key) => {
      updatedCosts[key].percentage = total > 0 ? ((updatedCosts[key].amount || 0) / total * 100).toFixed(1) : 0
    })
    setCosts(updatedCosts)

    // 计算毛利率（假设报价为成本的1.3倍）
    const margin = total > 0 ? ((total * 1.3 - total) / (total * 1.3) * 100).toFixed(1) : 0
    setGrossMargin(margin)
    setSuggestedPrice(total * 1.3)
  }

  // 更新成本项
  const updateCost = (category, field, value) => {
    const newCosts = { ...costs }
    if (field === 'amount') {
      newCosts[category].amount = parseFloat(value) || 0
    } else {
      newCosts[category][field] = value
    }
    setCosts(newCosts)
    calculateTotals(newCosts)
  }

  // 保存草稿
  const handleSaveDraft = async () => {
    setIsSubmitting(true)
    try {
      // 如果有投标ID，尝试更新投标记录或创建/更新方案
      if (bidding?.id) {
        // 尝试通过更新投标关联的方案来保存成本
        // 或者创建新的方案记录
        const costData = {
          estimated_cost: totalAmount * 10000, // 转换为元
          suggested_price: suggestedPrice * 10000,
          cost_breakdown: {
            mechanical: costs.mechanical.amount * 10000,
            electrical: costs.electrical.amount * 10000,
            software: costs.software.amount * 10000,
            standard: costs.standard.amount * 10000,
            labor: costs.labor.amount * 10000,
            other: costs.other.amount * 10000,
            notes: notes,
          },
        }
        
        // 这里可以调用API保存，暂时先调用onSave回调
        onSave?.({
          status: 'draft',
          costs,
          totalAmount,
          grossMargin,
          suggestedPrice,
          notes,
          submittedAt: new Date().toISOString(),
          costData,
        })
      } else {
        onSave?.({
          status: 'draft',
          costs,
          totalAmount,
          grossMargin,
          suggestedPrice,
          notes,
          submittedAt: new Date().toISOString(),
        })
      }
    } catch (err) {
      console.error('Failed to save cost estimate:', err)
      alert('保存失败：' + (err.response?.data?.detail || err.message))
    } finally {
      setIsSubmitting(false)
    }
  }

  // 提交成本估算
  const handleSubmit = async () => {
    if (totalAmount === 0) {
      alert('请先填写成本数据')
      return
    }

    setIsSubmitting(true)
    try {
      // 如果有投标ID，尝试更新投标记录或创建/更新方案
      if (bidding?.id) {
        const costData = {
          estimated_cost: totalAmount * 10000, // 转换为元
          suggested_price: suggestedPrice * 10000,
          cost_breakdown: {
            mechanical: costs.mechanical.amount * 10000,
            electrical: costs.electrical.amount * 10000,
            software: costs.software.amount * 10000,
            standard: costs.standard.amount * 10000,
            labor: costs.labor.amount * 10000,
            other: costs.other.amount * 10000,
            notes: notes,
          },
        }
        
        // 这里可以调用API保存，暂时先调用onSave回调
        onSave?.({
          status: 'submitted',
          costs,
          totalAmount,
          grossMargin,
          suggestedPrice,
          notes,
          submittedAt: new Date().toISOString(),
          costData,
        })
      } else {
        onSave?.({
          status: 'submitted',
          costs,
          totalAmount,
          grossMargin,
          suggestedPrice,
          notes,
          submittedAt: new Date().toISOString(),
        })
      }
    } catch (err) {
      console.error('Failed to submit cost estimate:', err)
      alert('提交失败：' + (err.response?.data?.detail || err.message))
      setIsSubmitting(false)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-4"
    >
      {/* 成本分类输入 */}
      <div className="space-y-3">
        {costCategories.map((category) => {
          const cost = costs[category.id]
          const Icon = category.icon
          return (
            <Card key={category.id} className="bg-surface-50/50 border border-white/5">
              <CardContent className="p-4">
                <div className="flex items-start gap-4">
                  <div className={cn('w-10 h-10 rounded-lg flex items-center justify-center', category.bgColor)}>
                    <Icon className={cn('w-5 h-5', category.color)} />
                  </div>
                  <div className="flex-1 space-y-3">
                    <div className="flex items-center justify-between">
                      <h4 className="text-sm font-medium text-white">{category.name}</h4>
                      {cost.percentage > 0 && (
                        <Badge variant="outline" className="text-xs">
                          {cost.percentage}%
                        </Badge>
                      )}
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="text-xs text-slate-400 mb-1 block">金额（万元）</label>
                        <Input
                          type="number"
                          value={cost.amount || ''}
                          onChange={(e) => updateCost(category.id, 'amount', e.target.value)}
                          placeholder="0.00"
                          className="bg-surface-100 border-white/10"
                        />
                      </div>
                      <div>
                        <label className="text-xs text-slate-400 mb-1 block">备注</label>
                        <Input
                          type="text"
                          value={cost.notes}
                          onChange={(e) => updateCost(category.id, 'notes', e.target.value)}
                          placeholder="说明..."
                          className="bg-surface-100 border-white/10"
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* 成本汇总 */}
      <Card className="bg-gradient-to-br from-violet-500/10 to-indigo-500/10 border border-violet-500/20">
        <CardContent className="p-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-xs text-slate-400 mb-1">总成本</p>
              <p className="text-2xl font-bold text-white">¥{totalAmount.toFixed(2)}万</p>
            </div>
            <div>
              <p className="text-xs text-slate-400 mb-1">建议报价</p>
              <p className="text-2xl font-bold text-emerald-400">¥{suggestedPrice.toFixed(2)}万</p>
            </div>
            <div>
              <p className="text-xs text-slate-400 mb-1">毛利率</p>
              <p className={cn(
                'text-xl font-semibold',
                grossMargin >= 30 ? 'text-emerald-400' :
                grossMargin >= 20 ? 'text-amber-400' : 'text-red-400'
              )}>
                {grossMargin}%
              </p>
            </div>
            <div>
              <p className="text-xs text-slate-400 mb-1">投标预算</p>
              <p className="text-lg font-medium text-white">¥{bidding?.amount || 0}万</p>
            </div>
          </div>
          {grossMargin < 20 && (
            <div className="mt-3 p-2 bg-red-500/10 border border-red-500/20 rounded-lg flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-red-400" />
              <p className="text-xs text-red-400">毛利率低于20%，建议重新评估成本或调整报价策略</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* 备注 */}
      <div>
        <label className="text-sm font-medium text-slate-400 mb-2 block">成本说明</label>
        <textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="成本估算说明、风险提示、特殊要求等..."
          className="w-full h-24 px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-sm text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-primary/50 resize-none"
        />
      </div>

      {/* 操作按钮 */}
      <div className="flex gap-2 pt-2">
        <Button
          variant="outline"
          onClick={onCancel}
          className="flex-1"
        >
          <X className="w-4 h-4 mr-2" />
          取消
        </Button>
        <Button
          variant="outline"
          onClick={handleSaveDraft}
          disabled={isSubmitting}
          className="flex-1"
        >
          <Save className="w-4 h-4 mr-2" />
          保存草稿
        </Button>
        <Button
          onClick={handleSubmit}
          disabled={isSubmitting || totalAmount === 0}
          className="flex-1"
        >
          <Send className="w-4 h-4 mr-2" />
          {isSubmitting ? '提交中...' : '提交成本估算'}
        </Button>
      </div>
    </motion.div>
  )
}

