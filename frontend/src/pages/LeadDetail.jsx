/**
 * Lead Detail Page - 线索详情页面
 * Features: 线索详情、跟进记录、转换商机
 */
import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  User,
  Phone,
  Mail,
  MapPin,
  Building2,
  Calendar,
  Clock,
  RefreshCw,
  Plus,
  ArrowRight,
  CheckCircle2,
  AlertTriangle } from
"lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle } from
"../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue } from
"../components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow } from
"../components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter } from
"../components/ui/dialog";
import { cn as _cn, formatDate } from "../lib/utils";
import { leadApi, customerApi } from "../services/api";
import { confirmAction } from "@/lib/confirmAction";
const statusConfigs = {
  NEW: { label: "待跟进", color: "bg-blue-500" },
  CONTACTED: { label: "已联系", color: "bg-sky-500" },
  QUALIFIED: { label: "已合格", color: "bg-amber-500" },
  LOST: { label: "已丢失", color: "bg-red-500" },
  CONVERTED: { label: "已转商机", color: "bg-emerald-500" },
  QUALIFYING: { label: "已合格", color: "bg-amber-500" },
  INVALID: { label: "已丢失", color: "bg-red-500" }
};
const followUpTypeConfigs = {
  CALL: { label: "电话", color: "bg-blue-500" },
  VISIT: { label: "拜访", color: "bg-purple-500" },
  EMAIL: { label: "邮件", color: "bg-amber-500" },
  MEETING: { label: "会议", color: "bg-emerald-500" },
  OTHER: { label: "其他", color: "bg-slate-500" }
};
export default function LeadDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [lead, setLead] = useState(null);
  const [followUps, setFollowUps] = useState([]);
  const [customers, setCustomers] = useState([]);
  // Dialogs
  const [showFollowUpDialog, setShowFollowUpDialog] = useState(false);
  const [showConvertDialog, setShowConvertDialog] = useState(false);
  // Form states
  const [followUpData, setFollowUpData] = useState({
    follow_up_type: "CALL",
    content: "",
    next_action: "",
    next_action_at: ""
  });
  const [convertData, setConvertData] = useState({
    customer_id: null,
    skip_validation: false
  });
  useEffect(() => {
    if (id) {
      fetchLeadDetail();
      fetchFollowUps();
      fetchCustomers();
    }
  }, [id]);
  const fetchLeadDetail = async () => {
    try {
      setLoading(true);
      const res = await leadApi.get(id);
      setLead(res.data || res);
    } catch (error) {
      console.error("Failed to fetch lead detail:", error);
    } finally {
      setLoading(false);
    }
  };
  const fetchFollowUps = async () => {
    try {
      const res = await leadApi.getFollowUps(id);
      const followUpList = res.data || res || [];
      setFollowUps(followUpList);
    } catch (error) {
      console.error("Failed to fetch follow-ups:", error);
    }
  };
  const fetchCustomers = async () => {
    try {
      const res = await customerApi.list({ page_size: 1000 });
      setCustomers(res.data?.items || res.data?.items || res.data || []);
    } catch (error) {
      console.error("Failed to fetch customers:", error);
    }
  };
  const handleCreateFollowUp = async () => {
    if (!followUpData.content) {
      alert("请填写跟进内容");
      return;
    }
    try {
      await leadApi.createFollowUp(id, followUpData);
      setShowFollowUpDialog(false);
      setFollowUpData({
        follow_up_type: "CALL",
        content: "",
        next_action: "",
        next_action_at: ""
      });
      fetchFollowUps();
      fetchLeadDetail();
    } catch (error) {
      console.error("Failed to create follow-up:", error);
      alert(
        "创建跟进记录失败: " + (error.response?.data?.detail || error.message)
      );
    }
  };
  const handleConvert = async () => {
    if (!convertData.customer_id) {
      alert("请选择客户");
      return;
    }
    try {
      const res = await leadApi.convert(
        id,
        convertData.customer_id,
        null,
        convertData.skip_validation
      );
      alert("转换成功");
      navigate(`/opportunities/${res.data?.id || res.id}`);
    } catch (error) {
      console.error("Failed to convert lead:", error);
      const errorMsg = error.response?.data?.detail || error.message;
      if (errorMsg.includes("G1阶段门验证失败")) {
        if (await confirmAction(errorMsg + "\n\n是否跳过验证继续转换？")) {
          setConvertData({ ...convertData, skip_validation: true });
          handleConvert();
        }
      } else {
        alert("转换失败: " + errorMsg);
      }
    }
  };
  if (loading) {
    return (
      <div className="space-y-6 p-6">
        <div className="text-center py-8 text-slate-400">加载中...</div>
      </div>);

  }
  if (!lead) {
    return (
      <div className="space-y-6 p-6">
        <div className="text-center py-8 text-slate-400">线索不存在</div>
      </div>);

  }
  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate("/sales/leads")}>

            <ArrowLeft className="w-4 h-4 mr-2" />
            返回列表
          </Button>
          <PageHeader
            title={`线索详情 - ${lead.lead_code || lead.customer_name}`}
            description="线索详情、跟进记录、转换商机" />

        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={fetchLeadDetail}>
            <RefreshCw className="w-4 h-4 mr-2" />
            刷新
          </Button>
          {lead.status !== "CONVERTED" &&
          <>
              <Button
              variant="outline"
              onClick={() => setShowFollowUpDialog(true)}>

                <Plus className="w-4 h-4 mr-2" />
                添加跟进
              </Button>
              <Button onClick={() => setShowConvertDialog(true)}>
                <ArrowRight className="w-4 h-4 mr-2" />
                转商机
              </Button>
          </>
          }
        </div>
      </div>
      {/* Basic Information */}
      <Card>
        <CardHeader>
          <CardTitle>基本信息</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <div className="text-sm text-slate-500 mb-1">线索编码</div>
              <div className="font-mono font-medium">{lead.lead_code}</div>
            </div>
            <div>
              <div className="text-sm text-slate-500 mb-1">状态</div>
              <Badge
                className={statusConfigs[lead.status]?.color || "bg-slate-500"}>

                {statusConfigs[lead.status]?.label || lead.status}
              </Badge>
            </div>
            <div>
              <div className="text-sm text-slate-500 mb-1">客户名称</div>
              <div className="font-medium">{lead.customer_name || "-"}</div>
            </div>
            <div>
              <div className="text-sm text-slate-500 mb-1">负责人</div>
              <div>{lead.owner_name || "-"}</div>
            </div>
            <div>
              <div className="text-sm text-slate-500 mb-1">来源</div>
              <div>{lead.source || "-"}</div>
            </div>
            <div>
              <div className="text-sm text-slate-500 mb-1">行业</div>
              <div>{lead.industry || "-"}</div>
            </div>
            <div>
              <div className="text-sm text-slate-500 mb-1">联系人</div>
              <div className="flex items-center gap-1">
                <User className="w-4 h-4 text-slate-400" />
                {lead.contact_name || "-"}
              </div>
            </div>
            <div>
              <div className="text-sm text-slate-500 mb-1">联系电话</div>
              <div className="flex items-center gap-1">
                <Phone className="w-4 h-4 text-slate-400" />
                {lead.contact_phone || "-"}
              </div>
            </div>
            {lead.contact_email &&
            <div>
                <div className="text-sm text-slate-500 mb-1">联系邮箱</div>
                <div className="flex items-center gap-1">
                  <Mail className="w-4 h-4 text-slate-400" />
                  {lead.contact_email}
                </div>
            </div>
            }
            {lead.address &&
            <div>
                <div className="text-sm text-slate-500 mb-1">地址</div>
                <div className="flex items-center gap-1">
                  <MapPin className="w-4 h-4 text-slate-400" />
                  {lead.address}
                </div>
            </div>
            }
            {lead.next_action_at &&
            <div>
                <div className="text-sm text-slate-500 mb-1">下次行动时间</div>
                <div className="flex items-center gap-1">
                  <Clock className="w-4 h-4 text-slate-400" />
                  {formatDate(lead.next_action_at)}
                </div>
            </div>
            }
            <div>
              <div className="text-sm text-slate-500 mb-1">创建时间</div>
              <div className="flex items-center gap-1">
                <Calendar className="w-4 h-4 text-slate-400" />
                {formatDate(lead.created_at)}
              </div>
            </div>
          </div>
          {lead.demand_summary &&
          <div className="mt-4">
              <div className="text-sm text-slate-500 mb-2">需求摘要</div>
              <div className="p-3 bg-slate-50 rounded-lg">
                {lead.demand_summary}
              </div>
          </div>
          }
        </CardContent>
      </Card>
      {/* Follow-up Records */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>跟进记录</CardTitle>
            <Badge variant="outline">{followUps.length} 条记录</Badge>
          </div>
        </CardHeader>
        <CardContent>
          {followUps.length === 0 ?
          <div className="text-center py-8 text-slate-400">暂无跟进记录</div> :

          <div className="space-y-4">
              {followUps.map((followUp) =>
            <div key={followUp.id} className="border rounded-lg p-4">
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <Badge
                    className={
                    followUpTypeConfigs[followUp.follow_up_type]?.color ||
                    "bg-slate-500"
                    }>

                        {followUpTypeConfigs[followUp.follow_up_type]?.label ||
                    followUp.follow_up_type}
                      </Badge>
                      <span className="text-sm text-slate-500">
                        {followUp.creator_name || "未知"}
                      </span>
                    </div>
                    <span className="text-sm text-slate-500">
                      {formatDate(followUp.created_at)}
                    </span>
                  </div>
                  <div className="text-sm text-slate-700 mb-2">
                    {followUp.content}
                  </div>
                  {followUp.next_action &&
              <div className="flex items-center gap-2 text-sm">
                      <span className="text-slate-500">下次行动:</span>
                      <span className="font-medium">
                        {followUp.next_action}
                      </span>
                      {followUp.next_action_at &&
                <>
                          <span className="text-slate-500">|</span>
                          <span className="text-slate-500">
                            {formatDate(followUp.next_action_at)}
                          </span>
                </>
                }
              </div>
              }
            </div>
            )}
          </div>
          }
        </CardContent>
      </Card>
      {/* Create Follow-up Dialog */}
      <Dialog open={showFollowUpDialog} onOpenChange={setShowFollowUpDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>添加跟进记录</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">
                  跟进类型 *
                </label>
                <Select
                  value={followUpData.follow_up_type}
                  onValueChange={(val) =>
                  setFollowUpData({ ...followUpData, follow_up_type: val })
                  }>

                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(followUpTypeConfigs).map(
                      ([key, config]) =>
                      <SelectItem key={key} value={key}>
                          {config.label}
                      </SelectItem>

                    )}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">
                  跟进内容 *
                </label>
                <textarea
                  className="w-full min-h-[100px] p-3 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={followUpData.content}
                  onChange={(e) =>
                  setFollowUpData({
                    ...followUpData,
                    content: e.target.value
                  })
                  }
                  placeholder="详细记录跟进内容..." />

              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">
                  下次行动
                </label>
                <Input
                  value={followUpData.next_action}
                  onChange={(e) =>
                  setFollowUpData({
                    ...followUpData,
                    next_action: e.target.value
                  })
                  }
                  placeholder="下次行动计划" />

              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">
                  下次行动时间
                </label>
                <Input
                  type="datetime-local"
                  value={followUpData.next_action_at}
                  onChange={(e) =>
                  setFollowUpData({
                    ...followUpData,
                    next_action_at: e.target.value
                  })
                  } />

              </div>
            </div>
          </DialogBody>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowFollowUpDialog(false)}>

              取消
            </Button>
            <Button onClick={handleCreateFollowUp}>保存</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      {/* Convert Dialog */}
      <Dialog open={showConvertDialog} onOpenChange={setShowConvertDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>转换商机</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">
                  选择客户 *
                </label>
                <Select
                  value={convertData.customer_id?.toString() || ""}
                  onValueChange={(val) =>
                  setConvertData({
                    ...convertData,
                    customer_id: val ? parseInt(val) : null
                  })
                  }>

                  <SelectTrigger>
                    <SelectValue placeholder="选择客户" />
                  </SelectTrigger>
                  <SelectContent>
                    {customers.map((customer) =>
                    <SelectItem
                      key={customer.id}
                      value={customer.id.toString()}>

                        {customer.customer_name}
                    </SelectItem>
                    )}
                  </SelectContent>
                </Select>
              </div>
              <div className="p-3 bg-amber-50 rounded-lg">
                <div className="flex items-start gap-2">
                  <AlertTriangle className="w-5 h-5 text-amber-600 mt-0.5" />
                  <div className="text-sm text-amber-800">
                    <div className="font-medium mb-1">G1阶段门验证要求：</div>
                    <ul className="list-disc list-inside space-y-1 text-xs">
                      <li>客户基本信息与联系人齐全</li>
                      <li>
                        需求模板必填项：行业/产品对象/节拍/接口/现场约束/验收依据
                      </li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </DialogBody>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowConvertDialog(false)}>

              取消
            </Button>
            <Button onClick={handleConvert}>转换</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>);

}
