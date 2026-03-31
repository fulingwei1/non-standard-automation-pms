/**
 * Shared form fields used by both Create and Edit dialogs
 */
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue } from
"../../components/ui/select";
import { Input } from "../../components/ui/input";
import { Textarea } from "../../components/ui/textarea";
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
} from "../../components/customer-communication";

export default function CommunicationFormFields({ formData, setFormData, customers, users }) {
  return (
    <div className="grid grid-cols-2 gap-4">
      <div>
        <label className="text-sm font-medium text-gray-200">客户</label>
        <Select
          value={formData.customer_id}
          onValueChange={(value) =>
          setFormData({ ...formData, customer_id: value })
          }>

          <SelectTrigger className="bg-slate-800 border-slate-600 text-white">
            <SelectValue placeholder="选择客户" />
          </SelectTrigger>
          <SelectContent className="bg-slate-800 border-slate-600">
            {(customers || []).map((customer) =>
            <SelectItem key={customer.id} value={customer.id} className="text-white">
                {customer.name}
            </SelectItem>
            )}
          </SelectContent>
        </Select>
      </div>

      <div>
        <label className="text-sm font-medium text-gray-200">沟通方式</label>
        <Select
          value={formData.communication_type}
          onValueChange={(value) =>
          setFormData({ ...formData, communication_type: value })
          }>

          <SelectTrigger className="bg-slate-800 border-slate-600 text-white">
            <SelectValue placeholder="选择沟通方式" />
          </SelectTrigger>
          <SelectContent className="bg-slate-800 border-slate-600">
            {Object.entries(COMMUNICATION_TYPE).map(([_key, value]) =>
            <SelectItem key={value} value={value || "unknown"} className="text-white">
                {getCommunicationTypeIcon(value)} {COMMUNICATION_TYPE_LABELS[value]}
            </SelectItem>
            )}
          </SelectContent>
        </Select>
      </div>

      <div>
        <label className="text-sm font-medium text-gray-200">主题</label>
        <Select
          value={formData.topic}
          onValueChange={(value) =>
          setFormData({ ...formData, topic: value })
          }>

          <SelectTrigger className="bg-slate-800 border-slate-600 text-white">
            <SelectValue placeholder="选择主题" />
          </SelectTrigger>
          <SelectContent className="bg-slate-800 border-slate-600">
            {Object.entries(COMMUNICATION_TOPIC).map(([_key, value]) =>
            <SelectItem key={value} value={value || "unknown"} className="text-white">
                {COMMUNICATION_TOPIC_LABELS[value]}
            </SelectItem>
            )}
          </SelectContent>
        </Select>
      </div>

      <div>
        <label className="text-sm font-medium text-gray-200">优先级</label>
        <Select
          value={formData.priority}
          onValueChange={(value) =>
          setFormData({ ...formData, priority: value })
          }>

          <SelectTrigger className="bg-slate-800 border-slate-600 text-white">
            <SelectValue placeholder="选择优先级" />
          </SelectTrigger>
          <SelectContent className="bg-slate-800 border-slate-600">
            {Object.entries(COMMUNICATION_PRIORITY).map(([_key, value]) =>
            <SelectItem key={value} value={value || "unknown"} className="text-white">
                {COMMUNICATION_PRIORITY_LABELS[value]}
            </SelectItem>
            )}
          </SelectContent>
        </Select>
      </div>

      <div className="col-span-2">
        <label className="text-sm font-medium text-gray-200">主题标题</label>
        <Input
          value={formData.subject}
          onChange={(e) =>
          setFormData({ ...formData, subject: e.target.value })
          }
          placeholder="输入沟通主题"
          className="bg-slate-800 border-slate-600 text-white" />

      </div>

      <div className="col-span-2">
        <label className="text-sm font-medium text-gray-200">沟通内容</label>
        <Textarea
          value={formData.content}
          onChange={(e) =>
          setFormData({ ...formData, content: e.target.value })
          }
          placeholder="详细描述沟通内容"
          rows={4}
          className="bg-slate-800 border-slate-600 text-white" />

      </div>

      <div>
        <label className="text-sm font-medium text-gray-200">沟通日期</label>
        <Input
          type="date"
          value={formData.communication_date}
          onChange={(e) =>
          setFormData({ ...formData, communication_date: e.target.value })
          }
          className="bg-slate-800 border-slate-600 text-white" />

      </div>

      <div>
        <label className="text-sm font-medium text-gray-200">持续时间(分钟)</label>
        <Input
          type="number"
          value={formData.duration_minutes}
          onChange={(e) =>
          setFormData({ ...formData, duration_minutes: e.target.value })
          }
          placeholder="分钟"
          className="bg-slate-800 border-slate-600 text-white" />

      </div>

      <div>
        <label className="text-sm font-medium text-gray-200">负责人</label>
        <Select
          value={formData.assigned_to}
          onValueChange={(value) =>
          setFormData({ ...formData, assigned_to: value })
          }>

          <SelectTrigger className="bg-slate-800 border-slate-600 text-white">
            <SelectValue placeholder="选择负责人" />
          </SelectTrigger>
          <SelectContent className="bg-slate-800 border-slate-600">
            {(users || []).map((user) =>
            <SelectItem key={user.id} value={user.id} className="text-white">
                {user.name}
            </SelectItem>
            )}
          </SelectContent>
        </Select>
      </div>

      <div>
        <label className="text-sm font-medium text-gray-200">满意度评分</label>
        <Select
          value={formData.satisfaction_rating?.toString() || ""}
          onValueChange={(value) =>
          setFormData({
            ...formData,
            satisfaction_rating: value ? parseInt(value) : null
          })
          }>

          <SelectTrigger className="bg-slate-800 border-slate-600 text-white">
            <SelectValue placeholder="选择满意度" />
          </SelectTrigger>
          <SelectContent className="bg-slate-800 border-slate-600">
            <SelectItem value="__none__" className="text-white">未评分</SelectItem>
            {Object.entries(CUSTOMER_SATISFACTION).map(([_key, value]) =>
            <SelectItem key={value} value={value?.toString() || "unknown"} className="text-white">
                {CUSTOMER_SATISFACTION_LABELS[value]}
            </SelectItem>
            )}
          </SelectContent>
        </Select>
      </div>

      <div className="col-span-2">
        <label className="text-sm font-medium text-gray-200">客户反馈</label>
        <Textarea
          value={formData.customer_feedback}
          onChange={(e) =>
          setFormData({ ...formData, customer_feedback: e.target.value })
          }
          placeholder="客户反馈内容"
          rows={3}
          className="bg-slate-800 border-slate-600 text-white" />

      </div>

      <div>
        <label className="text-sm font-medium text-gray-200">后续行动</label>
        <Input
          value={formData.next_action}
          onChange={(e) =>
          setFormData({ ...formData, next_action: e.target.value })
          }
          placeholder="后续行动计划"
          className="bg-slate-800 border-slate-600 text-white" />

      </div>

      <div>
        <label className="text-sm font-medium text-gray-200">行动日期</label>
        <Input
          type="date"
          value={formData.next_action_date}
          onChange={(e) =>
          setFormData({ ...formData, next_action_date: e.target.value })
          }
          className="bg-slate-800 border-slate-600 text-white" />

      </div>

      <div className="col-span-2">
        <label className="text-sm font-medium text-gray-200">备注</label>
        <Textarea
          value={formData.notes}
          onChange={(e) =>
          setFormData({ ...formData, notes: e.target.value })
          }
          placeholder="备注信息"
          rows={2}
          className="bg-slate-800 border-slate-600 text-white" />

      </div>
    </div>
  );
}
