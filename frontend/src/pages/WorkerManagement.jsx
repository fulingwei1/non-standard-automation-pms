/**
 * Worker Management Page - 工人管理页面
 * Features: 工人列表、创建、编辑、技能管理
 */
import { useState, useEffect, useMemo } from "react";
import {
  Plus,
  Search,
  Eye,
  Edit,
} from "lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
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

export default function WorkerManagement() {
  const [loading, setLoading] = useState(true);
  const [workers, setWorkers] = useState([]);
  // Filters
  const [searchKeyword, setSearchKeyword] = useState("");
  // Dialogs
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [selectedWorker, setSelectedWorker] = useState(null);
  // Form state
  const [workerForm, setWorkerForm] = useState({
    worker_code: "",
    worker_name: "",
    workshop_id: null,
    phone: "",
    email: "",
    hire_date: "",
    skill_level: "JUNIOR",
    is_active: true,
  });

  useEffect(() => {
    fetchWorkers();
  }, [searchKeyword]);

  const fetchWorkers = async () => {
    try {
      setLoading(true);
      const params = { page: 1, page_size: 100 };
      if (searchKeyword) {params.search = searchKeyword;}
      const res = await productionApi.workers.list(params);
      const workerList = res.data?.items || res.data || [];
      setWorkers(workerList);
    } catch (error) {
      console.error("Failed to fetch workers:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    if (!workerForm.worker_code || !workerForm.worker_name) {
      alert("请填写工人编码和姓名");
      return;
    }
    try {
      await productionApi.workers.create(workerForm);
      setShowCreateDialog(false);
      resetForm();
      fetchWorkers();
    } catch (error) {
      console.error("Failed to create worker:", error);
      alert("创建工人失败: " + (error.response?.data?.detail || error.message));
    }
  };

  const handleEdit = async () => {
    if (!selectedWorker) {return;}
    try {
      await productionApi.workers.update(selectedWorker.id, workerForm);
      setShowEditDialog(false);
      resetForm();
      fetchWorkers();
    } catch (error) {
      console.error("Failed to update worker:", error);
      alert("更新工人失败: " + (error.response?.data?.detail || error.message));
    }
  };

  const handleViewDetail = async (workerId) => {
    try {
      const res = await productionApi.workers.get(workerId);
      setSelectedWorker(res.data || res);
      setShowDetailDialog(true);
    } catch (error) {
      console.error("Failed to fetch worker detail:", error);
    }
  };

  const handleEditClick = (worker) => {
    setSelectedWorker(worker);
    setWorkerForm({
      worker_code: worker.worker_code,
      worker_name: worker.worker_name,
      workshop_id: worker.workshop_id,
      phone: worker.phone || "",
      email: worker.email || "",
      hire_date: worker.hire_date || "",
      skill_level: worker.skill_level || "JUNIOR",
      is_active: worker.is_active !== false,
    });
    setShowEditDialog(true);
  };

  const resetForm = () => {
    setWorkerForm({
      worker_code: "",
      worker_name: "",
      workshop_id: null,
      phone: "",
      email: "",
      hire_date: "",
      skill_level: "JUNIOR",
      is_active: true,
    });
    setSelectedWorker(null);
  };

  const skillLevelConfigs = {
    EXPERT: { label: "专家", color: "bg-purple-500" },
    SENIOR: { label: "高级", color: "bg-blue-500" },
    INTERMEDIATE: { label: "中级", color: "bg-emerald-500" },
    JUNIOR: { label: "初级", color: "bg-amber-500" },
  };

  const filteredWorkers = useMemo(() => {
    return workers.filter((worker) => {
      if (searchKeyword) {
        const keyword = searchKeyword.toLowerCase();
        return (
          worker.worker_code?.toLowerCase().includes(keyword) ||
          worker.worker_name?.toLowerCase().includes(keyword) ||
          worker.phone?.toLowerCase().includes(keyword)
        );
      }
      return true;
    });
  }, [workers, searchKeyword]);

  return (
    <div className="space-y-6 p-6">
      <PageHeader
        title="工人管理"
        description="工人列表、创建、编辑、技能管理"
      />
      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
            <Input
              placeholder="搜索工人编码、姓名、电话..."
              value={searchKeyword}
              onChange={(e) => setSearchKeyword(e.target.value)}
              className="pl-10"
            />
          </div>
        </CardContent>
      </Card>
      {/* Action Bar */}
      <div className="flex justify-end">
        <Button onClick={() => setShowCreateDialog(true)}>
          <Plus className="w-4 h-4 mr-2" />
          新建工人
        </Button>
      </div>
      {/* Worker List */}
      <Card>
        <CardHeader>
          <CardTitle>工人列表</CardTitle>
          <CardDescription>共 {filteredWorkers.length} 个工人</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8 text-slate-400">加载中...</div>
          ) : filteredWorkers.length === 0 ? (
            <div className="text-center py-8 text-slate-400">暂无工人</div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>工人编码</TableHead>
                  <TableHead>姓名</TableHead>
                  <TableHead>车间</TableHead>
                  <TableHead>电话</TableHead>
                  <TableHead>技能等级</TableHead>
                  <TableHead>入职日期</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead className="text-right">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredWorkers.map((worker) => (
                  <TableRow key={worker.id}>
                    <TableCell className="font-mono text-sm">
                      {worker.worker_code}
                    </TableCell>
                    <TableCell className="font-medium">
                      {worker.worker_name}
                    </TableCell>
                    <TableCell>{worker.workshop_name || "-"}</TableCell>
                    <TableCell>{worker.phone || "-"}</TableCell>
                    <TableCell>
                      <Badge
                        className={
                          skillLevelConfigs[worker.skill_level]?.color ||
                          "bg-slate-500"
                        }
                      >
                        {skillLevelConfigs[worker.skill_level]?.label ||
                          worker.skill_level}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-slate-500 text-sm">
                      {worker.hire_date ? formatDate(worker.hire_date) : "-"}
                    </TableCell>
                    <TableCell>
                      {worker.is_active !== false ? (
                        <Badge className="bg-emerald-500">启用</Badge>
                      ) : (
                        <Badge className="bg-gray-500">停用</Badge>
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleViewDetail(worker.id)}
                        >
                          <Eye className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleEditClick(worker)}
                        >
                          <Edit className="w-4 h-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
      {/* Create Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>新建工人</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    工人编码 *
                  </label>
                  <Input
                    value={workerForm.worker_code}
                    onChange={(e) =>
                      setWorkerForm({
                        ...workerForm,
                        worker_code: e.target.value,
                      })
                    }
                    placeholder="请输入工人编码"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    姓名 *
                  </label>
                  <Input
                    value={workerForm.worker_name}
                    onChange={(e) =>
                      setWorkerForm({
                        ...workerForm,
                        worker_name: e.target.value,
                      })
                    }
                    placeholder="请输入姓名"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">电话</label>
                  <Input
                    value={workerForm.phone}
                    onChange={(e) =>
                      setWorkerForm({ ...workerForm, phone: e.target.value })
                    }
                    placeholder="联系电话"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">邮箱</label>
                  <Input
                    type="email"
                    value={workerForm.email}
                    onChange={(e) =>
                      setWorkerForm({ ...workerForm, email: e.target.value })
                    }
                    placeholder="邮箱地址"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    技能等级
                  </label>
                  <Select
                    value={workerForm.skill_level}
                    onValueChange={(val) =>
                      setWorkerForm({ ...workerForm, skill_level: val })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {Object.entries(skillLevelConfigs).map(
                        ([key, config]) => (
                          <SelectItem key={key} value={key}>
                            {config.label}
                          </SelectItem>
                        ),
                      )}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    入职日期
                  </label>
                  <Input
                    type="date"
                    value={workerForm.hire_date}
                    onChange={(e) =>
                      setWorkerForm({
                        ...workerForm,
                        hire_date: e.target.value,
                      })
                    }
                  />
                </div>
              </div>
            </div>
          </DialogBody>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowCreateDialog(false)}
            >
              取消
            </Button>
            <Button onClick={handleCreate}>创建</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      {/* Edit Dialog */}
      <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>编辑工人</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    工人编码 *
                  </label>
                  <Input
                    value={workerForm.worker_code}
                    onChange={(e) =>
                      setWorkerForm({
                        ...workerForm,
                        worker_code: e.target.value,
                      })
                    }
                    placeholder="请输入工人编码"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    姓名 *
                  </label>
                  <Input
                    value={workerForm.worker_name}
                    onChange={(e) =>
                      setWorkerForm({
                        ...workerForm,
                        worker_name: e.target.value,
                      })
                    }
                    placeholder="请输入姓名"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">电话</label>
                  <Input
                    value={workerForm.phone}
                    onChange={(e) =>
                      setWorkerForm({ ...workerForm, phone: e.target.value })
                    }
                    placeholder="联系电话"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">邮箱</label>
                  <Input
                    type="email"
                    value={workerForm.email}
                    onChange={(e) =>
                      setWorkerForm({ ...workerForm, email: e.target.value })
                    }
                    placeholder="邮箱地址"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    技能等级
                  </label>
                  <Select
                    value={workerForm.skill_level}
                    onValueChange={(val) =>
                      setWorkerForm({ ...workerForm, skill_level: val })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {Object.entries(skillLevelConfigs).map(
                        ([key, config]) => (
                          <SelectItem key={key} value={key}>
                            {config.label}
                          </SelectItem>
                        ),
                      )}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    入职日期
                  </label>
                  <Input
                    type="date"
                    value={workerForm.hire_date}
                    onChange={(e) =>
                      setWorkerForm({
                        ...workerForm,
                        hire_date: e.target.value,
                      })
                    }
                  />
                </div>
              </div>
              <div>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={workerForm.is_active}
                    onChange={(e) =>
                      setWorkerForm({
                        ...workerForm,
                        is_active: e.target.checked,
                      })
                    }
                  />
                  <span className="text-sm">启用</span>
                </label>
              </div>
            </div>
          </DialogBody>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowEditDialog(false)}>
              取消
            </Button>
            <Button onClick={handleEdit}>保存</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      {/* Detail Dialog */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="max-w-4xl">
          <DialogHeader>
            <DialogTitle>{selectedWorker?.worker_name} - 工人详情</DialogTitle>
          </DialogHeader>
          <DialogBody>
            {selectedWorker && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-sm text-slate-500 mb-1">工人编码</div>
                    <div className="font-mono">
                      {selectedWorker.worker_code}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">姓名</div>
                    <div>{selectedWorker.worker_name}</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">车间</div>
                    <div>{selectedWorker.workshop_name || "-"}</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">电话</div>
                    <div>{selectedWorker.phone || "-"}</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">邮箱</div>
                    <div>{selectedWorker.email || "-"}</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">技能等级</div>
                    <Badge
                      className={
                        skillLevelConfigs[selectedWorker.skill_level]?.color
                      }
                    >
                      {skillLevelConfigs[selectedWorker.skill_level]?.label}
                    </Badge>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">入职日期</div>
                    <div>
                      {selectedWorker.hire_date
                        ? formatDate(selectedWorker.hire_date)
                        : "-"}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">状态</div>
                    {selectedWorker.is_active !== false ? (
                      <Badge className="bg-emerald-500">启用</Badge>
                    ) : (
                      <Badge className="bg-gray-500">停用</Badge>
                    )}
                  </div>
                </div>
              </div>
            )}
          </DialogBody>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowDetailDialog(false)}
            >
              关闭
            </Button>
            {selectedWorker && (
              <Button
                onClick={() => {
                  setShowDetailDialog(false);
                  handleEditClick(selectedWorker);
                }}
              >
                <Edit className="w-4 h-4 mr-2" />
                编辑
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
