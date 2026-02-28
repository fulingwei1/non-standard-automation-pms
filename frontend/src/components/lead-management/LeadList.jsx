import { motion } from "framer-motion";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
} from "../../components/ui";
import {
  User,
  Phone,
  MapPin,
  Eye,
  Edit,
  ArrowRight,
  Star,
  Building2,
  Calendar,
  Clock,
} from "lucide-react";
import { cn } from "../../lib/utils";
import { formatDate, formatDateTime } from "../../lib/formatters";
import { fadeIn } from "../../lib/animations";
import { sourceOptions } from "@/lib/constants/leadManagement";


// 获取来源标签
const getSourceLabel = (sourceValue) => {
  const source = sourceOptions.find((s) => s.value === sourceValue);
  return source ? source.label : sourceValue || "-";
};

export default function LeadList({
  loading,
  leads,
  viewMode,
  statusConfig,
  handleViewDetail,
  handleEdit,
  handleConvert,
}) {
  if (loading) {
    return <div className="text-center py-12 text-slate-400">加载中...</div>;
  }

  if (leads.length === 0) {
    return (
      <Card>
        <CardContent className="p-12 text-center">
          <p className="text-slate-400">暂无线索数据</p>
        </CardContent>
      </Card>
    );
  }

  if (viewMode === "grid") {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {leads.map((lead) => (
          <motion.div
            key={lead.id}
            variants={fadeIn}
            whileHover={{ y: -4 }}
            className="cursor-pointer"
          >
            <Card className="h-full hover:border-blue-500 transition-colors">
              <CardHeader className="pb-2">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <CardTitle className="text-lg">
                      {lead.customer_name}
                    </CardTitle>
                    <p className="text-xs text-slate-500 mt-1">
                      {lead.lead_code}
                    </p>
                  </div>
                  <div className="flex items-center gap-1.5">
                    {lead.is_key_lead && (
                      <Star className="h-4 w-4 text-yellow-500 fill-yellow-500" />
                    )}
                    <Badge className={cn(statusConfig[lead.status]?.color, "text-xs")}>
                      {statusConfig[lead.status]?.label}
                    </Badge>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="pt-2">
                <div className="space-y-1.5 text-sm">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 text-slate-300">
                      <User className="h-3.5 w-3.5 text-slate-500" />
                      <span>{lead.contact_name || "-"}</span>
                    </div>
                    {lead.priority_score != null && (
                      <Badge variant="outline" className="text-xs px-1.5 py-0">
                        {lead.priority_score}分
                      </Badge>
                    )}
                  </div>
                  {lead.contact_phone && (
                    <div className="flex items-center gap-2 text-slate-400">
                      <Phone className="h-3.5 w-3.5 text-slate-500" />
                      <span>{lead.contact_phone}</span>
                    </div>
                  )}
                  <div className="flex items-center gap-4 text-slate-400">
                    {lead.industry && (
                      <div className="flex items-center gap-1.5">
                        <Building2 className="h-3.5 w-3.5 text-slate-500" />
                        <span>{lead.industry}</span>
                      </div>
                    )}
                    {lead.source && (
                      <div className="flex items-center gap-1.5">
                        <MapPin className="h-3.5 w-3.5 text-slate-500" />
                        <span>{getSourceLabel(lead.source)}</span>
                      </div>
                    )}
                  </div>
                  {lead.owner_name && (
                    <div className="flex items-center gap-2 text-slate-400">
                      <User className="h-3.5 w-3.5 text-blue-500" />
                      <span className="text-blue-400">{lead.owner_name}</span>
                    </div>
                  )}
                  {lead.demand_summary && (
                    <p className="text-slate-500 line-clamp-2 mt-2 text-xs">
                      {lead.demand_summary}
                    </p>
                  )}
                  <div className="flex items-center gap-4 text-xs text-slate-500 pt-1">
                    <div className="flex items-center gap-1">
                      <Calendar className="h-3 w-3" />
                      <span>{formatDate(lead.created_at)}</span>
                    </div>
                    {lead.next_action_at && (
                      <div className="flex items-center gap-1 text-amber-400">
                        <Clock className="h-3 w-3" />
                        <span>跟进: {formatDate(lead.next_action_at)}</span>
                      </div>
                    )}
                  </div>
                </div>
                <div className="flex gap-2 mt-3 pt-3 border-t border-slate-800">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleViewDetail(lead)}
                    className="flex-1 h-8"
                  >
                    <Eye className="mr-1.5 h-3.5 w-3.5" />
                    详情
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleEdit(lead)}
                    className="flex-1 h-8"
                  >
                    <Edit className="mr-1.5 h-3.5 w-3.5" />
                    编辑
                  </Button>
                  {lead.status !== "CONVERTED" && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleConvert(lead)}
                      className="flex-1 h-8 text-emerald-400 hover:text-emerald-300"
                    >
                      <ArrowRight className="mr-1.5 h-3.5 w-3.5" />
                      转商机
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>
    );
  }

  return (
    <Card>
      <CardContent className="p-0">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-800">
                <th className="text-left p-4 text-slate-400 text-sm">客户名称</th>
                <th className="text-left p-4 text-slate-400 text-sm">联系人</th>
                <th className="text-left p-4 text-slate-400 text-sm">行业</th>
                <th className="text-left p-4 text-slate-400 text-sm">来源</th>
                <th className="text-left p-4 text-slate-400 text-sm">负责人</th>
                <th className="text-left p-4 text-slate-400 text-sm">优先级</th>
                <th className="text-left p-4 text-slate-400 text-sm">状态</th>
                <th className="text-left p-4 text-slate-400 text-sm">创建时间</th>
                <th className="text-left p-4 text-slate-400 text-sm">操作</th>
              </tr>
            </thead>
            <tbody>
              {leads.map((lead) => (
                <tr
                  key={lead.id}
                  className="border-b border-slate-800 hover:bg-slate-800/50"
                >
                  <td className="p-4">
                    <div>
                      <div className="text-white font-medium">{lead.customer_name}</div>
                      <div className="text-xs text-slate-500">{lead.lead_code}</div>
                    </div>
                  </td>
                  <td className="p-4">
                    <div className="text-slate-300">{lead.contact_name || "-"}</div>
                    {lead.contact_phone && (
                      <div className="text-xs text-slate-500">{lead.contact_phone}</div>
                    )}
                  </td>
                  <td className="p-4 text-slate-300">{lead.industry || "-"}</td>
                  <td className="p-4 text-slate-300">{getSourceLabel(lead.source)}</td>
                  <td className="p-4 text-blue-400">{lead.owner_name || "-"}</td>
                  <td className="p-4">
                    <div className="flex items-center gap-2">
                      {lead.is_key_lead && (
                        <Star className="h-4 w-4 text-yellow-500 fill-yellow-500" />
                      )}
                      {lead.priority_score != null ? (
                        <Badge variant="outline" className="text-xs">
                          {lead.priority_score}分
                        </Badge>
                      ) : (
                        <span className="text-slate-500 text-xs">-</span>
                      )}
                    </div>
                  </td>
                  <td className="p-4">
                    <Badge className={cn(statusConfig[lead.status]?.color, "text-xs")}>
                      {statusConfig[lead.status]?.label}
                    </Badge>
                  </td>
                  <td className="p-4 text-slate-400 text-sm">
                    {formatDateTime(lead.created_at)}
                  </td>
                  <td className="p-4">
                    <div className="flex gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleViewDetail(lead)}
                        className="h-8 w-8 p-0"
                      >
                        <Eye className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleEdit(lead)}
                        className="h-8 w-8 p-0"
                      >
                        <Edit className="h-4 w-4" />
                      </Button>
                      {lead.status !== "CONVERTED" && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleConvert(lead)}
                          className="h-8 w-8 p-0 text-emerald-400"
                        >
                          <ArrowRight className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}
