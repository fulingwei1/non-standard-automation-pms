/**
 * Customer Card Component - Displays customer information in a card format
 * Enhanced: higher info density, quick contact actions, value tags
 */

import { motion } from "framer-motion";
import { cn } from "../../lib/utils";
import {
  Building2,
  MapPin,
  Phone,
  Mail,
  Calendar,
  AlertTriangle,
  ChevronRight,
  MoreHorizontal,
  MessageSquare,
  DollarSign,
  TrendingUp,
  Star,
} from "lucide-react";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";

const gradeColors = {
  A: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
  B: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  C: "bg-amber-500/20 text-amber-400 border-amber-500/30",
  D: "bg-slate-500/20 text-slate-400 border-slate-500/30",
};

const statusConfig = {
  active: { label: "活跃", color: "bg-emerald-500", textColor: "text-emerald-400" },
  potential: { label: "潜在", color: "bg-blue-500", textColor: "text-blue-400" },
  dormant: { label: "沉睡", color: "bg-amber-500", textColor: "text-amber-400" },
  lost: { label: "流失", color: "bg-red-500", textColor: "text-red-400" },
};

const valueLevel = (amount) => {
  if (amount >= 5000000) return { label: "高价值", color: "bg-emerald-500/15 text-emerald-400 border-emerald-500/25" };
  if (amount >= 1000000) return { label: "中价值", color: "bg-blue-500/15 text-blue-400 border-blue-500/25" };
  return { label: "待开发", color: "bg-slate-500/15 text-slate-400 border-slate-500/25" };
};

const getContactUrgency = (lastContact) => {
  if (!lastContact) return { label: "从未联系", urgent: true };
  const days = Math.floor((Date.now() - new Date(lastContact).getTime()) / 86400000);
  if (days > 30) return { label: `${days}天未联系`, urgent: true };
  if (days > 14) return { label: `${days}天前`, urgent: false };
  return { label: `${days}天前`, urgent: false };
};

