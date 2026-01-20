/**
 * 技术评审详情/创建页面
 * 支持创建、编辑、查看技术评审详情
 */
import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { cn as _cn } from "../lib/utils";
import { technicalReviewApi, projectApi, userApi } from "../services/api";
import { formatDate } from "../lib/utils";
import { PageHeader } from "../components/layout/PageHeader";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Input,
  Select,
  Textarea,
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
  SkeletonCard } from
"../components/ui";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter } from
"../components/ui";
import {
  ArrowLeft,
  Save,
  Plus,
  Trash2,
  Upload,
  FileText,
  Users,
  CheckSquare,
  AlertCircle,
  Calendar,
  MapPin,
  User,
  X } from
"lucide-react";

const getStatusBadge = (status) => {
  const badges = {
    DRAFT: { label: "草稿", color: "bg-slate-500/20 text-slate-400" },
    PENDING: { label: "待评审", color: "bg-blue-500/20 text-blue-400" },
    IN_PROGRESS: { label: "评审中", color: "bg-amber-500/20 text-amber-400" },
    COMPLETED: { label: "已完成", color: "bg-emerald-500/20 text-emerald-400" },
    CANCELLED: { label: "已取消", color: "bg-red-500/20 text-red-400" }
  };
  return badges[status] || badges.DRAFT;
};

const _getReviewTypeLabel = (type) => {
  const types = {
    PDR: "方案设计评审",
    DDR: "详细设计评审",
    PRR: "生产准备评审",
    FRR: "出厂评审",
    ARR: "现场评审"
  };
  return types[type] || type;
};

