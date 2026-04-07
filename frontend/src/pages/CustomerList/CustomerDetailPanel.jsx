import {
  Building2,
  Phone,
  Mail,
  MessageSquare,
} from "lucide-react"
import { cn } from "../../lib/utils"
import { gradeColors, statusConfig } from "./constants"

// Interaction Timeline Component
function InteractionTimeline({ customerId: _customerId }) {
  const timelineItems = [
    { type: "call", label: "电话沟通", desc: "讨论Q2项目需求", date: "3天前", icon: Phone, color: "text-blue-400" },
    { type: "visit", label: "客户拜访", desc: "现场技术交流", date: "1周前", icon: Building2, color: "text-emerald-400" },
    { type: "email", label: "邮件往来", desc: "发送报价方案V2", date: "2周前", icon: Mail, color: "text-purple-400" },
    { type: "meeting", label: "线上会议", desc: "需求评审会", date: "3周前", icon: MessageSquare, color: "text-amber-400" },
  ];

  return (
    <div className="relative">
      <div className="absolute left-[11px] top-2 bottom-2 w-px bg-white/10" />
      <div className="space-y-3">
        {timelineItems.map((item, idx) => {
          const Icon = item.icon;
          return (
            <div key={idx} className="flex items-start gap-3 relative">
              <div className="w-6 h-6 rounded-full bg-surface-50 border border-white/10 flex items-center justify-center z-10 flex-shrink-0">
                <Icon className={cn("w-3 h-3", item.color)} />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-white font-medium">{item.label}</span>
                  <span className="text-xs text-slate-500">{item.date}</span>
                </div>
                <p className="text-xs text-slate-400 mt-0.5">{item.desc}</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// Customer Detail Side Panel
export function CustomerDetailPanel({ customer, onClose }) {
  const statusConf = statusConfig[customer.status] || statusConfig.active;

  return (
    <motion.div
      initial={{ x: "100%" }}
      animate={{ x: 0 }}
      exit={{ x: "100%" }}
      transition={{ type: "spring", damping: 25, stiffness: 200 }}
      className="fixed right-0 top-0 h-full w-full md:w-[450px] bg-surface-100/95 backdrop-blur-xl border-l border-white/5 shadow-2xl z-50 flex flex-col"
    >
      {/* Header */}
      <div className="p-4 border-b border-white/5">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center">
              <Building2 className="w-6 h-6 text-primary" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-semibold text-white">
                  {customer.shortName}
                </h2>
                <Badge
                  variant="outline"
                  className={gradeColors[customer.grade] || gradeColors.B}
                >
                  {customer.grade}级
                </Badge>
              </div>
              <p className="text-sm text-slate-400">{customer.name}</p>
            </div>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <ChevronRight className="w-5 h-5" />
          </Button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {/* Quick Stats */}
        <div className="grid grid-cols-3 gap-3">
          <div className="text-center p-3 bg-surface-50 rounded-lg">
            <div className="text-lg font-semibold text-white">
              ¥{(customer.totalAmount / 10000).toFixed(0)}万
            </div>
            <div className="text-xs text-slate-400">累计金额</div>
          </div>
          <div className="text-center p-3 bg-surface-50 rounded-lg">
            <div className="text-lg font-semibold text-amber-400">
              ¥{(customer.pendingAmount / 10000).toFixed(0)}万
            </div>
            <div className="text-xs text-slate-400">待回款</div>
          </div>
          <div className="text-center p-3 bg-surface-50 rounded-lg">
            <div className="text-lg font-semibold text-white">
              {customer.projectCount}
            </div>
            <div className="text-xs text-slate-400">项目数</div>
          </div>
        </div>

        {/* Basic Info */}
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-slate-400">基本信息</h3>
          <div className="space-y-2">
            <div className="flex items-center gap-3 text-sm">
              <MapPin className="w-4 h-4 text-slate-500" />
              <span className="text-slate-400">地址:</span>
              <span className="text-white">{customer.location}</span>
            </div>
            <div className="flex items-center gap-3 text-sm">
              <Tag className="w-4 h-4 text-slate-500" />
              <span className="text-slate-400">行业:</span>
              <span className="text-white">{customer.industry}</span>
            </div>
            <div className="flex items-center gap-3 text-sm">
              <div className={cn("w-2 h-2 rounded-full", statusConf.color)} />
              <span className="text-slate-400">状态:</span>
              <span className={statusConf.textColor}>{statusConf.label}</span>
            </div>
          </div>
        </div>

        {/* Contact Info */}
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-slate-400">联系方式</h3>
          <div className="space-y-2">
            <div className="flex items-center gap-3 text-sm">
              <UserPlus className="w-4 h-4 text-slate-500" />
              <span className="text-slate-400">联系人:</span>
              <span className="text-white">{customer.contactPerson}</span>
            </div>
            <div className="flex items-center gap-3 text-sm">
              <Phone className="w-4 h-4 text-slate-500" />
              <span className="text-slate-400">电话:</span>
              <span className="text-white">{customer.phone}</span>
            </div>
            <div className="flex items-center gap-3 text-sm">
              <Mail className="w-4 h-4 text-slate-500" />
              <span className="text-slate-400">邮箱:</span>
              <span className="text-white">{customer.email}</span>
            </div>
            <div className="flex items-center gap-3 text-sm">
              <History className="w-4 h-4 text-slate-500" />
              <span className="text-slate-400">最近联系:</span>
              <span className="text-white">{customer.lastContact}</span>
            </div>
          </div>
        </div>

        {/* Tags */}
        {customer.tags?.length > 0 && (
          <div className="space-y-3">
            <h3 className="text-sm font-medium text-slate-400">标签</h3>
            <div className="flex flex-wrap gap-2">
              {(customer.tags || []).map((tag, index) => (
                <Badge key={index} variant="secondary">
                  {tag}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Quick Actions */}
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-slate-400">快捷操作</h3>
          <div className="grid grid-cols-2 gap-2">
            <Button variant="outline" size="sm" className="justify-start">
              <Target className="w-4 h-4 mr-2 text-blue-400" />
              新建商机
            </Button>
            <Button variant="outline" size="sm" className="justify-start">
              <MessageSquare className="w-4 h-4 mr-2 text-green-400" />
              添加跟进
            </Button>
            <Button variant="outline" size="sm" className="justify-start">
              <Calendar className="w-4 h-4 mr-2 text-purple-400" />
              安排拜访
            </Button>
            <Button variant="outline" size="sm" className="justify-start">
              <DollarSign className="w-4 h-4 mr-2 text-amber-400" />
              查看回款
            </Button>
          </div>
        </div>

        {/* Interaction Timeline */}
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-slate-400">交互历史</h3>
          <InteractionTimeline customerId={customer.id} />
        </div>
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-white/5 flex gap-2">
        <Button variant="outline" className="flex-1" onClick={onClose}>
          关闭
        </Button>
        <Button className="flex-1">
          <Edit className="w-4 h-4 mr-2" />
          编辑客户
        </Button>
      </div>
    </motion.div>
  );
}
