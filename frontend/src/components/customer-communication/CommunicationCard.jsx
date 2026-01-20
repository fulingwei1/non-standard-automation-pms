/**
 * Customer Communication Card Component
 * 客户沟通卡片组件
 */
import React, { useState } from "react";
import { format } from 'date-fns';
import { zhCN } from 'date-fns/locale';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ChevronDown, ChevronRight, MessageSquare, Phone,
  Mail, Calendar, Clock, AlertCircle, CheckCircle,
  EllipsisVertical, Send, Copy, Download, MoreHorizontal } from
"lucide-react";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "../ui/avatar";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import {
  Popover,
  PopoverContent,
  PopoverTrigger } from
"../ui/popover";
import { Edit, Delete } from "lucide-react";
import { cn } from "../../lib/utils";
import {
  statusConfigs as _statusConfigs,
  typeConfigs as _typeConfigs,
  priorityConfigs as _priorityConfigs,
  channelConfigs as _channelConfigs,
  getStatusConfig,
  getTypeConfig,
  getPriorityConfig,
  getChannelConfig,
  formatStatus,
  formatType,
  formatPriority,
  formatChannel } from
"./communicationConstants";

const fadeIn = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.3 } }
};

const slideDown = {
  hidden: { opacity: 0, height: 0 },
  visible: { opacity: 1, height: "auto", transition: { duration: 0.3 } },
  exit: { opacity: 0, height: 0, transition: { duration: 0.2 } }
};

/**
 * 沟通详情卡片
 */
const CommunicationDetailCard = ({ communication }) => {
  if (!communication) {return null;}

  const config = getStatusConfig(communication.status);
  const typeConfig = getTypeConfig(communication.communication_type);
  const priorityConfig = getPriorityConfig(communication.priority);
  const channelConfig = getChannelConfig(communication.channel);

  return (
    <motion.div
      variants={fadeIn}
      initial="hidden"
      animate="visible"
      className="space-y-4">

      {/* 基本信息卡片 */}
      <Card className="border-l-4" style={{ borderLeftColor: config.color.replace('bg-', '#').replace('-500', '') }}>
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between">
            <div className="flex items-start gap-3">
              <Avatar className="w-10 h-10">
                <AvatarImage src={communication.avatar_url} alt={communication.contact_name} />
                <AvatarFallback>
                  {communication.contact_name?.charAt(0) || "客"}
                </AvatarFallback>
              </Avatar>
              <div className="min-w-0 flex-1">
                <CardTitle className="text-lg flex items-center gap-2">
                  {communication.title}
                  <Badge
                    variant="secondary"
                    className={cn(typeConfig.color, typeConfig.textColor || "text-white")}>

                    {typeConfig.icon} {formatType(communication.communication_type)}
                  </Badge>
                </CardTitle>
                <div className="flex items-center gap-4 mt-1 text-sm text-slate-500">
                  <span className="flex items-center gap-1">
                    {channelConfig.icon} {formatChannel(communication.channel)}
                  </span>
                  <span className="flex items-center gap-1">
                    <Clock className="w-4 h-4" />
                    {format(new Date(communication.created_at || communication.createdAt), 'yyyy-MM-dd HH:mm', { locale: zhCN })}
                  </span>
                </div>
              </div>
            </div>
            <Badge
              variant="outline"
              className={cn(
                config.color.replace('bg-', 'border-'),
                config.color.replace('bg-', 'text-'),
                "border-2"
              )}>

              {formatStatus(communication.status)}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <div className="text-sm text-slate-500">联系人</div>
              <div className="font-medium">{communication.contact_name}</div>
            </div>
            <div>
              <div className="text-sm text-slate-500">联系方式</div>
              <div className="font-medium">
                {communication.contact_email || communication.contact_phone || "未设置"}
              </div>
            </div>
            <div>
              <div className="text-sm text-slate-500">公司</div>
              <div>{communication.contact_company || "-"}</div>
            </div>
            <div>
              <div className="text-sm text-slate-500">优先级</div>
              <div className="flex items-center gap-2">
                {priorityConfig.icon}
                <Badge
                  variant="secondary"
                  className={cn(priorityConfig.color, priorityConfig.textColor || "text-white")}>

                  {formatPriority(communication.priority)}
                </Badge>
              </div>
            </div>
          </div>

          {communication.content &&
          <div className="mb-4">
              <div className="text-sm text-slate-500 mb-1">沟通内容</div>
              <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded text-sm whitespace-pre-wrap">
                {communication.content}
              </div>
          </div>
          }
        </CardContent>
      </Card>

      {/* 沟通记录时间线 */}
      {communication.communication_records && communication.communication_records.length > 0 &&
      <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">沟通记录</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {communication.communication_records.map((record, index) =>
            <div key={index} className="flex gap-3">
                  <div className="flex flex-col items-center">
                    <div className="w-2 h-2 bg-blue-500 rounded-full" />
                    {index < communication.communication_records.length - 1 &&
                <div className="w-0.5 h-16 bg-slate-200 dark:bg-slate-700 mt-2" />
                }
                  </div>
                  <div className="flex-1 pb-4">
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="font-medium">{record.action}</div>
                        <div className="text-sm text-slate-500">
                          {format(new Date(record.created_at), 'yyyy-MM-dd HH:mm', { locale: zhCN })}
                        </div>
                      </div>
                      {record.result &&
                  <div className="text-sm text-slate-500">结果: {record.result}</div>
                  }
                    </div>
                    {record.notes &&
                <div className="mt-1 text-sm text-slate-600 dark:text-slate-400">
                        备注: {record.notes}
                </div>
                }
                  </div>
            </div>
            )}
            </div>
          </CardContent>
      </Card>
      }

      {/* 附件信息 */}
      {communication.attachments && communication.attachments.length > 0 &&
      <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">附件 ({communication.attachments.length})</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {communication.attachments.map((attachment, index) =>
            <div key={index} className="flex items-center justify-between p-2 bg-slate-50 dark:bg-slate-800 rounded">
                  <div className="flex items-center gap-2">
                    <FileText className="w-4 h-4 text-slate-500" />
                    <span className="text-sm">{attachment.filename}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-slate-500">
                      {(attachment.file_size / 1024 / 1024).toFixed(2)} MB
                    </span>
                    <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                      <Download className="w-3 h-3" />
                    </Button>
                  </div>
            </div>
            )}
            </div>
          </CardContent>
      </Card>
      }
    </motion.div>);

};

