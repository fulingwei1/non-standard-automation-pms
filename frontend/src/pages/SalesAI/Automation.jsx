/**
 * 销售自动化页面
 * 
 * 功能：
 * 1. 自动跟进提醒
 * 2. 自动邮件序列
 * 3. 自动任务规则
 * 4. 自动报告
 */

import { useState } from "react";
import { motion } from "framer-motion";
import {
  Zap,
  Bell,
  Mail,
  CheckSquare,
  FileText,
  Play,
  Pause,
  Settings,
  Clock,
  AlertCircle,
  CheckCircle,
  ChevronRight,
} from "lucide-react";
import { PageHeader } from "../../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
  Button,
  Badge,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  Switch,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../../components/ui";

// 跟进提醒
function FollowUpReminders() {
  const [reminders, _setReminders] = useState([
    {
      customer_id: 1,
      customer_name: "宁德时代",
      days_since_contact: 14,
      priority: "HIGH",
      reason: "商机STAGE4价格谈判阶段，7天未联系",
      suggested_action: "电话跟进价格反馈",
    },
    {
      customer_id: 2,
      customer_name: "比亚迪",
      days_since_contact: 9,
      priority: "MEDIUM",
      reason: "方案已发送，待客户确认",
      suggested_action: "邮件询问方案反馈",
    },
  ]);

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <div className="text-sm text-slate-400">
          今天有 <span className="text-white font-bold">{reminders.length}</span> 个客户需要跟进
        </div>
        <Button size="sm">
          <Bell className="w-4 h-4 mr-2" />
          发送提醒
        </Button>
      </div>

      <div className="grid gap-4">
        {reminders.map((reminder, idx) => (
          <Card
            key={idx}
            className={
              reminder.priority === "HIGH"
                ? "border-red-500 bg-red-500/5"
                : reminder.priority === "MEDIUM"
                ? "border-orange-500 bg-orange-500/5"
                : ""
            }
          >
            <CardContent className="pt-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div
                    className={`w-2 h-2 rounded-full ${
                      reminder.priority === "HIGH"
                        ? "bg-red-500"
                        : reminder.priority === "MEDIUM"
                        ? "bg-orange-500"
                        : "bg-green-500"
                    }`}
                  />
                  <div>
                    <div className="font-medium">{reminder.customer_name}</div>
                    <div className="text-sm text-slate-400">{reminder.reason}</div>
                  </div>
                </div>
                <Badge
                  variant={reminder.priority === "HIGH" ? "destructive" : "secondary"}
                >
                  {reminder.days_since_contact}天未联系
                </Badge>
              </div>
              <div className="mt-3 flex items-center justify-between">
                <div className="text-sm text-slate-300">
                  <ChevronRight className="w-4 h-4 inline mr-1" />
                  建议行动: {reminder.suggested_action}
                </div>
                <Button size="sm" variant="outline">标记完成</Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

// 自动任务规则
function AutomationRules() {
  const [rules, setRules] = useState([
    {
      id: 1,
      name: "商机阶段变更-方案演示",
      trigger: "商机进入STAGE3",
      action: "创建方案演示任务",
      is_active: true,
    },
    {
      id: 2,
      name: "报价审批通过-合同准备",
      trigger: "报价状态=已批准",
      action: "创建合同准备任务",
      is_active: true,
    },
    {
      id: 3,
      name: "客户7天未联系-跟进提醒",
      trigger: "7天无交互记录",
      action: "创建跟进任务",
      is_active: true,
    },
    {
      id: 4,
      name: "合同签订-项目启动",
      trigger: "合同已签署",
      action: "创建项目启动会任务",
      is_active: false,
    },
  ]);

  const toggleRule = (id) => {
    setRules(rules.map(r => r.id === id ? {...r, is_active: !r.is_active} : r));
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <div className="text-sm text-slate-400">
          已启用 <span className="text-green-500 font-bold">{rules.filter(r => r.is_active).length}</span> 条规则
        </div>
        <Button size="sm">
          <Settings className="w-4 h-4 mr-2" />
          新建规则
        </Button>
      </div>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>规则名称</TableHead>
            <TableHead>触发条件</TableHead>
            <TableHead>执行动作</TableHead>
            <TableHead>状态</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {rules.map((rule) => (
            <TableRow key={rule.id}>
              <TableCell className="font-medium">{rule.name}</TableCell>
              <TableCell>{rule.trigger}</TableCell>
              <TableCell>{rule.action}</TableCell>
              <TableCell>
                <Switch
                  checked={rule.is_active}
                  onCheckedChange={() => toggleRule(rule.id)}
                />
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

// 自动报告
function AutoReports() {
  const [schedules, _setSchedules] = useState([
    { id: 1, report_type: "日报", frequency: "每天", time: "18:00", is_active: true },
    { id: 2, report_type: "周报", frequency: "每周一", time: "09:00", is_active: true },
    { id: 3, report_type: "月报", frequency: "每月1日", time: "09:00", is_active: true },
  ]);

  return (
    <div className="space-y-4">
      <div className="grid gap-4">
        {schedules.map((schedule) => (
          <Card key={schedule.id}>
            <CardContent className="pt-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <FileText className="w-5 h-5 text-blue-500" />
                  <div>
                    <div className="font-medium">{schedule.report_type}</div>
                    <div className="text-sm text-slate-400">
                      {schedule.frequency} {schedule.time} 生成
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {schedule.is_active ? (
                    <Badge variant="default" className="bg-green-500">运行中</Badge>
                  ) : (
                    <Badge variant="secondary">已暂停</Badge>
                  )}
                  <Switch checked={schedule.is_active} />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>立即生成报告</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2">
            <Button variant="outline">生成日报</Button>
            <Button variant="outline">生成周报</Button>
            <Button variant="outline">生成月报</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// 主页面
export default function SalesAutomation() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="container mx-auto px-4 py-6">
        <PageHeader
          title="销售自动化"
          description="自动化销售流程，提高效率，减少遗漏"
          icon={<Zap className="w-6 h-6 text-yellow-500" />}
        />

        <Tabs defaultValue="reminders" className="mt-6">
          <TabsList className="grid w-full grid-cols-3 lg:w-[450px]">
            <TabsTrigger value="reminders">
              <Bell className="w-4 h-4 mr-2" />
              跟进提醒
            </TabsTrigger>
            <TabsTrigger value="rules">
              <CheckSquare className="w-4 h-4 mr-2" />
              自动任务
            </TabsTrigger>
            <TabsTrigger value="reports">
              <FileText className="w-4 h-4 mr-2" />
              自动报告
            </TabsTrigger>
          </TabsList>

          <TabsContent value="reminders" className="mt-6">
            <FollowUpReminders />
          </TabsContent>

          <TabsContent value="rules" className="mt-6">
            <AutomationRules />
          </TabsContent>

          <TabsContent value="reports" className="mt-6">
            <AutoReports />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
