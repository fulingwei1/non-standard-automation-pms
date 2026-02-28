/**
 * Requirement Freeze Management Page - 需求冻结管理页面
 * 管理线索和商机的需求冻结记录
 */

import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  Lock } from
"lucide-react";
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
  SelectValue } from
"../components/ui";
import { technicalAssessmentApi } from "../services/api";

const freezeTypeConfig = {
  SOLUTION: "方案冻结",
  INTERFACE: "接口冻结",
  ACCEPTANCE: "验收冻结",
  KEY_SELECTION: "关键选型冻结"
};

export default function RequirementFreezeManagement() {
  const { sourceType, sourceId } = useParams();
  const _navigate = useNavigate();

  const [freezes, setFreezes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [formData, setFormData] = useState({
    freeze_type: "",
    version_number: "",
    requires_ecr: true,
    description: ""
  });

  useEffect(() => {
    loadFreezes();
  }, [sourceType, sourceId]);

  const loadFreezes = async () => {
    try {
      setLoading(true);
      const response = await technicalAssessmentApi.getRequirementFreezes(
        sourceType,
        parseInt(sourceId)
      );
      setFreezes(response.data || []);
    } catch (error) {
      console.error("加载冻结记录失败:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    try {
      await technicalAssessmentApi.createRequirementFreeze(
        sourceType,
        parseInt(sourceId),
        formData
      );
      setShowCreateDialog(false);
      setFormData({
        freeze_type: "",
        version_number: "",
        requires_ecr: true,
        description: ""
      });
      await loadFreezes();
      alert("需求冻结记录已创建");
    } catch (error) {
      console.error("创建冻结记录失败:", error);
      alert("创建失败: " + (error.response?.data?.detail || error.message));
    }
  };

  if (loading) {
    return <div className="p-6">加载中...</div>;
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      <PageHeader
        title="需求冻结管理"
        breadcrumbs={[
        { label: "销售管理", path: "/sales" },
        {
          label: sourceType === "lead" ? "线索管理" : "商机管理",
          path:
          sourceType === "lead" ? "/sales/leads" : "/sales/opportunities"
        },
        { label: "需求冻结", path: "" }]
        } />


      <div className="mt-6">
        <Card className="bg-gray-800 border-gray-700">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>冻结记录列表</CardTitle>
              <Button
                onClick={() => setShowCreateDialog(true)}
                className="bg-blue-600 hover:bg-blue-700">

                <Lock className="w-4 h-4 mr-2" />
                创建冻结记录
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {freezes.length === 0 ?
            <div className="text-center py-8 text-gray-400">暂无冻结记录</div> :

            <div className="space-y-3">
                {freezes.map((freeze) =>
              <div key={freeze.id} className="p-4 bg-gray-700 rounded-lg">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <Badge className="bg-blue-500">
                            {freezeTypeConfig[freeze.freeze_type] ||
                        freeze.freeze_type}
                          </Badge>
                          <Badge variant="outline">
                            版本: {freeze.version_number}
                          </Badge>
                          {freeze.requires_ecr &&
                      <Badge className="bg-orange-500">需ECR/ECN</Badge>
                      }
                        </div>
                        {freeze.description &&
                    <div className="text-sm mb-2">
                            {freeze.description}
                    </div>
                    }
                        <div className="flex items-center gap-4 text-xs text-gray-400">
                          <span>
                            冻结时间:{" "}
                            {new Date(freeze.freeze_time).toLocaleString()}
                          </span>
                          {freeze.frozen_by_name &&
                      <span>冻结人: {freeze.frozen_by_name}</span>
                      }
                        </div>
                      </div>
                    </div>
              </div>
              )}
            </div>
            }
          </CardContent>
        </Card>
      </div>

      {/* 创建冻结对话框 */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="bg-gray-800 border-gray-700 text-white">
          <DialogHeader>
            <DialogTitle>创建需求冻结记录</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>冻结类型</Label>
              <Select
                value={formData.freeze_type}
                onValueChange={(value) =>
                setFormData({ ...formData, freeze_type: value })
                }>

                <SelectTrigger>
                  <SelectValue placeholder="选择冻结类型" />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(freezeTypeConfig).map(([key, label]) =>
                  <SelectItem key={key} value={key}>
                      {label}
                  </SelectItem>
                  )}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>版本号</Label>
              <Input
                value={formData.version_number}
                onChange={(e) =>
                setFormData({ ...formData, version_number: e.target.value })
                }
                placeholder="例如: v1.0" />

            </div>
            <div>
              <Label>冻结说明</Label>
              <Textarea
                value={formData.description}
                onChange={(e) =>
                setFormData({ ...formData, description: e.target.value })
                }
                placeholder="请输入冻结说明"
                rows={4} />

            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="requires_ecr"
                checked={formData.requires_ecr}
                onChange={(e) =>
                setFormData({ ...formData, requires_ecr: e.target.checked })
                } />

              <Label htmlFor="requires_ecr">冻结后变更必须走ECR/ECN</Label>
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowCreateDialog(false)}>

              取消
            </Button>
            <Button
              onClick={handleCreate}
              className="bg-blue-600 hover:bg-blue-700">

              创建
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>);

}