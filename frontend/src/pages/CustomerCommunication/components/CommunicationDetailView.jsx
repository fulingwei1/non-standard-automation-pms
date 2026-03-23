/**
 * 沟通记录详情展示组件
 */

import { formatDate } from "../../../lib/utils";
import { COMMUNICATION_TOPIC_LABELS } from "../../../components/customer-communication";

export default function CommunicationDetailView({
  communication,
  getTypeDisplay,
  getPriorityBadge,
  getStatusBadge,
  getSatisfactionDisplay,
}) {
  return (
    <div className="space-y-4 text-white">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="text-sm font-medium text-gray-400">客户</label>
          <p className="mt-1 text-sm">{communication.customer?.name || communication.customer_name || "-"}</p>
        </div>
        <div>
          <label className="text-sm font-medium text-gray-400">沟通方式</label>
          <p className="mt-1 text-sm">{getTypeDisplay(communication.communication_type)}</p>
        </div>
        <div>
          <label className="text-sm font-medium text-gray-400">主题</label>
          <p className="mt-1 text-sm">{COMMUNICATION_TOPIC_LABELS[communication.topic]}</p>
        </div>
        <div>
          <label className="text-sm font-medium text-gray-400">优先级</label>
          <div className="mt-1">{getPriorityBadge(communication.priority)}</div>
        </div>
        <div>
          <label className="text-sm font-medium text-gray-400">状态</label>
          <div className="mt-1">{getStatusBadge(communication.status)}</div>
        </div>
        <div>
          <label className="text-sm font-medium text-gray-400">满意度</label>
          <div className="mt-1">{getSatisfactionDisplay(communication.satisfaction_rating)}</div>
        </div>
        <div>
          <label className="text-sm font-medium text-gray-400">沟通日期</label>
          <p className="mt-1 text-sm">{formatDate(communication.communication_date)}</p>
        </div>
        <div>
          <label className="text-sm font-medium text-gray-400">持续时间</label>
          <p className="mt-1 text-sm">{communication.duration_minutes} 分钟</p>
        </div>
        <div>
          <label className="text-sm font-medium text-gray-400">负责人</label>
          <p className="mt-1 text-sm">{communication.assigned_user?.name || "未分配"}</p>
        </div>
      </div>
      <div>
        <label className="text-sm font-medium text-gray-400">主题标题</label>
        <p className="mt-1 text-sm font-medium">{communication.subject}</p>
      </div>
      <div>
        <label className="text-sm font-medium text-gray-400">沟通内容</label>
        <p className="mt-1 text-sm whitespace-pre-wrap bg-slate-800 p-3 rounded">{communication.content}</p>
      </div>
      {communication.customer_feedback && (
        <div>
          <label className="text-sm font-medium text-gray-400">客户反馈</label>
          <p className="mt-1 text-sm whitespace-pre-wrap bg-slate-800 p-3 rounded">{communication.customer_feedback}</p>
        </div>
      )}
      {communication.next_action && (
        <div>
          <label className="text-sm font-medium text-gray-400">后续行动</label>
          <p className="mt-1 text-sm">{communication.next_action}</p>
        </div>
      )}
      {communication.next_action_date && (
        <div>
          <label className="text-sm font-medium text-gray-400">行动日期</label>
          <p className="mt-1 text-sm">{formatDate(communication.next_action_date)}</p>
        </div>
      )}
      {communication.notes && (
        <div>
          <label className="text-sm font-medium text-gray-400">备注</label>
          <p className="mt-1 text-sm whitespace-pre-wrap bg-slate-800 p-3 rounded">{communication.notes}</p>
        </div>
      )}
    </div>
  );
}
