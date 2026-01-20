import React from "react";
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
} from "lucide-react";
import { cn } from "../../lib/utils";
import { fadeIn } from "../../lib/animations";

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
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <CardTitle className="text-lg">
                      {lead.lead_code}
                    </CardTitle>
                    <p className="text-sm text-slate-400 mt-1">
                      {lead.customer_name}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    {lead.is_key_lead && (
                      <Star className="h-4 w-4 text-yellow-500 fill-yellow-500" />
                    )}
                    <Badge className={cn(statusConfig[lead.status]?.color)}>
                      {statusConfig[lead.status]?.label}
                    </Badge>
                    {lead.priority_score !== null &&
                      lead.priority_score !== undefined && (
                        <Badge variant="outline" className="text-xs">
                          {lead.priority_score}分
                        </Badge>
                      )}
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 text-sm">
                  {lead.contact_name && (
                    <div className="flex items-center gap-2 text-slate-300">
                      <User className="h-4 w-4 text-slate-400" />
                      {lead.contact_name}
                    </div>
                  )}
                  {lead.contact_phone && (
                    <div className="flex items-center gap-2 text-slate-300">
                      <Phone className="h-4 w-4 text-slate-400" />
                      {lead.contact_phone}
                    </div>
                  )}
                  {lead.source && (
                    <div className="flex items-center gap-2 text-slate-300">
                      <MapPin className="h-4 w-4 text-slate-400" />
                      来源: {lead.source}
                    </div>
                  )}
                  {lead.demand_summary && (
                    <p className="text-slate-400 line-clamp-2 mt-2">
                      {lead.demand_summary}
                    </p>
                  )}
                </div>
                <div className="flex gap-2 mt-4">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleViewDetail(lead)}
                    className="flex-1"
                  >
                    <Eye className="mr-2 h-4 w-4" />
                    详情
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleEdit(lead)}
                    className="flex-1"
                  >
                    <Edit className="mr-2 h-4 w-4" />
                    编辑
                  </Button>
                  {lead.status !== "CONVERTED" && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleConvert(lead)}
                      className="flex-1"
                    >
                      <ArrowRight className="mr-2 h-4 w-4" />
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
                <th className="text-left p-4 text-slate-400">线索编码</th>
                <th className="text-left p-4 text-slate-400">客户名称</th>
                <th className="text-left p-4 text-slate-400">联系人</th>
                <th className="text-left p-4 text-slate-400">联系电话</th>
                <th className="text-left p-4 text-slate-400">来源</th>
                <th className="text-left p-4 text-slate-400">优先级</th>
                <th className="text-left p-4 text-slate-400">状态</th>
                <th className="text-left p-4 text-slate-400">操作</th>
              </tr>
            </thead>
            <tbody>
              {leads.map((lead) => (
                <tr
                  key={lead.id}
                  className="border-b border-slate-800 hover:bg-slate-800/50"
                >
                  <td className="p-4 text-white">{lead.lead_code}</td>
                  <td className="p-4 text-slate-300">{lead.customer_name}</td>
                  <td className="p-4 text-slate-300">
                    {lead.contact_name || "-"}
                  </td>
                  <td className="p-4 text-slate-300">
                    {lead.contact_phone || "-"}
                  </td>
                  <td className="p-4 text-slate-300">{lead.source || "-"}</td>
                  <td className="p-4">
                    <div className="flex items-center gap-2">
                      {lead.is_key_lead && (
                        <Star className="h-4 w-4 text-yellow-500 fill-yellow-500" />
                      )}
                      {lead.priority_score !== null &&
                      lead.priority_score !== undefined ? (
                        <Badge variant="outline" className="text-xs">
                          {lead.priority_score}分
                        </Badge>
                      ) : (
                        <span className="text-slate-400 text-xs">-</span>
                      )}
                    </div>
                  </td>
                  <td className="p-4">
                    <Badge className={cn(statusConfig[lead.status]?.color)}>
                      {statusConfig[lead.status]?.label}
                    </Badge>
                  </td>
                  <td className="p-4">
                    <div className="flex gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleViewDetail(lead)}
                      >
                        <Eye className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleEdit(lead)}
                      >
                        <Edit className="h-4 w-4" />
                      </Button>
                      {lead.status !== "CONVERTED" && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleConvert(lead)}
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
