/**
 * ECNLogsTab Component
 * ECN 变更日志 Tab 组件（时间线视图）
 */
import { useState, useMemo } from 'react'
import { Card, CardContent } from '../ui/card'
import { Input } from '../ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../ui/select'
import { Badge } from '../ui/badge'
import { History } from 'lucide-react'
import { formatDate } from '../../lib/utils'

export default function ECNLogsTab({ logs }) {
  const [logSearchKeyword, setLogSearchKeyword] = useState('')
  const [logFilterType, setLogFilterType] = useState('all')

  // 筛选日志
  const filteredLogs = useMemo(() => {
    let filtered = [...logs]

    // 按类型筛选
    if (logFilterType !== 'all') {
      filtered = filtered.filter((log) => log.log_type === logFilterType)
    }

    // 按关键词搜索
    if (logSearchKeyword) {
      const keyword = logSearchKeyword.toLowerCase()
      filtered = filtered.filter(
        (log) =>
          log.log_action?.toLowerCase().includes(keyword) ||
          log.log_content?.toLowerCase().includes(keyword) ||
          log.created_by_name?.toLowerCase().includes(keyword)
      )
    }

    // 按时间倒序
    return filtered.sort(
      (a, b) => new Date(b.created_at) - new Date(a.created_at)
    )
  }, [logs, logFilterType, logSearchKeyword])

  return (
    <div className="space-y-4">
      {/* 日志筛选 */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <Input
                placeholder="搜索日志内容..."
                value={logSearchKeyword}
                onChange={(e) => setLogSearchKeyword(e.target.value)}
                className="max-w-sm"
              />
            </div>
            <Select value={logFilterType} onValueChange={setLogFilterType}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="日志类型" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部类型</SelectItem>
                <SelectItem value="STATUS_CHANGE">状态变更</SelectItem>
                <SelectItem value="APPROVAL">审批</SelectItem>
                <SelectItem value="EVALUATION">评估</SelectItem>
                <SelectItem value="OPERATION">操作</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* 日志列表 */}
      {filteredLogs.length === 0 ? (
        <Card>
          <CardContent className="py-8 text-center text-slate-400">
            {logs.length === 0 ? '暂无变更日志' : '没有匹配的日志'}
          </CardContent>
        </Card>
      ) : (
        <div className="relative">
          {/* 时间线 */}
          <div className="absolute left-5 top-0 bottom-0 w-0.5 bg-slate-200" />

          <div className="space-y-4">
            {filteredLogs.map((log) => (
              <div key={log.id} className="relative flex items-start gap-4">
                {/* 时间线节点 */}
                <div className="relative z-10">
                  <div className="w-10 h-10 rounded-full bg-blue-500 flex items-center justify-center text-white shadow-lg">
                    <History className="w-5 h-5" />
                  </div>
                </div>

                {/* 日志卡片 */}
                <Card className="flex-1 shadow-sm">
                  <CardContent className="pt-4">
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <div className="font-semibold">{log.log_action}</div>
                        <div className="text-sm text-slate-500">
                          {log.created_by_name || `用户${log.created_by || ''}`} ·{' '}
                          {formatDate(log.created_at)}
                        </div>
                      </div>
                      <Badge className="bg-slate-500">{log.log_type}</Badge>
                    </div>
                    {log.old_status && log.new_status && (
                      <div className="text-sm text-slate-600 mb-2">
                        状态变更:{' '}
                        <span className="font-mono">{log.old_status}</span> →{' '}
                        <span className="font-mono">{log.new_status}</span>
                      </div>
                    )}
                    {log.log_content && (
                      <div className="p-2 bg-slate-50 rounded text-sm">
                        {log.log_content}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
