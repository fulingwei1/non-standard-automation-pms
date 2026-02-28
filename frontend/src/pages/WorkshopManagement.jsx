/**
 * Workshop Management Page - 车间管理页面
 * Features: 车间列表、创建、编辑、工位管理
 */
import { useState, useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import {
  Plus,
  Search,
  Eye,
  Edit,
  Wrench,
  CheckCircle2,
  XCircle } from
"lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription } from
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
import { productionApi, userApi } from "../services/api";

const typeConfigs = {
  MACHINING: { label: "机加车间", color: "bg-blue-500" },
  ASSEMBLY: { label: "装配车间", color: "bg-purple-500" },
  DEBUGGING: { label: "调试车间", color: "bg-emerald-500" }
};

export default function WorkshopManagement() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [workshops, setWorkshops] = useState([]);
  const [managers, setManagers] = useState([]);
  // Filters
  const [searchKeyword, setSearchKeyword] = useState("");
  const [filterType, setFilterType] = useState("");
  const [filterActive, setFilterActive] = useState("");
  // Dialogs
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [selectedWorkshop, setSelectedWorkshop] = useState(null);
  // Form state
  const [workshopForm, setWorkshopForm] = useState({
    workshop_code: "",
    workshop_name: "",
    workshop_type: "MACHINING",
    manager_id: null,
    location: "",
    capacity_hours: 0,
    description: "",
    is_active: true
  });

  useEffect(() => {
    fetchManagers();
    fetchWorkshops();
  }, [filterType, filterActive, searchKeyword]);

  const fetchManagers = async () => {
    try {
      const res = await userApi.list({ page_size: 1000 });
      setManagers(res.data?.items || res.data || []);
    } catch (error) {
      console.error("Failed to fetch managers:", error);
    }
  };

  const fetchWorkshops = async () => {
    try {
      setLoading(true);
      const params = { page: 1, page_size: 100 };
      if (filterType) {params.workshop_type = filterType;}
      if (filterActive !== "") {params.is_active = filterActive === "true";}
      if (searchKeyword) {params.search = searchKeyword;}
      const res = await productionApi.workshops.list(params);
      const workshopList = res.data?.items || res.data || [];
      setWorkshops(workshopList);
    } catch (error) {
      console.error("Failed to fetch workshops:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    if (!workshopForm.workshop_code || !workshopForm.workshop_name) {
      alert("请填写车间编码和名称");
      return;
    }
    try {
      await productionApi.workshops.create(workshopForm);
      setShowCreateDialog(false);
      resetForm();
      fetchWorkshops();
    } catch (error) {
      console.error("Failed to create workshop:", error);
      alert("创建车间失败: " + (error.response?.data?.detail || error.message));
    }
  };

  const handleEdit = async () => {
    if (!selectedWorkshop) {return;}
    try {
      await productionApi.workshops.update(selectedWorkshop.id, workshopForm);
      setShowEditDialog(false);
      resetForm();
      fetchWorkshops();
    } catch (error) {
      console.error("Failed to update workshop:", error);
      alert("更新车间失败: " + (error.response?.data?.detail || error.message));
    }
  };

  const handleViewDetail = async (workshopId) => {
    try {
      const res = await productionApi.workshops.get(workshopId);
      setSelectedWorkshop(res.data || res);
      setShowDetailDialog(true);
    } catch (error) {
      console.error("Failed to fetch workshop detail:", error);
    }
  };

  const handleEditClick = (workshop) => {
    setSelectedWorkshop(workshop);
    setWorkshopForm({
      workshop_code: workshop.workshop_code,
      workshop_name: workshop.workshop_name,
      workshop_type: workshop.workshop_type,
      manager_id: workshop.manager_id,
      location: workshop.location || "",
      capacity_hours: workshop.capacity_hours || 0,
      description: workshop.description || "",
      is_active: workshop.is_active !== false
    });
    setShowEditDialog(true);
  };

  const resetForm = () => {
    setWorkshopForm({
      workshop_code: "",
      workshop_name: "",
      workshop_type: "MACHINING",
      manager_id: null,
      location: "",
      capacity_hours: 0,
      description: "",
      is_active: true
    });
    setSelectedWorkshop(null);
  };

  const filteredWorkshops = useMemo(() => {
    return workshops.filter((ws) => {
      if (searchKeyword) {
        const keyword = searchKeyword.toLowerCase();
        return (
          ws.workshop_code?.toLowerCase().includes(keyword) ||
          ws.workshop_name?.toLowerCase().includes(keyword));

      }
      return true;
    });
  }, [workshops, searchKeyword]);

  return (
    <div className="space-y-6 p-6">
      <PageHeader
        title="车间管理"
        description="车间列表、创建、编辑、工位管理" />

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
              <Input
                placeholder="搜索车间编码、名称..."
                value={searchKeyword}
                onChange={(e) => setSearchKeyword(e.target.value)}
                className="pl-10" />

            </div>
            <Select value={filterType} onValueChange={setFilterType}>
              <SelectTrigger>
                <SelectValue placeholder="选择类型" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部类型</SelectItem>
                {Object.entries(typeConfigs).map(([key, config]) =>
                <SelectItem key={key} value={key}>
                    {config.label}
                </SelectItem>
                )}
              </SelectContent>
            </Select>
            <Select value={filterActive} onValueChange={setFilterActive}>
              <SelectTrigger>
                <SelectValue placeholder="选择状态" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部状态</SelectItem>
                <SelectItem value="true">启用</SelectItem>
                <SelectItem value="false">停用</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>
      {/* Action Bar */}
      <div className="flex justify-end">
        <Button onClick={() => setShowCreateDialog(true)}>
          <Plus className="w-4 h-4 mr-2" />
          新建车间
        </Button>
      </div>
      {/* Workshop List */}
      <Card>
        <CardHeader>
          <CardTitle>车间列表</CardTitle>
          <CardDescription>
            共 {filteredWorkshops.length} 个车间
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ?
          <div className="text-center py-8 text-slate-400">加载中...</div> :
          filteredWorkshops.length === 0 ?
          <div className="text-center py-8 text-slate-400">暂无车间</div> :

          <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>车间编码</TableHead>
                  <TableHead>车间名称</TableHead>
                  <TableHead>类型</TableHead>
                  <TableHead>主管</TableHead>
                  <TableHead>位置</TableHead>
                  <TableHead>产能（小时）</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead className="text-right">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredWorkshops.map((workshop) =>
              <TableRow key={workshop.id}>
                    <TableCell className="font-mono text-sm">
                      {workshop.workshop_code}
                    </TableCell>
                    <TableCell className="font-medium">
                      {workshop.workshop_name}
                    </TableCell>
                    <TableCell>
                      <Badge
                    className={
                    typeConfigs[workshop.workshop_type]?.color ||
                    "bg-slate-500"
                    }>

                        {typeConfigs[workshop.workshop_type]?.label ||
                    workshop.workshop_type}
                      </Badge>
                    </TableCell>
                    <TableCell>{workshop.manager_name || "-"}</TableCell>
                    <TableCell>{workshop.location || "-"}</TableCell>
                    <TableCell>{workshop.capacity_hours || 0}</TableCell>
                    <TableCell>
                      {workshop.is_active !== false ?
                  <Badge className="bg-emerald-500">
                          <CheckCircle2 className="w-3 h-3 mr-1" />
                          启用
                  </Badge> :

                  <Badge className="bg-gray-500">
                          <XCircle className="w-3 h-3 mr-1" />
                          停用
                  </Badge>
                  }
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleViewDetail(workshop.id)}>

                          <Eye className="w-4 h-4" />
                        </Button>
                        <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleEditClick(workshop)}>

                          <Edit className="w-4 h-4" />
                        </Button>
                        <Button
                      variant="ghost"
                      size="sm"
                      onClick={() =>
                      navigate(`/workshops/${workshop.id}/task-board`)
                      }>

                          <Wrench className="w-4 h-4" />
                        </Button>
                      </div>
                    </TableCell>
              </TableRow>
              )}
              </TableBody>
          </Table>
          }
        </CardContent>
      </Card>
      {/* Create Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>新建车间</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    车间编码 *
                  </label>
                  <Input
                    value={workshopForm.workshop_code}
                    onChange={(e) =>
                    setWorkshopForm({
                      ...workshopForm,
                      workshop_code: e.target.value
                    })
                    }
                    placeholder="请输入车间编码" />

                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    车间名称 *
                  </label>
                  <Input
                    value={workshopForm.workshop_name}
                    onChange={(e) =>
                    setWorkshopForm({
                      ...workshopForm,
                      workshop_name: e.target.value
                    })
                    }
                    placeholder="请输入车间名称" />

                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    车间类型
                  </label>
                  <Select
                    value={workshopForm.workshop_type}
                    onValueChange={(val) =>
                    setWorkshopForm({ ...workshopForm, workshop_type: val })
                    }>

                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {Object.entries(typeConfigs).map(([key, config]) =>
                      <SelectItem key={key} value={key}>
                          {config.label}
                      </SelectItem>
                      )}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    车间主管
                  </label>
                  <Select
                    value={workshopForm.manager_id?.toString() || ""}
                    onValueChange={(val) =>
                    setWorkshopForm({
                      ...workshopForm,
                      manager_id: val ? parseInt(val) : null
                    })
                    }>

                    <SelectTrigger>
                      <SelectValue placeholder="选择主管" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">无</SelectItem>
                      {managers.map((mgr) =>
                      <SelectItem key={mgr.id} value={mgr.id.toString()}>
                          {mgr.real_name || mgr.username}
                      </SelectItem>
                      )}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">位置</label>
                  <Input
                    value={workshopForm.location}
                    onChange={(e) =>
                    setWorkshopForm({
                      ...workshopForm,
                      location: e.target.value
                    })
                    }
                    placeholder="车间位置" />

                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    产能（小时）
                  </label>
                  <Input
                    type="number"
                    value={workshopForm.capacity_hours}
                    onChange={(e) =>
                    setWorkshopForm({
                      ...workshopForm,
                      capacity_hours: parseFloat(e.target.value) || 0
                    })
                    }
                    placeholder="0" />

                </div>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">描述</label>
                <textarea
                  className="w-full min-h-[80px] p-3 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={workshopForm.description}
                  onChange={(e) =>
                  setWorkshopForm({
                    ...workshopForm,
                    description: e.target.value
                  })
                  }
                  placeholder="车间描述..." />

              </div>
            </div>
          </DialogBody>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowCreateDialog(false)}>

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
            <DialogTitle>编辑车间</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    车间编码 *
                  </label>
                  <Input
                    value={workshopForm.workshop_code}
                    onChange={(e) =>
                    setWorkshopForm({
                      ...workshopForm,
                      workshop_code: e.target.value
                    })
                    }
                    placeholder="请输入车间编码" />

                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    车间名称 *
                  </label>
                  <Input
                    value={workshopForm.workshop_name}
                    onChange={(e) =>
                    setWorkshopForm({
                      ...workshopForm,
                      workshop_name: e.target.value
                    })
                    }
                    placeholder="请输入车间名称" />

                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    车间类型
                  </label>
                  <Select
                    value={workshopForm.workshop_type}
                    onValueChange={(val) =>
                    setWorkshopForm({ ...workshopForm, workshop_type: val })
                    }>

                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {Object.entries(typeConfigs).map(([key, config]) =>
                      <SelectItem key={key} value={key}>
                          {config.label}
                      </SelectItem>
                      )}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    车间主管
                  </label>
                  <Select
                    value={workshopForm.manager_id?.toString() || ""}
                    onValueChange={(val) =>
                    setWorkshopForm({
                      ...workshopForm,
                      manager_id: val ? parseInt(val) : null
                    })
                    }>

                    <SelectTrigger>
                      <SelectValue placeholder="选择主管" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">无</SelectItem>
                      {managers.map((mgr) =>
                      <SelectItem key={mgr.id} value={mgr.id.toString()}>
                          {mgr.real_name || mgr.username}
                      </SelectItem>
                      )}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">位置</label>
                  <Input
                    value={workshopForm.location}
                    onChange={(e) =>
                    setWorkshopForm({
                      ...workshopForm,
                      location: e.target.value
                    })
                    }
                    placeholder="车间位置" />

                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    产能（小时）
                  </label>
                  <Input
                    type="number"
                    value={workshopForm.capacity_hours}
                    onChange={(e) =>
                    setWorkshopForm({
                      ...workshopForm,
                      capacity_hours: parseFloat(e.target.value) || 0
                    })
                    }
                    placeholder="0" />

                </div>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">描述</label>
                <textarea
                  className="w-full min-h-[80px] p-3 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={workshopForm.description}
                  onChange={(e) =>
                  setWorkshopForm({
                    ...workshopForm,
                    description: e.target.value
                  })
                  }
                  placeholder="车间描述..." />

              </div>
              <div>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={workshopForm.is_active}
                    onChange={(e) =>
                    setWorkshopForm({
                      ...workshopForm,
                      is_active: e.target.checked
                    })
                    } />

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
            <DialogTitle>
              {selectedWorkshop?.workshop_name} - 车间详情
            </DialogTitle>
          </DialogHeader>
          <DialogBody>
            {selectedWorkshop &&
            <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-sm text-slate-500 mb-1">车间编码</div>
                    <div className="font-mono">
                      {selectedWorkshop.workshop_code}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">车间名称</div>
                    <div>{selectedWorkshop.workshop_name}</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">车间类型</div>
                    <Badge
                    className={
                    typeConfigs[selectedWorkshop.workshop_type]?.color
                    }>

                      {typeConfigs[selectedWorkshop.workshop_type]?.label}
                    </Badge>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">车间主管</div>
                    <div>{selectedWorkshop.manager_name || "-"}</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">位置</div>
                    <div>{selectedWorkshop.location || "-"}</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">
                      产能（小时）
                    </div>
                    <div>{selectedWorkshop.capacity_hours || 0}</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">状态</div>
                    {selectedWorkshop.is_active !== false ?
                  <Badge className="bg-emerald-500">启用</Badge> :

                  <Badge className="bg-gray-500">停用</Badge>
                  }
                  </div>
                </div>
                {selectedWorkshop.description &&
              <div>
                    <div className="text-sm text-slate-500 mb-1">描述</div>
                    <div>{selectedWorkshop.description}</div>
              </div>
              }
            </div>
            }
          </DialogBody>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowDetailDialog(false)}>

              关闭
            </Button>
            {selectedWorkshop &&
            <Button
              onClick={() => {
                setShowDetailDialog(false);
                handleEditClick(selectedWorkshop);
              }}>

                <Edit className="w-4 h-4 mr-2" />
                编辑
            </Button>
            }
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>);

}