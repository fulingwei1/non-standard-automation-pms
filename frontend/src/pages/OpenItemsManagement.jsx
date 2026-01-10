/**
 * Open Items Management Page - 未决事项管理页面
 * 管理线索和商机的未决事项
 */

import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  Plus,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Calendar,
  User,
  Edit,
  Trash2,
} from "lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  Input,
  Label,
  Textarea,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui";
import { technicalAssessmentApi } from "../services/api";

const itemTypeConfig = {
  INTERFACE: "接口",
  TAKT: "节拍",
  ACCEPTANCE: "验收",
  SAMPLE: "样品",
  SITE: "现场",
  REGULATION: "法规",
  BUSINESS: "商务",
  OTHER: "其他",
};

const statusConfig = {
  PENDING: { label: "待确认", color: "bg-yellow-500" },
  REPLIED: { label: "已回复", color: "bg-blue-500" },
  VERIFIED: { label: "已验证", color: "bg-green-500" },
  CLOSED: { label: "已关闭", color: "bg-gray-500" },
};

export default function OpenItemsManagement() {
  const { sourceType, sourceId } = useParams();
  const navigate = useNavigate();

  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [formData, setFormData] = useState({
    item_type: "",
    description: "",
    responsible_party: "",
    responsible_person_id: null,
    due_date: "",
    blocks_quotation: false,
  });

  useEffect(() => {
    loadItems();
  }, [sourceType, sourceId]);

  const loadItems = async () => {
    try {
      setLoading(true);
      const response = await technicalAssessmentApi.getOpenItems({
        source_type: sourceType?.toUpperCase(),
        source_id: parseInt(sourceId),
      });
      setItems(response.data.items || response.data || []);
    } catch (error) {
      console.error("加载未决事项失败:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    try {
      let response;
      if (sourceType === "lead") {
        response = await technicalAssessmentApi.createOpenItemForLead(
          parseInt(sourceId),
          formData,
        );
      } else {
        response = await technicalAssessmentApi.createOpenItemForOpportunity(
          parseInt(sourceId),
          formData,
        );
      }

      setShowCreateDialog(false);
      setFormData({
        item_type: "",
        description: "",
        responsible_party: "",
        responsible_person_id: null,
        due_date: "",
        blocks_quotation: false,
      });
      await loadItems();
    } catch (error) {
      console.error("创建未决事项失败:", error);
      alert("创建失败: " + (error.response?.data?.detail || error.message));
    }
  };

  const handleClose = async (itemId) => {
    if (!confirm("确定要关闭此未决事项吗？")) return;

    try {
      await technicalAssessmentApi.closeOpenItem(itemId);
      await loadItems();
    } catch (error) {
      console.error("关闭未决事项失败:", error);
      alert("关闭失败: " + (error.response?.data?.detail || error.message));
    }
  };

  if (loading) {
    return <div className="p-6">加载中...</div>;
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      <PageHeader
        title="未决事项管理"
        breadcrumbs={[
          { label: "销售管理", path: "/sales" },
          {
            label: sourceType === "lead" ? "线索管理" : "商机管理",
            path:
              sourceType === "lead" ? "/sales/leads" : "/sales/opportunities",
          },
          { label: "未决事项", path: "" },
        ]}
      />

      <div className="mt-6">
        <Card className="bg-gray-800 border-gray-700">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>未决事项列表</CardTitle>
              <Button
                onClick={() => setShowCreateDialog(true)}
                className="bg-blue-600 hover:bg-blue-700"
              >
                <Plus className="w-4 h-4 mr-2" />
                新建未决事项
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {items.length === 0 ? (
              <div className="text-center py-8 text-gray-400">暂无未决事项</div>
            ) : (
              <div className="space-y-3">
                {items.map((item) => (
                  <div key={item.id} className="p-4 bg-gray-700 rounded-lg">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <Badge
                            className={
                              statusConfig[item.status]?.color || "bg-gray-500"
                            }
                          >
                            {statusConfig[item.status]?.label || item.status}
                          </Badge>
                          <Badge variant="outline">
                            {itemTypeConfig[item.item_type] || item.item_type}
                          </Badge>
                          {item.blocks_quotation && (
                            <Badge className="bg-red-500">阻塞报价</Badge>
                          )}
                        </div>
                        <div className="text-sm mb-2">{item.description}</div>
                        <div className="flex items-center gap-4 text-xs text-gray-400">
                          <span>责任方: {item.responsible_party}</span>
                          {item.responsible_person_name && (
                            <span>责任人: {item.responsible_person_name}</span>
                          )}
                          {item.due_date && (
                            <span>
                              截止日期:{" "}
                              {new Date(item.due_date).toLocaleDateString()}
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="flex gap-2">
                        {item.status !== "CLOSED" && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleClose(item.id)}
                          >
                            <CheckCircle2 className="w-4 h-4" />
                          </Button>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* 创建对话框 */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="bg-gray-800 border-gray-700 text-white">
          <DialogHeader>
            <DialogTitle>新建未决事项</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>问题类型</Label>
              <Select
                value={formData.item_type}
                onValueChange={(value) =>
                  setFormData({ ...formData, item_type: value })
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="选择问题类型" />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(itemTypeConfig).map(([key, label]) => (
                    <SelectItem key={key} value={key}>
                      {label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>问题描述</Label>
              <Textarea
                value={formData.description}
                onChange={(e) =>
                  setFormData({ ...formData, description: e.target.value })
                }
                placeholder="请输入问题描述"
                rows={4}
              />
            </div>
            <div>
              <Label>责任方</Label>
              <Input
                value={formData.responsible_party}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    responsible_party: e.target.value,
                  })
                }
                placeholder="客户/销售/售前/工程等"
              />
            </div>
            <div>
              <Label>截止日期</Label>
              <Input
                type="date"
                value={formData.due_date}
                onChange={(e) =>
                  setFormData({ ...formData, due_date: e.target.value })
                }
              />
            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="blocks_quotation"
                checked={formData.blocks_quotation}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    blocks_quotation: e.target.checked,
                  })
                }
              />
              <Label htmlFor="blocks_quotation">阻塞报价</Label>
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowCreateDialog(false)}
            >
              取消
            </Button>
            <Button
              onClick={handleCreate}
              className="bg-blue-600 hover:bg-blue-700"
            >
              创建
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
