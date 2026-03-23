/**
 * 沟通记录表单字段组件
 * 用于创建和编辑对话框中的表单
 */

import {
  COMMUNICATION_TYPE,
  COMMUNICATION_TYPE_LABELS,
  COMMUNICATION_PRIORITY,
  COMMUNICATION_PRIORITY_LABELS,
  COMMUNICATION_TOPIC,
  COMMUNICATION_TOPIC_LABELS,
  CUSTOMER_SATISFACTION,
  CUSTOMER_SATISFACTION_LABELS,
  getCommunicationTypeIcon,
} from "../../../components/customer-communication";

export default function CommunicationFormFields({ formData, setFormData, customers, users }) {
  return (
    <div className="grid grid-cols-2 gap-4">
      <div>
        <label className="text-sm font-medium text-gray-200">客户</label>
        <Select value={formData.customer_id} onValueChange={(v) => setFormData({ ...formData, customer_id: v })}>
          <SelectTrigger className="bg-slate-800 border-slate-600 text-white"><SelectValue placeholder="选择客户" /></SelectTrigger>
          <SelectContent className="bg-slate-800 border-slate-600">
            {(customers || []).map((c) => <SelectItem key={c.id} value={String(c.id)} className="text-white">{c.name}</SelectItem>)}
          </SelectContent>
        </Select>
      </div>
      <div>
        <label className="text-sm font-medium text-gray-200">沟通方式</label>
        <Select value={formData.communication_type} onValueChange={(v) => setFormData({ ...formData, communication_type: v })}>
          <SelectTrigger className="bg-slate-800 border-slate-600 text-white"><SelectValue placeholder="选择沟通方式" /></SelectTrigger>
          <SelectContent className="bg-slate-800 border-slate-600">
            {Object.entries(COMMUNICATION_TYPE).map(([_k, v]) => <SelectItem key={v} value={v} className="text-white">{getCommunicationTypeIcon(v)} {COMMUNICATION_TYPE_LABELS[v]}</SelectItem>)}
          </SelectContent>
        </Select>
      </div>
      <div>
        <label className="text-sm font-medium text-gray-200">主题</label>
        <Select value={formData.topic} onValueChange={(v) => setFormData({ ...formData, topic: v })}>
          <SelectTrigger className="bg-slate-800 border-slate-600 text-white"><SelectValue placeholder="选择主题" /></SelectTrigger>
          <SelectContent className="bg-slate-800 border-slate-600">
            {Object.entries(COMMUNICATION_TOPIC).map(([_k, v]) => <SelectItem key={v} value={v} className="text-white">{COMMUNICATION_TOPIC_LABELS[v]}</SelectItem>)}
          </SelectContent>
        </Select>
      </div>
      <div>
        <label className="text-sm font-medium text-gray-200">优先级</label>
        <Select value={formData.priority} onValueChange={(v) => setFormData({ ...formData, priority: v })}>
          <SelectTrigger className="bg-slate-800 border-slate-600 text-white"><SelectValue placeholder="选择优先级" /></SelectTrigger>
          <SelectContent className="bg-slate-800 border-slate-600">
            {Object.entries(COMMUNICATION_PRIORITY).map(([_k, v]) => <SelectItem key={v} value={v} className="text-white">{COMMUNICATION_PRIORITY_LABELS[v]}</SelectItem>)}
          </SelectContent>
        </Select>
      </div>
      <div className="col-span-2">
        <label className="text-sm font-medium text-gray-200">主题标题</label>
        <Input value={formData.subject} onChange={(e) => setFormData({ ...formData, subject: e.target.value })} placeholder="输入沟通主题" className="bg-slate-800 border-slate-600 text-white" />
      </div>
      <div className="col-span-2">
        <label className="text-sm font-medium text-gray-200">沟通内容</label>
        <Textarea value={formData.content} onChange={(e) => setFormData({ ...formData, content: e.target.value })} placeholder="详细描述沟通内容" rows={4} className="bg-slate-800 border-slate-600 text-white" />
      </div>
      <div>
        <label className="text-sm font-medium text-gray-200">沟通日期</label>
        <Input type="date" value={formData.communication_date} onChange={(e) => setFormData({ ...formData, communication_date: e.target.value })} className="bg-slate-800 border-slate-600 text-white" />
      </div>
      <div>
        <label className="text-sm font-medium text-gray-200">持续时间(分钟)</label>
        <Input type="number" value={formData.duration_minutes} onChange={(e) => setFormData({ ...formData, duration_minutes: e.target.value })} placeholder="分钟" className="bg-slate-800 border-slate-600 text-white" />
      </div>
      <div>
        <label className="text-sm font-medium text-gray-200">负责人</label>
        <Select value={formData.assigned_to} onValueChange={(v) => setFormData({ ...formData, assigned_to: v })}>
          <SelectTrigger className="bg-slate-800 border-slate-600 text-white"><SelectValue placeholder="选择负责人" /></SelectTrigger>
          <SelectContent className="bg-slate-800 border-slate-600">
            {(users || []).map((u) => <SelectItem key={u.id} value={String(u.id)} className="text-white">{u.name}</SelectItem>)}
          </SelectContent>
        </Select>
      </div>
      <div>
        <label className="text-sm font-medium text-gray-200">满意度评分</label>
        <Select value={formData.satisfaction_rating?.toString() || "__none__"} onValueChange={(v) => setFormData({ ...formData, satisfaction_rating: v === "__none__" ? null : parseInt(v) })}>
          <SelectTrigger className="bg-slate-800 border-slate-600 text-white"><SelectValue placeholder="选择满意度" /></SelectTrigger>
          <SelectContent className="bg-slate-800 border-slate-600">
            <SelectItem value="__none__" className="text-white">未评分</SelectItem>
            {Object.entries(CUSTOMER_SATISFACTION).map(([_k, v]) => <SelectItem key={v} value={v?.toString()} className="text-white">{CUSTOMER_SATISFACTION_LABELS[v]}</SelectItem>)}
          </SelectContent>
        </Select>
      </div>
      <div className="col-span-2">
        <label className="text-sm font-medium text-gray-200">客户反馈</label>
        <Textarea value={formData.customer_feedback} onChange={(e) => setFormData({ ...formData, customer_feedback: e.target.value })} placeholder="客户反馈内容" rows={3} className="bg-slate-800 border-slate-600 text-white" />
      </div>
      <div>
        <label className="text-sm font-medium text-gray-200">后续行动</label>
        <Input value={formData.next_action} onChange={(e) => setFormData({ ...formData, next_action: e.target.value })} placeholder="后续行动计划" className="bg-slate-800 border-slate-600 text-white" />
      </div>
      <div>
        <label className="text-sm font-medium text-gray-200">行动日期</label>
        <Input type="date" value={formData.next_action_date} onChange={(e) => setFormData({ ...formData, next_action_date: e.target.value })} className="bg-slate-800 border-slate-600 text-white" />
      </div>
      <div className="col-span-2">
        <label className="text-sm font-medium text-gray-200">备注</label>
        <Textarea value={formData.notes} onChange={(e) => setFormData({ ...formData, notes: e.target.value })} placeholder="备注信息" rows={2} className="bg-slate-800 border-slate-600 text-white" />
      </div>
    </div>
  );
}