export default function TechnicalReviewDetail() {
  const { reviewId } = useParams();
  const navigate = useNavigate();
  const isNew = reviewId === "new";

  const [loading, setLoading] = useState(!isNew);
  const [saving, setSaving] = useState(false);
  const [review, setReview] = useState(null);
  const [activeTab, setActiveTab] = useState("basic");

  // 表单数据
  const [formData, setFormData] = useState({
    review_type: "PDR",
    review_name: "",
    project_id: "",
    equipment_id: "",
    scheduled_date: "",
    location: "",
    meeting_type: "ONSITE",
    host_id: "",
    presenter_id: "",
    recorder_id: ""
  });

  // 关联数据
  const [projects, setProjects] = useState([]);
  const [users, setUsers] = useState([]);
  const [participants, setParticipants] = useState([]);
  const [materials, setMaterials] = useState([]);
  const [checklistRecords, setChecklistRecords] = useState([]);
  const [issues, setIssues] = useState([]);

  // 对话框
  const [_participantDialog, setParticipantDialog] = useState({ open: false });
  const [_materialDialog, setMaterialDialog] = useState({ open: false });
  const [_checklistDialog, setChecklistDialog] = useState({ open: false });
  const [_issueDialog, setIssueDialog] = useState({ open: false });

  useEffect(() => {
    if (isNew) {
      setLoading(false);
    } else {
      fetchReview();
    }
    fetchProjects();
    fetchUsers();
  }, [reviewId]);

  const fetchProjects = async () => {
    try {
      const response = await projectApi.list({ page: 1, page_size: 100 });
      const data = response.data || response;
      setProjects(data.items || []);
    } catch (error) {
      console.error("Failed to fetch projects:", error);
    }
  };

  const fetchUsers = async () => {
    try {
      const response = await userApi.list({ page: 1, page_size: 100 });
      const data = response.data || response;
      setUsers(data.items || []);
    } catch (error) {
      console.error("Failed to fetch users:", error);
    }
  };

  const fetchReview = async () => {
    try {
      setLoading(true);
      const response = await technicalReviewApi.get(reviewId);
      const data = response.data || response;
      setReview(data);
      setFormData({
        review_type: data.review_type,
        review_name: data.review_name,
        project_id: data.project_id,
        equipment_id: data.equipment_id || "",
        scheduled_date: formatDate(data.scheduled_date, "YYYY-MM-DDTHH:mm"),
        location: data.location || "",
        meeting_type: data.meeting_type,
        host_id: data.host_id,
        presenter_id: data.presenter_id,
        recorder_id: data.recorder_id
      });
      setParticipants(data.participants || []);
      setMaterials(data.materials || []);
      setChecklistRecords(data.checklist_records || []);
      setIssues(data.issues || []);
    } catch (error) {
      console.error("Failed to fetch review:", error);
      alert("加载失败：" + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      if (isNew) {
        await technicalReviewApi.create(formData);
        navigate("/technical-reviews");
      } else {
        await technicalReviewApi.update(reviewId, formData);
        await fetchReview();
      }
    } catch (error) {
      console.error("Failed to save:", error);
      alert("保存失败：" + (error.response?.data?.detail || error.message));
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 p-6 space-y-6">
        <SkeletonCard />
        <SkeletonCard />
      </div>);

  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <PageHeader
        title={
        isNew ? "创建技术评审" : `技术评审 - ${review?.review_name || ""}`
        }
        description={
        isNew ? "创建新的技术评审" : `评审编号: ${review?.review_no || ""}`
        }
        action={
        <div className="flex items-center gap-2">
            <Button
            variant="outline"
            onClick={() => navigate("/technical-reviews")}
            className="border-slate-700">

              <ArrowLeft className="w-4 h-4 mr-2" />
              返回列表
            </Button>
            <Button
            onClick={handleSave}
            disabled={saving}
            className="bg-blue-600 hover:bg-blue-700">

              <Save className="w-4 h-4 mr-2" />
              {saving ? "保存中..." : "保存"}
            </Button>
        </div>
        } />


      <div className="container mx-auto px-4 py-6">
        <Tabs
          value={activeTab}
          onValueChange={setActiveTab}
          className="space-y-6">

          <TabsList className="bg-slate-900/50 border-slate-800">
            <TabsTrigger value="basic">基本信息</TabsTrigger>
            <TabsTrigger value="participants">
              参与人 ({participants.length})
            </TabsTrigger>
            <TabsTrigger value="materials">
              材料 ({materials.length})
            </TabsTrigger>
            <TabsTrigger value="checklist">
              检查项 ({checklistRecords.length})
            </TabsTrigger>
            <TabsTrigger value="issues">问题 ({issues.length})</TabsTrigger>
          </TabsList>

          {/* 基本信息 */}
          <TabsContent value="basic" className="space-y-4">
            <Card className="bg-slate-900/50 border-slate-800">
              <CardHeader>
                <CardTitle>评审信息</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      评审类型 *
                    </label>
                    <Select
                      value={formData.review_type}
                      onValueChange={(value) =>
                      setFormData({ ...formData, review_type: value })
                      }
                      className="bg-slate-800/50 border-slate-700">

                      <option value="PDR">方案设计评审 (PDR)</option>
                      <option value="DDR">详细设计评审 (DDR)</option>
                      <option value="PRR">生产准备评审 (PRR)</option>
                      <option value="FRR">出厂评审 (FRR)</option>
                      <option value="ARR">现场评审 (ARR)</option>
                    </Select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      评审名称 *
                    </label>
                    <Input
                      value={formData.review_name}
                      onChange={(e) =>
                      setFormData({
                        ...formData,
                        review_name: e.target.value
                      })
                      }
                      placeholder="请输入评审名称"
                      className="bg-slate-800/50 border-slate-700" />

                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      关联项目 *
                    </label>
                    <Select
                      value={formData.project_id}
                      onValueChange={(value) =>
                      setFormData({ ...formData, project_id: value })
                      }
                      className="bg-slate-800/50 border-slate-700">

                      <option value="">请选择项目</option>
                      {projects.map((p) =>
                      <option key={p.id} value={p.id}>
                          {p.project_code} - {p.project_name}
                      </option>
                      )}
                    </Select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      计划评审时间 *
                    </label>
                    <Input
                      type="datetime-local"
                      value={formData.scheduled_date}
                      onChange={(e) =>
                      setFormData({
                        ...formData,
                        scheduled_date: e.target.value
                      })
                      }
                      className="bg-slate-800/50 border-slate-700" />

                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      评审地点
                    </label>
                    <Input
                      value={formData.location}
                      onChange={(e) =>
                      setFormData({ ...formData, location: e.target.value })
                      }
                      placeholder="请输入评审地点"
                      className="bg-slate-800/50 border-slate-700" />

                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      会议形式 *
                    </label>
                    <Select
                      value={formData.meeting_type}
                      onValueChange={(value) =>
                      setFormData({ ...formData, meeting_type: value })
                      }
                      className="bg-slate-800/50 border-slate-700">

                      <option value="ONSITE">现场</option>
                      <option value="ONLINE">线上</option>
                      <option value="HYBRID">混合</option>
                    </Select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      主持人 *
                    </label>
                    <Select
                      value={formData.host_id}
                      onValueChange={(value) =>
                      setFormData({ ...formData, host_id: value })
                      }
                      className="bg-slate-800/50 border-slate-700">

                      <option value="">请选择主持人</option>
                      {users.map((u) =>
                      <option key={u.id} value={u.id}>
                          {u.real_name || u.username}
                      </option>
                      )}
                    </Select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      汇报人 *
                    </label>
                    <Select
                      value={formData.presenter_id}
                      onValueChange={(value) =>
                      setFormData({ ...formData, presenter_id: value })
                      }
                      className="bg-slate-800/50 border-slate-700">

                      <option value="">请选择汇报人</option>
                      {users.map((u) =>
                      <option key={u.id} value={u.id}>
                          {u.real_name || u.username}
                      </option>
                      )}
                    </Select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      记录人 *
                    </label>
                    <Select
                      value={formData.recorder_id}
                      onValueChange={(value) =>
                      setFormData({ ...formData, recorder_id: value })
                      }
                      className="bg-slate-800/50 border-slate-700">

                      <option value="">请选择记录人</option>
                      {users.map((u) =>
                      <option key={u.id} value={u.id}>
                          {u.real_name || u.username}
                      </option>
                      )}
                    </Select>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* 评审结论（仅查看模式） */}
            {!isNew && review?.conclusion &&
            <Card className="bg-slate-900/50 border-slate-800">
                <CardHeader>
                  <CardTitle>评审结论</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-slate-400">结论:</span>
                      <Badge
                      className={getStatusBadge(review.conclusion).color}>

                        {review.conclusion === "PASS" && "通过"}
                        {review.conclusion === "PASS_WITH_CONDITION" &&
                      "有条件通过"}
                        {review.conclusion === "REJECT" && "不通过"}
                        {review.conclusion === "ABORT" && "中止"}
                      </Badge>
                    </div>
                    {review.conclusion_summary &&
                  <p className="text-sm text-slate-300">
                        {review.conclusion_summary}
                  </p>
                  }
                    {review.condition_deadline &&
                  <p className="text-sm text-slate-400">
                        整改期限:{" "}
                        {formatDate(review.condition_deadline, "YYYY-MM-DD")}
                  </p>
                  }
                  </div>
                </CardContent>
            </Card>
            }
          </TabsContent>

          {/* 参与人 */}
          <TabsContent value="participants" className="space-y-4">
            <Card className="bg-slate-900/50 border-slate-800">
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>评审参与人</CardTitle>
                {!isNew &&
                <Button
                  size="sm"
                  onClick={() => setParticipantDialog({ open: true })}
                  className="bg-blue-600 hover:bg-blue-700">

                    <Plus className="w-4 h-4 mr-2" />
                    添加参与人
                </Button>
                }
              </CardHeader>
              <CardContent>
                {participants.length === 0 ?
                <p className="text-center text-slate-400 py-8">暂无参与人</p> :

                <div className="space-y-2">
                    {participants.map((p) =>
                  <div
                    key={p.id}
                    className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg">

                        <div className="flex items-center gap-3">
                          <User className="w-5 h-5 text-slate-400" />
                          <div>
                            <p className="text-slate-200">
                              {users.find((u) => u.id === p.user_id)?.
                          real_name ||
                          users.find((u) => u.id === p.user_id)?.
                          username ||
                          `用户${p.user_id}`}
                            </p>
                            <p className="text-sm text-slate-400">
                              {p.role} {p.is_required ? "(必需)" : "(可选)"}
                            </p>
                          </div>
                        </div>
                        <Badge
                      className={
                      getStatusBadge(p.attendance || "PENDING").color
                      }>

                          {p.attendance === "CONFIRMED" && "已确认"}
                          {p.attendance === "ABSENT" && "缺席"}
                          {p.attendance === "DELEGATED" && "已委派"}
                          {!p.attendance && "待确认"}
                        </Badge>
                  </div>
                  )}
                </div>
                }
              </CardContent>
            </Card>
          </TabsContent>

          {/* 材料 */}
          <TabsContent value="materials" className="space-y-4">
            <Card className="bg-slate-900/50 border-slate-800">
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>评审材料</CardTitle>
                {!isNew &&
                <Button
                  size="sm"
                  onClick={() => setMaterialDialog({ open: true })}
                  className="bg-blue-600 hover:bg-blue-700">

                    <Upload className="w-4 h-4 mr-2" />
                    上传材料
                </Button>
                }
              </CardHeader>
              <CardContent>
                {materials.length === 0 ?
                <p className="text-center text-slate-400 py-8">暂无材料</p> :

                <div className="space-y-2">
                    {materials.map((m) =>
                  <div
                    key={m.id}
                    className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg">

                        <div className="flex items-center gap-3">
                          <FileText className="w-5 h-5 text-slate-400" />
                          <div>
                            <p className="text-slate-200">{m.material_name}</p>
                            <p className="text-sm text-slate-400">
                              {m.material_type} |{" "}
                              {(m.file_size / 1024 / 1024).toFixed(2)}MB{" "}
                              {m.is_required && "(必需)"}
                            </p>
                          </div>
                        </div>
                        {!isNew &&
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={async () => {
                        if (confirm("确定删除此材料吗？")) {
                          try {
                            await technicalReviewApi.deleteMaterial(m.id);
                            await fetchReview();
                          } catch (_error) {
                            alert("删除失败");
                          }
                        }
                      }}
                      className="text-red-400 hover:text-red-300">

                            <Trash2 className="w-4 h-4" />
                    </Button>
                    }
                  </div>
                  )}
                </div>
                }
              </CardContent>
            </Card>
          </TabsContent>

          {/* 检查项 */}
          <TabsContent value="checklist" className="space-y-4">
            <Card className="bg-slate-900/50 border-slate-800">
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>检查项记录</CardTitle>
                {!isNew &&
                <Button
                  size="sm"
                  onClick={() => setChecklistDialog({ open: true })}
                  className="bg-blue-600 hover:bg-blue-700">

                    <Plus className="w-4 h-4 mr-2" />
                    添加检查项
                </Button>
                }
              </CardHeader>
              <CardContent>
                {checklistRecords.length === 0 ?
                <p className="text-center text-slate-400 py-8">
                    暂无检查项记录
                </p> :

                <div className="space-y-2">
                    {checklistRecords.map((c) =>
                  <div
                    key={c.id}
                    className="p-3 bg-slate-800/50 rounded-lg space-y-2">

                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-slate-200">{c.check_item}</p>
                            <p className="text-sm text-slate-400">
                              {c.category}
                            </p>
                          </div>
                          <Badge
                        className={
                        c.result === "PASS" ?
                        "bg-emerald-500/20 text-emerald-400" :
                        c.result === "FAIL" ?
                        "bg-red-500/20 text-red-400" :
                        "bg-slate-500/20 text-slate-400"
                        }>

                            {c.result === "PASS" && "通过"}
                            {c.result === "FAIL" && "不通过"}
                            {c.result === "NA" && "不适用"}
                          </Badge>
                        </div>
                        {c.issue_desc &&
                    <p className="text-sm text-amber-400">
                            问题: {c.issue_desc} (等级: {c.issue_level})
                    </p>
                    }
                  </div>
                  )}
                </div>
                }
              </CardContent>
            </Card>
          </TabsContent>

          {/* 问题 */}
          <TabsContent value="issues" className="space-y-4">
            <Card className="bg-slate-900/50 border-slate-800">
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>评审问题</CardTitle>
                {!isNew &&
                <Button
                  size="sm"
                  onClick={() => setIssueDialog({ open: true })}
                  className="bg-blue-600 hover:bg-blue-700">

                    <Plus className="w-4 h-4 mr-2" />
                    创建问题
                </Button>
                }
              </CardHeader>
              <CardContent>
                {issues.length === 0 ?
                <p className="text-center text-slate-400 py-8">暂无问题</p> :

                <div className="space-y-3">
                    {issues.map((i) =>
                  <div
                    key={i.id}
                    className="p-4 bg-slate-800/50 rounded-lg space-y-2">

                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <Badge
                          className={
                          i.issue_level === "A" ?
                          "bg-red-500/20 text-red-400" :
                          i.issue_level === "B" ?
                          "bg-orange-500/20 text-orange-400" :
                          i.issue_level === "C" ?
                          "bg-amber-500/20 text-amber-400" :
                          "bg-blue-500/20 text-blue-400"
                          }>

                              {i.issue_level}类问题
                            </Badge>
                            <span className="text-sm text-slate-400">
                              {i.issue_no}
                            </span>
                          </div>
                          <Badge className={getStatusBadge(i.status).color}>
                            {i.status === "OPEN" && "开放"}
                            {i.status === "PROCESSING" && "处理中"}
                            {i.status === "RESOLVED" && "已解决"}
                            {i.status === "VERIFIED" && "已验证"}
                            {i.status === "CLOSED" && "已关闭"}
                          </Badge>
                        </div>
                        <p className="text-slate-200">{i.description}</p>
                        <div className="flex items-center gap-4 text-sm text-slate-400">
                          <span>类别: {i.category}</span>
                          <span>
                            责任人:{" "}
                            {users.find((u) => u.id === i.assignee_id)?.
                        real_name ||
                        users.find((u) => u.id === i.assignee_id)?.
                        username ||
                        `用户${i.assignee_id}`}
                          </span>
                          <span>
                            期限: {formatDate(i.deadline, "YYYY-MM-DD")}
                          </span>
                        </div>
                        {i.solution &&
                    <p className="text-sm text-slate-300">
                            解决方案: {i.solution}
                    </p>
                    }
                  </div>
                  )}
                </div>
                }
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>);

}