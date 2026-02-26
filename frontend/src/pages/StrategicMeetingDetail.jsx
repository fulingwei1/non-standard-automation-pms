import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { managementRhythmApi } from "../services/api";
import { PageHeader } from "../components/layout/PageHeader";
import StrategicStructureEditor from "../components/StrategicStructureEditor";
import {
  Card,
  CardContent,
  Badge,
  Button,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "../components/ui";
import {
import { formatDate } from "@/lib/formatters";
  ArrowLeft,
  Calendar,
  Users,
  FileText,
  Target,
  CheckCircle2,
  Clock,
  Save,
} from "lucide-react";

export default function StrategicMeetingDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [meeting, setMeeting] = useState(null);
  const [activeTab, setActiveTab] = useState("structure");

  useEffect(() => {
    if (id) {
      fetchMeeting();
    }
  }, [id]);

  const fetchMeeting = async () => {
    try {
      setLoading(true);
      const res = await managementRhythmApi.meetings.get(id);
      const data = res.data || res;
      setMeeting(data);
    } catch (err) {
      console.error("Failed to fetch meeting:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveStructure = async (structure) => {
    try {
      await managementRhythmApi.meetings.updateMinutes(id, {
        minutes: meeting.minutes || "",
        strategic_structure: structure,
      });
      setMeeting((prev) => ({
        ...prev,
        strategic_structure: structure,
      }));
      alert("战略结构已保存");
    } catch (err) {
      console.error("Failed to save structure:", err);
      alert("保存失败: " + (err.response?.data?.detail || err.message));
    }
  };


  const formatTime = (timeStr) => {
    if (!timeStr) {return "";}
    return timeStr.substring(0, 5);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4" />
          <p className="text-gray-600">加载中...</p>
        </div>
      </div>
    );
  }

  if (!meeting) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">会议不存在</p>
        <Button
          onClick={() => navigate("/strategic-meetings")}
          className="mt-4"
        >
          返回列表
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate("/strategic-meetings")}
            >
              <ArrowLeft className="w-4 h-4" />
            </Button>
            <span>{meeting.meeting_name}</span>
          </div>
        }
        description={`${formatDate(meeting.meeting_date)} ${meeting.start_time ? formatTime(meeting.start_time) : ""}`}
      />

      {/* 会议基本信息 */}
      <Card>
        <CardContent className="p-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <div className="text-sm text-gray-500 mb-1">会议层级</div>
              <Badge>
                {meeting.rhythm_level === "STRATEGIC"
                  ? "战略层"
                  : meeting.rhythm_level}
              </Badge>
            </div>
            <div>
              <div className="text-sm text-gray-500 mb-1">周期类型</div>
              <div className="font-medium">{meeting.cycle_type}</div>
            </div>
            <div>
              <div className="text-sm text-gray-500 mb-1">组织者</div>
              <div className="font-medium">{meeting.organizer_name || "-"}</div>
            </div>
            <div>
              <div className="text-sm text-gray-500 mb-1">状态</div>
              <Badge>{meeting.status}</Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 标签页 */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="structure">
            <Target className="w-4 h-4 mr-2" />
            五层战略结构
          </TabsTrigger>
          <TabsTrigger value="minutes">
            <FileText className="w-4 h-4 mr-2" />
            会议纪要
          </TabsTrigger>
          <TabsTrigger value="actions">
            <CheckCircle2 className="w-4 h-4 mr-2" />
            行动项 ({meeting.action_items_count || 0})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="structure" className="mt-6">
          <StrategicStructureEditor
            meetingId={id}
            initialData={meeting.strategic_structure}
            onSave={handleSaveStructure}
            readOnly={meeting.status === "COMPLETED"}
          />
        </TabsContent>

        <TabsContent value="minutes" className="mt-6">
          <Card>
            <CardContent className="p-6">
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">
                    会议议程
                  </label>
                  <div className="p-4 bg-gray-50 rounded-lg whitespace-pre-wrap">
                    {meeting.agenda || "暂无议程"}
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">
                    会议纪要
                  </label>
                  <div className="p-4 bg-gray-50 rounded-lg whitespace-pre-wrap">
                    {meeting.minutes || "暂无纪要"}
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">
                    会议决议
                  </label>
                  <div className="p-4 bg-gray-50 rounded-lg whitespace-pre-wrap">
                    {meeting.decisions || "暂无决议"}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="actions" className="mt-6">
          <Card>
            <CardContent className="p-6">
              <p className="text-gray-500">行动项列表功能开发中...</p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