/**
 * 客户沟通卡片组件
 */
export const CommunicationCard = ({
  communication,
  onSelect: _onSelect,
  onEdit,
  onDelete,
  onResend,
  className,
  expanded = false,
  onToggleExpand
}) => {
  const [showActions, setShowActions] = useState(false);

  const config = getStatusConfig(communication.status);
  const typeConfig = getTypeConfig(communication.communication_type);
  const priorityConfig = getPriorityConfig(communication.priority);
  const channelConfig = getChannelConfig(communication.channel);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onToggleExpand?.();
    }
  };

  return (
    <motion.div
      variants={fadeIn}
      initial="hidden"
      animate="visible"
      className={cn("border rounded-lg overflow-hidden", className)}>

      {/* 卡片主体 */}
      <div
        className="cursor-pointer"
        onClick={() => onToggleExpand?.()}
        onKeyDown={handleKeyDown}
        tabIndex={0}
        role="button"
        aria-expanded={expanded}>

        <Card className="hover:shadow-md transition-shadow">
          <CardHeader className="pb-3">
            <div className="flex items-start justify-between">
              <div className="flex items-start gap-3">
                <Avatar className="w-10 h-10">
                  <AvatarImage src={communication.avatar_url} alt={communication.contact_name} />
                  <AvatarFallback>
                    {communication.contact_name?.charAt(0) || "客"}
                  </AvatarFallback>
                </Avatar>
                <div className="min-w-0 flex-1">
                  <CardTitle className="text-lg flex items-center gap-2">
                    {communication.title}
                    <Badge
                      variant="secondary"
                      className={cn(typeConfig.color, typeConfig.textColor || "text-white")}>

                      {typeConfig.icon} {formatType(communication.communication_type)}
                    </Badge>
                    <Badge
                      variant="outline"
                      className={cn(
                        config.color.replace('bg-', 'border-'),
                        config.color.replace('bg-', 'text-'),
                        "border-2"
                      )}>

                      {formatStatus(communication.status)}
                    </Badge>
                  </CardTitle>
                  <div className="flex items-center gap-4 mt-1 text-sm text-slate-500">
                    <span className="flex items-center gap-1">
                      {channelConfig.icon} {formatChannel(communication.channel)}
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock className="w-4 h-4" />
                      {format(new Date(communication.created_at || communication.createdAt), 'yyyy-MM-dd HH:mm', { locale: zhCN })}
                    </span>
                    <span className="flex items-center gap-1">
                      {priorityConfig.icon}
                      {formatPriority(communication.priority)}
                    </span>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {onToggleExpand &&
                <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                    {expanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                </Button>
                }
                <Popover open={showActions} onOpenChange={setShowActions}>
                  <PopoverTrigger asChild>
                    <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                      <MoreHorizontal className="w-4 h-4" />
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent align="end" className="w-48">
                    <div className="flex flex-col gap-1">
                      {onEdit &&
                      <Button
                        variant="ghost"
                        className="w-full justify-start"
                        onClick={() => {
                          onEdit(communication);
                          setShowActions(false);
                        }}>

                          <Edit className="w-4 h-4 mr-2" />
                          编辑
                      </Button>
                      }
                      {onResend && communication.status === "FAILED" &&
                      <Button
                        variant="ghost"
                        className="w-full justify-start"
                        onClick={() => {
                          onResend(communication);
                          setShowActions(false);
                        }}>

                          <Send className="w-4 h-4 mr-2" />
                          重新发送
                      </Button>
                      }
                      <Button
                        variant="ghost"
                        className="w-full justify-start"
                        onClick={() => {
                          navigator.clipboard.writeText(communication.content);
                          setShowActions(false);
                        }}>

                        <Copy className="w-4 h-4 mr-2" />
                        复制内容
                      </Button>
                      {onDelete &&
                      <Button
                        variant="ghost"
                        className="w-full justify-start text-red-500"
                        onClick={() => {
                          onDelete(communication);
                          setShowActions(false);
                        }}>

                          <Delete className="w-4 h-4 mr-2" />
                          删除
                      </Button>
                      }
                    </div>
                  </PopoverContent>
                </Popover>
              </div>
            </div>
          </CardHeader>
        </Card>
      </div>

      {/* 展开的详情内容 */}
      <AnimatePresence>
        {expanded &&
        <motion.div
          variants={slideDown}
          initial="hidden"
          animate="visible"
          exit="exit">

            <CommunicationDetailCard communication={communication} />
        </motion.div>
        }
      </AnimatePresence>
    </motion.div>);

};

export default CommunicationCard;