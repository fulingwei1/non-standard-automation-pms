import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Bell, BellOff, Moon, Sun, Save } from 'lucide-react'
import { PageHeader } from '../components/layout'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Badge } from '../components/ui/badge'
import { Input } from '../components/ui/input'
import { fadeIn } from '../lib/animations'

const alertTypes = [
  { value: 'PROJ_DELAY', label: '项目进度延期预警' },
  { value: 'PO_DELIVERY', label: '采购交期预警' },
  { value: 'COST_OVERRUN', label: '成本超支预警' },
  { value: 'OS_DELIVERY', label: '外协交期预警' },
  { value: 'QA_INSPECTION', label: '检验不合格预警' },
]

const alertLevels = [
  { value: 'INFO', label: '提示' },
  { value: 'WARNING', label: '注意' },
  { value: 'CRITICAL', label: '严重' },
  { value: 'URGENT', label: '紧急' },
]

export default function AlertSubscription() {
  const [subscriptions, setSubscriptions] = useState([])
  const [quietStart, setQuietStart] = useState('22:00')
  const [quietEnd, setQuietEnd] = useState('08:00')

  useEffect(() => {
    loadSubscriptions()
  }, [])

  const loadSubscriptions = async () => {
    try {
      // Mock data for now
      setSubscriptions([
        { id: 1, alert_type: 'PROJ_DELAY', min_level: 'WARNING', is_active: true },
        { id: 2, alert_type: 'PO_DELIVERY', min_level: 'CRITICAL', is_active: true },
      ])
    } catch (error) {
    }
  }

  const handleToggle = (id) => {
    setSubscriptions((prev) =>
      prev.map((sub) =>
        sub.id === id ? { ...sub, is_active: !sub.is_active } : sub
      )
    )
  }

  const handleSave = async () => {
    try {
      // API call: alertApi.saveSubscriptions(subscriptions)
      // For now, save to localStorage as fallback
      localStorage.setItem('alertSubscriptions', JSON.stringify(subscriptions))
      alert('订阅配置已保存')
    } catch (error) {
      alert('保存失败，请稍后重试')
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <PageHeader
        title="预警订阅配置"
        actions={
          <Button onClick={handleSave} className="gap-2">
            <Save className="w-4 h-4" />
            保存配置
          </Button>
        }
      />

      <div className="container mx-auto px-4 py-6 space-y-6">
        {/* Quiet Hours */}
        <motion.div variants={fadeIn} initial="hidden" animate="visible">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Moon className="w-5 h-5" />
                免打扰时段
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-4">
                <div>
                  <label className="text-sm text-slate-400 mb-1 block">开始时间</label>
                  <Input
                    type="time"
                    value={quietStart}
                    onChange={(e) => setQuietStart(e.target.value)}
                    className="bg-slate-800/50 border-slate-700"
                  />
                </div>
                <span className="text-slate-400 mt-6">至</span>
                <div>
                  <label className="text-sm text-slate-400 mb-1 block">结束时间</label>
                  <Input
                    type="time"
                    value={quietEnd}
                    onChange={(e) => setQuietEnd(e.target.value)}
                    className="bg-slate-800/50 border-slate-700"
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Subscriptions */}
        <motion.div variants={fadeIn} initial="hidden" animate="visible">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Bell className="w-5 h-5" />
                订阅规则
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {alertTypes.map((type) => {
                  const subscription = subscriptions.find((s) => s.alert_type === type.value)
                  return (
                    <div
                      key={type.value}
                      className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg"
                    >
                      <div className="flex items-center gap-3">
                        {subscription?.is_active ? (
                          <Bell className="w-5 h-5 text-emerald-400" />
                        ) : (
                          <BellOff className="w-5 h-5 text-slate-500" />
                        )}
                        <div>
                          <p className="text-white font-medium">{type.label}</p>
                          {subscription && (
                            <p className="text-xs text-slate-500">
                              最低接收级别: {alertLevels.find((l) => l.value === subscription.min_level)?.label || subscription.min_level}
                            </p>
                          )}
                        </div>
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleToggle(subscription?.id || 0)}
                      >
                        {subscription?.is_active ? '已订阅' : '未订阅'}
                      </Button>
                    </div>
                  )
                })}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  )
}

