/**
 * Material Requisition Detail Page - 领料单详情页面
 * Features: 领料单详情、审批、发料
 */
import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  Package,
  CheckCircle2,
  XCircle,
  RefreshCw,
  FileText,
} from "lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter,
} from "../components/ui/dialog";
import { formatDate } from "../lib/utils";
import { productionApi } from "../services/api";

const statusConfigs = {
  PENDING: { label: "待审批", color: "bg-blue-500" },
  APPROVED: { label: "已批准", color: "bg-emerald-500" },
  REJECTED: { label: "已驳回", color: "bg-red-500" },
  ISSUED: { label: "已发料", color: "bg-violet-500" },
  CANCELLED: { label: "已取消", color: "bg-gray-500" },
};

export default function MaterialRequisitionDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [requisition, setRequisition] = useState(null);
  const [items, setItems] = useState([]);
  // Dialogs
  const [showApproveDialog, setShowApproveDialog] = useState(false);
  const [showIssueDialog, setShowIssueDialog] = useState(false);
  // Form states
  const [approveData, setApproveData] = useState({
    approved_qty: {},
    approve_comment: "",
  });
  const [issueData, setIssueData] = useState({
    issued_qty: {},
    issue_comment: "",
  });

  useEffect(() => {
    if (id) {
      fetchRequisition();
      fetchItems();
    }
  }, [id]);

  const fetchRequisition = async () => {
    try {
      setLoading(true);
      const res = await productionApi.materialRequisitions.get(id);
      setRequisition(res.data || res);
    } catch (error) {
      console.error("Failed to fetch requisition:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchItems = async () => {
    try {
      // Assuming there's a getItems endpoint, otherwise use the items from requisition
      if (requisition && requisition.items) {
        setItems(requisition.items);
      }
    } catch (error) {
      console.error("Failed to fetch items:", error);
    }
  };

  const handleApprove = async () => {
    if (!requisition) {return;}
    try {
      await productionApi.materialRequisitions.approve(
        requisition.id,
        approveData,
      );
      setShowApproveDialog(false);
      setApproveData({
        approved_qty: {},
        approve_comment: "",
      });
      fetchRequisition();
    } catch (error) {
      console.error("Failed to approve requisition:", error);
      alert("审批失败: " + (error.response?.data?.detail || error.message));
    }
  };

  const handleIssue = async () => {
    if (!requisition) {return;}
    try {
      await productionApi.materialRequisitions.issue(requisition.id, issueData);
      setShowIssueDialog(false);
      setIssueData({
        issued_qty: {},
        issue_comment: "",
      });
      fetchRequisition();
    } catch (error) {
      console.error("Failed to issue requisition:", error);
      alert("发料失败: " + (error.response?.data?.detail || error.message));
    }
  };

  if (loading) {
    return (
      <div className="space-y-6 p-6">
        <div className="text-center py-8 text-slate-400">加载中...</div>
      </div>
    );
  }

  if (!requisition) {
    return (
      <div className="space-y-6 p-6">
        <div className="text-center py-8 text-slate-400">领料单不存在</div>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate("/material-requisitions")}
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            返回列表
          </Button>
          <PageHeader
            title={`领料单详情 - ${requisition.requisition_no}`}
            description="领料单详情、审批、发料"
          />
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            onClick={() => {
              fetchRequisition();
              fetchItems();
            }}
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            刷新
          </Button>
          {requisition.status === "PENDING" && (
            <Button onClick={() => setShowApproveDialog(true)}>
              <CheckCircle2 className="w-4 h-4 mr-2" />
              审批
            </Button>
          )}
          {requisition.status === "APPROVED" && (
            <Button onClick={() => setShowIssueDialog(true)}>
              <Package className="w-4 h-4 mr-2" />
              发料
            </Button>
          )}
        </div>
      </div>
      {/* Requisition Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-500 mb-1">领料单号</div>
                <div className="font-mono text-sm">
                  {requisition.requisition_no}
                </div>
              </div>
              <FileText className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-500 mb-1">状态</div>
                <Badge
                  className={
                    statusConfigs[requisition.status]?.color || "bg-slate-500"
                  }
                >
                  {statusConfigs[requisition.status]?.label ||
                    requisition.status}
                </Badge>
              </div>
              <CheckCircle2 className="w-8 h-8 text-emerald-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-500 mb-1">项目</div>
                <div className="font-medium">
                  {requisition.project_name || "-"}
                </div>
              </div>
              <Package className="w-8 h-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-500 mb-1">申请时间</div>
                <div className="text-sm">
                  {requisition.apply_time
                    ? formatDate(requisition.apply_time)
                    : "-"}
                </div>
              </div>
              <RefreshCw className="w-8 h-8 text-amber-500" />
            </div>
          </CardContent>
        </Card>
      </div>
      {/* Requisition Info */}
      <Card>
        <CardHeader>
          <CardTitle>领料单信息</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-sm text-slate-500 mb-1">工单号</div>
              <div className="font-mono">
                {requisition.work_order_no || "-"}
              </div>
            </div>
            <div>
              <div className="text-sm text-slate-500 mb-1">申请人</div>
              <div>{requisition.applicant_name || "-"}</div>
            </div>
            <div>
              <div className="text-sm text-slate-500 mb-1">申请原因</div>
              <div>{requisition.apply_reason || "-"}</div>
            </div>
            {requisition.approve_comment && (
              <div>
                <div className="text-sm text-slate-500 mb-1">审批意见</div>
                <div>{requisition.approve_comment}</div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
      {/* Items List */}
      <Card>
        <CardHeader>
          <CardTitle>物料清单</CardTitle>
        </CardHeader>
        <CardContent>
          {items.length === 0 ? (
            <div className="text-center py-8 text-slate-400">暂无物料</div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>物料编码</TableHead>
                  <TableHead>物料名称</TableHead>
                  <TableHead>规格</TableHead>
                  <TableHead>申请数量</TableHead>
                  <TableHead>批准数量</TableHead>
                  <TableHead>发料数量</TableHead>
                  <TableHead>单位</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {items.map((item) => (
                  <TableRow key={item.id}>
                    <TableCell className="font-mono text-sm">
                      {item.material_code || "-"}
                    </TableCell>
                    <TableCell className="font-medium">
                      {item.material_name || "-"}
                    </TableCell>
                    <TableCell>{item.specification || "-"}</TableCell>
                    <TableCell className="font-medium">
                      {item.apply_qty || 0}
                    </TableCell>
                    <TableCell className="text-emerald-600 font-medium">
                      {item.approved_qty || 0}
                    </TableCell>
                    <TableCell className="text-violet-600 font-medium">
                      {item.issued_qty || 0}
                    </TableCell>
                    <TableCell>{item.unit || "-"}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
      {/* Approve Dialog */}
      <Dialog open={showApproveDialog} onOpenChange={setShowApproveDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>审批领料单</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <div className="space-y-4">
              {items.map((item) => (
                <div key={item.id} className="border rounded-lg p-3">
                  <div className="font-medium mb-2">{item.material_name}</div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <div className="text-sm text-slate-500 mb-1">
                        申请数量
                      </div>
                      <div>
                        {item.apply_qty || 0} {item.unit || ""}
                      </div>
                    </div>
                    <div>
                      <label className="text-sm font-medium mb-2 block">
                        批准数量
                      </label>
                      <Input
                        type="number"
                        value={
                          approveData.approved_qty[item.id] ||
                          item.apply_qty ||
                          0
                        }
                        onChange={(e) =>
                          setApproveData({
                            ...approveData,
                            approved_qty: {
                              ...approveData.approved_qty,
                              [item.id]: parseFloat(e.target.value) || 0,
                            },
                          })
                        }
                      />
                    </div>
                  </div>
                </div>
              ))}
              <div>
                <label className="text-sm font-medium mb-2 block">
                  审批意见
                </label>
                <textarea
                  className="w-full min-h-[80px] p-3 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={approveData.approve_comment}
                  onChange={(e) =>
                    setApproveData({
                      ...approveData,
                      approve_comment: e.target.value,
                    })
                  }
                  placeholder="审批意见..."
                />
              </div>
            </div>
          </DialogBody>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowApproveDialog(false)}
            >
              取消
            </Button>
            <Button onClick={handleApprove}>审批通过</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      {/* Issue Dialog */}
      <Dialog open={showIssueDialog} onOpenChange={setShowIssueDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>发料</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <div className="space-y-4">
              {items.map((item) => (
                <div key={item.id} className="border rounded-lg p-3">
                  <div className="font-medium mb-2">{item.material_name}</div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <div className="text-sm text-slate-500 mb-1">
                        批准数量
                      </div>
                      <div>
                        {item.approved_qty || 0} {item.unit || ""}
                      </div>
                    </div>
                    <div>
                      <label className="text-sm font-medium mb-2 block">
                        发料数量
                      </label>
                      <Input
                        type="number"
                        value={
                          issueData.issued_qty[item.id] ||
                          item.approved_qty ||
                          0
                        }
                        onChange={(e) =>
                          setIssueData({
                            ...issueData,
                            issued_qty: {
                              ...issueData.issued_qty,
                              [item.id]: parseFloat(e.target.value) || 0,
                            },
                          })
                        }
                      />
                    </div>
                  </div>
                </div>
              ))}
              <div>
                <label className="text-sm font-medium mb-2 block">
                  发料说明
                </label>
                <textarea
                  className="w-full min-h-[80px] p-3 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={issueData.issue_comment}
                  onChange={(e) =>
                    setIssueData({
                      ...issueData,
                      issue_comment: e.target.value,
                    })
                  }
                  placeholder="发料说明..."
                />
              </div>
            </div>
          </DialogBody>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowIssueDialog(false)}>
              取消
            </Button>
            <Button onClick={handleIssue}>确认发料</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
