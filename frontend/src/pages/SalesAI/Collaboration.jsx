/**
 * 销售协同页面
 * 
 * 功能：
 * 1. 内部协作留言
 * 2. 技术支持请求
 * 3. 知识库
 * 4. 经验分享会
 */

import { useState } from "react";
import { motion } from "framer-motion";
import {
  MessageSquare,
  HelpCircle,
  BookOpen,
  Users,
  Send,
  Plus,
  Search,
  ThumbsUp,
  Eye,
  Calendar,
  Clock,
  Play,
  CheckCircle,
  AlertCircle,
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
  Input,
  Textarea,
  Avatar,
  AvatarFallback,
} from "../../components/ui";

// 协作留言
function CollaborationMessages() {
  const [messages, _setMessages] = useState([
    {
      id: 1,
      author: "张三",
      avatar: "张",
      content: "这个客户的技术总监很关注测试精度，建议准备详细的技术参数对比表",
      time: "2 小时前",
      mentions: ["@李四"],
    },
    {
      id: 2,
      author: "李四",
      avatar: "李",
      content: "收到，我明天准备一份竞品对比报告",
      time: "1 小时前",
      mentions: [],
    },
  ]);
  const [newMessage, setNewMessage] = useState("");

  return (
    <div className="space-y-4">
      {/* 留言列表 */}
      <div className="space-y-4">
        {messages.map((msg) => (
          <Card key={msg.id}>
            <CardContent className="pt-4">
              <div className="flex items-start gap-3">
                <Avatar>
                  <AvatarFallback className="bg-blue-500 text-white">{msg.avatar}</AvatarFallback>
                </Avatar>
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="font-medium">{msg.author}</span>
                    <span className="text-xs text-slate-400">{msg.time}</span>
                  </div>
                  <p className="text-sm text-slate-300">{msg.content}</p>
                  {msg.mentions.length > 0 && (
                    <div className="mt-2">
                      {msg.mentions.map((mention, idx) => (
                        <Badge key={idx} variant="secondary" className="mr-2">{mention}</Badge>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* 发送留言 */}
      <Card>
        <CardContent className="pt-4">
          <Textarea
            placeholder="输入协作留言，可使用 @ 提及同事..."
            value={newMessage || "unknown"}
            onChange={(e) => setNewMessage(e.target.value)}
            className="mb-2"
          />
          <div className="flex justify-between items-center">
            <Button variant="outline" size="sm">
              <HelpCircle className="w-4 h-4 mr-2" />
              请求技术支持
            </Button>
            <Button>
              <Send className="w-4 h-4 mr-2" />
              发送
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// 技术支持请求
function SupportRequests() {
  const [requests, _setRequests] = useState([
    {
      id: 1,
      title: "FCT 测试方案技术咨询",
      customer: "宁德时代",
      priority: "HIGH",
      status: "processing",
      assignee: "陈工",
      deadline: "2025-03-05",
    },
    {
      id: 2,
      title: "EOL 设备选型建议",
      customer: "比亚迪",
      priority: "MEDIUM",
      status: "pending",
      assignee: null,
      deadline: "2025-03-03",
    },
  ]);

  const getStatusBadge = (status) => {
    const config = {
      pending: { label: "待处理", variant: "secondary" },
      processing: { label: "处理中", variant: "default" },
      completed: { label: "已完成", variant: "outline" },
    };
    return config[status] || config.pending;
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <div className="text-sm text-slate-400">
          待处理：<span className="text-orange-500 font-bold">1</span> · 
          处理中：<span className="text-blue-500 font-bold">1</span>
        </div>
        <Button>
          <Plus className="w-4 h-4 mr-2" />
          创建支持请求
        </Button>
      </div>

      <div className="space-y-4">
        {requests.map((req) => (
          <Card key={req.id}>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">{req.title}</CardTitle>
                <Badge variant={getStatusBadge(req.status).variant}>
                  {getStatusBadge(req.status).label}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="text-slate-400">客户：</span>
                  <span>{req.customer}</span>
                </div>
                <div>
                  <span className="text-slate-400">优先级：</span>
                  <Badge variant={req.priority === "HIGH" ? "destructive" : "secondary"}>
                    {req.priority === "HIGH" ? "高" : req.priority === "MEDIUM" ? "中" : "低"}
                  </Badge>
                </div>
                <div>
                  <span className="text-slate-400">处理人：</span>
                  <span>{req.assignee || "未分配"}</span>
                </div>
                <div>
                  <span className="text-slate-400">截止：</span>
                  <span>{req.deadline}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

// 知识库
function KnowledgeBase() {
  const [articles, _setArticles] = useState([
    {
      id: 1,
      title: "宁德时代 FCT 项目成功案例",
      category: "case",
      category_name: "成功案例",
      author: "张三",
      summary: "350 万 FCT 测试线项目，从接触 to 签约 45 天，关键成功因素分析",
      tags: ["FCT", "锂电", "大客户"],
      views: 256,
      likes: 42,
    },
    {
      id: 2,
      title: "竞品对比：我们 vs 竞品 A vs 竞品 B",
      category: "competitor",
      category_name: "竞品分析",
      author: "王五",
      summary: "详细对比技术参数、价格、服务，附应对策略",
      tags: ["竞品分析", "FCT", "EOL"],
      views: 512,
      likes: 89,
    },
    {
      id: 3,
      title: "价格谈判 10 大技巧",
      category: "skill",
      category_name: "销售技巧",
      author: "赵六",
      summary: "总结多年价格谈判经验，10 个实用技巧和话术",
      tags: ["谈判技巧", "价格"],
      views: 890,
      likes: 156,
    },
  ]);

  return (
    <div className="space-y-4">
      <div className="flex gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <Input placeholder="搜索知识库..." className="pl-10" />
        </div>
        <Button>
          <Plus className="w-4 h-4 mr-2" />
          贡献文章
        </Button>
      </div>

      <div className="grid gap-4">
        {articles.map((article) => (
          <Card key={article.id} className="hover:border-blue-500 cursor-pointer transition-colors">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Badge variant="outline">{article.category_name}</Badge>
                  <CardTitle className="text-base">{article.title}</CardTitle>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-slate-400 mb-3">{article.summary}</p>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4 text-sm text-slate-400">
                  <span>作者：{article.author}</span>
                  <div className="flex items-center gap-1">
                    <Eye className="w-3 h-3" />
                    {article.views}
                  </div>
                  <div className="flex items-center gap-1">
                    <ThumbsUp className="w-3 h-3" />
                    {article.likes}
                  </div>
                </div>
                <div className="flex gap-2">
                  {article.tags.map((tag, idx) => (
                    <Badge key={idx} variant="secondary" className="text-xs">{tag}</Badge>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

// 经验分享会
function ShareSessions() {
  const [sessions, _setSessions] = useState([
    {
      id: 1,
      title: "Q1 大单签约经验分享",
      speaker: "张三 - 高级销售",
      time: "2025-03-05 15:00",
      duration: 60,
      format: "线上",
      registered: 32,
      max: 50,
      status: "upcoming",
    },
    {
      id: 2,
      title: "竞品应对策略培训",
      speaker: "王五 - 销售经理",
      time: "2025-02-20 14:00",
      duration: 90,
      format: "线下",
      location: "深圳会议室 A",
      registered: 30,
      max: 30,
      status: "completed",
      recording: true,
    },
  ]);

  return (
    <div className="space-y-4">
      <div className="grid gap-4">
        {sessions.map((session) => (
          <Card key={session.id}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>{session.title}</CardTitle>
                  <CardDescription>
                    主讲：{session.speaker}
                  </CardDescription>
                </div>
                <Badge variant={session.status === "upcoming" ? "default" : "secondary"}>
                  {session.status === "upcoming" ? "即将开始" : "已结束"}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm mb-4">
                <div className="flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-slate-400" />
                  <span>{session.time}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4 text-slate-400" />
                  <span>{session.duration}分钟</span>
                </div>
                <div className="flex items-center gap-2">
                  <Users className="w-4 h-4 text-slate-400" />
                  <span>{session.registered}/{session.max} 人</span>
                </div>
                <div>
                  <Badge variant="outline">{session.format}</Badge>
                </div>
              </div>
              <div className="flex gap-2">
                {session.status === "upcoming" ? (
                  <Button>
                    <CheckCircle className="w-4 h-4 mr-2" />
                    立即报名
                  </Button>
                ) : session.recording ? (
                  <Button variant="outline">
                    <Play className="w-4 h-4 mr-2" />
                    观看回放
                  </Button>
                ) : null}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

// 主页面
export default function SalesCollaboration() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="container mx-auto px-4 py-6">
        <PageHeader
          title="销售协同"
          description="内部协作、知识共享、技术支持"
          icon={<Users className="w-6 h-6 text-indigo-500" />}
        />

        <Tabs defaultValue="messages" className="mt-6">
          <TabsList className="grid w-full grid-cols-4 lg:w-[600px]">
            <TabsTrigger value="messages">
              <MessageSquare className="w-4 h-4 mr-2" />
              协作留言
            </TabsTrigger>
            <TabsTrigger value="support">
              <HelpCircle className="w-4 h-4 mr-2" />
              技术支持
            </TabsTrigger>
            <TabsTrigger value="knowledge">
              <BookOpen className="w-4 h-4 mr-2" />
              知识库
            </TabsTrigger>
            <TabsTrigger value="sessions">
              <Calendar className="w-4 h-4 mr-2" />
              分享会
            </TabsTrigger>
          </TabsList>

          <TabsContent value="messages" className="mt-6">
            <CollaborationMessages />
          </TabsContent>

          <TabsContent value="support" className="mt-6">
            <SupportRequests />
          </TabsContent>

          <TabsContent value="knowledge" className="mt-6">
            <KnowledgeBase />
          </TabsContent>

          <TabsContent value="sessions" className="mt-6">
            <ShareSessions />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