export default function CustomerCard({ customer, onClick, compact = false }) {
  const {
    name,
    shortName,
    grade = "B",
    status = "active",
    industry,
    location,
    contactPerson,
    phone,
    email,
    lastContact,
    totalAmount = 0,
    pendingAmount = 0,
    projectCount = 0,
    opportunityCount = 0,
    tags = [],
    isWarning = false,
  } = customer;

  const gradeClass = gradeColors[grade] || gradeColors.B;
  const statusConf = statusConfig[status] || statusConfig.active;
  const valLevel = valueLevel(totalAmount);
  const contactInfo = getContactUrgency(lastContact);

  if (compact) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2 }}
        onClick={() => onClick?.(customer)}
        className="flex items-center justify-between p-3 bg-surface-50 rounded-lg hover:bg-surface-100 cursor-pointer transition-colors group"
      >
        <div className="flex items-center gap-3">
          <div className={cn("w-2 h-2 rounded-full", statusConf.color)} />
          <div>
            <div className="flex items-center gap-2">
              <span className="font-medium text-white">
                {shortName || name}
              </span>
              <Badge variant="outline" className={cn("text-xs", gradeClass)}>
                {grade}级
              </Badge>
            </div>
            <span className="text-xs text-slate-400">{industry}</span>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {opportunityCount > 0 && (
            <Badge variant="secondary" className="text-xs">
              {opportunityCount}个商机
            </Badge>
          )}
          <ChevronRight className="w-4 h-4 text-slate-500 group-hover:text-white transition-colors" />
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      onClick={() => onClick?.(customer)}
      className={cn(
        "bg-surface-100/50 backdrop-blur-sm rounded-xl border border-white/5 p-4",
        "hover:border-primary/30 hover:shadow-lg hover:shadow-primary/5 cursor-pointer transition-all",
        isWarning && "border-amber-500/30",
      )}
    >
      {/* Header with status indicator */}
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-3 min-w-0 flex-1">
          <div className="relative flex-shrink-0">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center">
              <Building2 className="w-5 h-5 text-primary" />
            </div>
            <div className={cn("absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full border-2 border-surface-100", statusConf.color)} title={statusConf.label} />
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-1.5 flex-wrap">
              <h3 className="font-semibold text-white truncate">{shortName || name}</h3>
              <Badge variant="outline" className={cn("text-xs flex-shrink-0", gradeClass)}>
                {grade}级
              </Badge>
              {isWarning && <AlertTriangle className="w-3.5 h-3.5 text-amber-500 flex-shrink-0" />}
            </div>
            <div className="flex items-center gap-1.5 text-xs text-slate-500 mt-0.5">
              <span className="truncate">{industry || "未分类"}</span>
              {location && <>
                <span>·</span>
                <MapPin className="w-3 h-3 flex-shrink-0" />
                <span className="truncate">{location}</span>
              </>}
            </div>
          </div>
        </div>
        <Button variant="ghost" size="icon" className="h-7 w-7 flex-shrink-0" onClick={(e) => e.stopPropagation()}>
          <MoreHorizontal className="w-4 h-4 text-slate-400" />
        </Button>
      </div>

      {/* Value tag + status label */}
      <div className="flex items-center gap-1.5 mb-2">
        <Badge variant="outline" className={cn("text-xs", valLevel.color)}>
          <DollarSign className="w-3 h-3 mr-0.5" />
          {valLevel.label}
        </Badge>
        <Badge variant="outline" className={cn("text-xs", statusConf.textColor, "border-current/20")}>
          {statusConf.label}
        </Badge>
        {contactInfo.urgent && (
          <Badge variant="outline" className="text-xs text-amber-400 border-amber-500/25 bg-amber-500/10">
            {contactInfo.label}
          </Badge>
        )}
      </div>

      {/* Contact info with quick actions */}
      <div className="flex items-center justify-between mb-2 py-1.5 px-2 bg-surface-50/50 rounded-lg">
        <div className="flex items-center gap-2 text-xs text-slate-300 min-w-0">
          <span className="font-medium truncate">{contactPerson || "未设置联系人"}</span>
        </div>
        <div className="flex items-center gap-1 flex-shrink-0">
          {phone && (
            <Button
              variant="ghost" size="icon" className="h-6 w-6"
              title={`拨打 ${phone}`}
              onClick={(e) => { e.stopPropagation(); window.open(`tel:${phone}`); }}
            >
              <Phone className="w-3 h-3 text-blue-400" />
            </Button>
          )}
          {email && (
            <Button
              variant="ghost" size="icon" className="h-6 w-6"
              title={`发送邮件 ${email}`}
              onClick={(e) => { e.stopPropagation(); window.open(`mailto:${email}`); }}
            >
              <Mail className="w-3 h-3 text-emerald-400" />
            </Button>
          )}
          <Button
            variant="ghost" size="icon" className="h-6 w-6"
            title="记录沟通"
            onClick={(e) => { e.stopPropagation(); onClick?.(customer); }}
          >
            <MessageSquare className="w-3 h-3 text-purple-400" />
          </Button>
        </div>
      </div>

      {/* Tags */}
      {tags?.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-2">
          {tags.slice(0, 3).map((tag, index) => (
            <Badge key={index} variant="secondary" className="text-xs py-0">
              {tag}
            </Badge>
          ))}
          {tags?.length > 3 && (
            <Badge variant="secondary" className="text-xs py-0">
              +{tags?.length - 3}
            </Badge>
          )}
        </div>
      )}

      {/* Stats - 4-column with more density */}
      <div className="grid grid-cols-4 gap-1.5 pt-2 border-t border-white/5">
        <div className="text-center">
          <div className="text-xs text-slate-500">累计</div>
          <div className="text-sm font-semibold text-white">
            {totalAmount >= 10000 ? `${(totalAmount / 10000).toFixed(0)}万` : `${totalAmount}`}
          </div>
        </div>
        <div className="text-center">
          <div className="text-xs text-slate-500">待回款</div>
          <div className={cn("text-sm font-semibold", pendingAmount > 0 ? "text-amber-400" : "text-slate-600")}>
            {pendingAmount >= 10000 ? `${(pendingAmount / 10000).toFixed(0)}万` : `${pendingAmount}`}
          </div>
        </div>
        <div className="text-center">
          <div className="text-xs text-slate-500">项目</div>
          <div className="text-sm font-semibold text-white">{projectCount}</div>
        </div>
        <div className="text-center">
          <div className="text-xs text-slate-500">商机</div>
          <div className={cn("text-sm font-semibold", opportunityCount > 0 ? "text-blue-400" : "text-slate-600")}>
            {opportunityCount}
          </div>
        </div>
      </div>

      {/* Footer - last contact */}
      <div className="flex items-center justify-between mt-2 pt-2 border-t border-white/5">
        <div className="flex items-center gap-1 text-xs text-slate-400">
          <Calendar className="w-3 h-3" />
          <span>最近联系: {contactInfo.label}</span>
        </div>
        {grade === "A" && (
          <Star className="w-3.5 h-3.5 text-amber-400 fill-amber-400" />
        )}
      </div>
    </motion.div>
  );
}
