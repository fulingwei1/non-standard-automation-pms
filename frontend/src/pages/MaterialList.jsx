/**
 * Material List Page - 物料列表页面
 * Features: 物料主数据管理，支持分类筛选、供应商关联、搜索
 */
import { useState, useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import {
  Package,
  Plus,
  Search,
  Filter,
  Edit,
  Trash2,
  Eye,
  Building2,
  Tag,
  DollarSign,
  Box,
  AlertCircle } from
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
import { ApiIntegrationError } from "../components/ui";
import { cn as _cn, formatCurrency } from "../lib/utils";
import { fadeIn as _fadeIn } from "../lib/animations";
import { materialApi, supplierApi } from "../services/api";
export default function MaterialList() {
  const _navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [materials, setMaterials] = useState(null);
  const [categories, setCategories] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  // Filters
  const [searchKeyword, setSearchKeyword] = useState("");
  const [filterCategory, setFilterCategory] = useState("all");
  const [filterSupplier, setFilterSupplier] = useState("all");
  // Dialogs
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [selectedMaterial, setSelectedMaterial] = useState(null);
  // Form state
  const [newMaterial, setNewMaterial] = useState({
    material_code: "",
    material_name: "",
    specification: "",
    category_id: null,
    unit: "PCS",
    unit_price: 0,
    supplier_id: null,
    remark: ""
  });
  useEffect(() => {
    fetchMaterials();
    fetchCategories();
    fetchSuppliers();
  }, [filterCategory, filterSupplier]);
  const fetchMaterials = async () => {
    try {
      setLoading(true);
      setError(null);
      const params = {};
      if (filterCategory && filterCategory !== "all")
      {params.category_id = filterCategory;}
      if (filterSupplier && filterSupplier !== "all")
      {params.supplier_id = filterSupplier;}
      if (searchKeyword) {params.search = searchKeyword;}
      const res = await materialApi.list(params);
      // 使用统一响应格式处理
      const paginatedData = res.formatted || res.data;
      const materialList = paginatedData?.items || paginatedData || [];
      setMaterials(materialList);
    } catch (error) {
      console.error("物料列表 API 调用失败:", error);
      setError(error);
      setMaterials(null); // 清空数据
    } finally {
      setLoading(false);
    }
  };
  const fetchCategories = async () => {
    try {
      const res = await materialApi.categories.list();
      // 使用统一响应格式处理
      const listData = res.formatted || res.data;
      setCategories(listData?.items || listData || []);
    } catch (error) {
      console.error("物料分类 API 调用失败:", error);
      // 分类失败不影响主数据加载，只记录错误
      setCategories([]);
    }
  };
  const fetchSuppliers = async () => {
    try {
      const res = await supplierApi.list({ page_size: 1000 });
      // 使用统一响应格式处理
      const paginatedData = res.formatted || res.data;
      setSuppliers(paginatedData?.items || paginatedData || []);
    } catch (error) {
      console.error("供应商 API 调用失败:", error);
      // 供应商失败不影响主数据加载，只记录错误
      setSuppliers([]);
    }
  };
  const handleCreateMaterial = async () => {
    if (!newMaterial.material_code || !newMaterial.material_name) {
      alert("请填写物料编码和物料名称");
      return;
    }
    try {
      await materialApi.create(newMaterial);
      setShowCreateDialog(false);
      setNewMaterial({
        material_code: "",
        material_name: "",
        specification: "",
        category_id: null,
        unit: "PCS",
        unit_price: 0,
        supplier_id: null,
        remark: ""
      });
      fetchMaterials();
    } catch (error) {
      console.error("Failed to create material:", error);
      alert("创建物料失败: " + (error.response?.data?.detail || error.message));
    }
  };
  const handleViewDetail = async (materialId) => {
    try {
      const res = await materialApi.get(materialId);
      // 使用统一响应格式处理
      setSelectedMaterial(res.formatted || res.data || res);
      setShowDetailDialog(true);
    } catch (error) {
      console.error("Failed to fetch material detail:", error);
    }
  };
  const filteredMaterials = useMemo(() => {
    if (!materials || materials.length === 0) {return [];}

    return materials.filter((material) => {
      if (searchKeyword) {
        const keyword = searchKeyword.toLowerCase();
        return (
          material.material_code?.toLowerCase().includes(keyword) ||
          material.material_name?.toLowerCase().includes(keyword) ||
          material.specification?.toLowerCase().includes(keyword));

      }
      return true;
    });
  }, [materials, searchKeyword]);

  // 如果有错误，显示错误组件
  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <div className="container mx-auto px-4 py-6 space-y-6">
          <PageHeader
            title="物料管理"
            description="物料主数据管理，支持分类、供应商关联、价格管理" />

          <ApiIntegrationError
            error={error}
            apiEndpoint="/api/v1/materials"
            onRetry={fetchMaterials} />

        </div>
      </div>);

  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="container mx-auto px-4 py-6 space-y-6">
        <PageHeader
          title="物料管理"
          description="物料主数据管理，支持分类、供应商关联、价格管理" />

        {/* Filters */}
        <Card className="bg-slate-800/50 border-slate-700/50">
          <CardContent className="pt-6">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
                <Input
                  placeholder="搜索物料编码、名称..."
                  value={searchKeyword}
                  onChange={(e) => setSearchKeyword(e.target.value)}
                  className="pl-10" />

              </div>
              <Select value={filterCategory} onValueChange={setFilterCategory}>
                <SelectTrigger>
                  <SelectValue placeholder="选择分类" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部分类</SelectItem>
                  {categories.map((cat) =>
                  <SelectItem key={cat.id} value={cat.id.toString()}>
                      {cat.name}
                  </SelectItem>
                  )}
                </SelectContent>
              </Select>
              <Select value={filterSupplier} onValueChange={setFilterSupplier}>
                <SelectTrigger>
                  <SelectValue placeholder="选择供应商" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部供应商</SelectItem>
                  {suppliers.map((supplier) =>
                  <SelectItem
                    key={supplier.id}
                    value={supplier.id.toString()}>

                      {supplier.name}
                  </SelectItem>
                  )}
                </SelectContent>
              </Select>
              <Button onClick={() => setShowCreateDialog(true)}>
                <Plus className="w-4 h-4 mr-2" />
                新建物料
              </Button>
            </div>
          </CardContent>
        </Card>
        {/* Material List */}
        <Card className="bg-slate-800/50 border-slate-700/50">
          <CardHeader>
            <CardTitle className="text-slate-200">物料列表</CardTitle>
            <CardDescription className="text-slate-400">
              共 {filteredMaterials.length} 个物料
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loading ?
            <div className="text-center py-8 text-slate-400">加载中...</div> :
            !materials ?
            <div className="text-center py-8 text-slate-400">暂无数据</div> :
            filteredMaterials.length === 0 ?
            <div className="text-center py-8 text-slate-400">
                暂无物料数据
            </div> :

            <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>物料编码</TableHead>
                    <TableHead>物料名称</TableHead>
                    <TableHead>规格</TableHead>
                    <TableHead>分类</TableHead>
                    <TableHead>单位</TableHead>
                    <TableHead>单价</TableHead>
                    <TableHead>供应商</TableHead>
                    <TableHead className="text-right">操作</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredMaterials.map((material) =>
                <TableRow key={material.id}>
                      <TableCell className="font-mono text-sm">
                        {material.material_code}
                      </TableCell>
                      <TableCell className="font-medium">
                        {material.material_name}
                      </TableCell>
                      <TableCell className="text-slate-500">
                        {material.specification || "-"}
                      </TableCell>
                      <TableCell>
                        {material.category_name ?
                    <Badge variant="outline">
                            {material.category_name}
                    </Badge> :

                    "-"
                    }
                      </TableCell>
                      <TableCell>{material.unit || "PCS"}</TableCell>
                      <TableCell>
                        {material.unit_price ?
                    formatCurrency(material.unit_price) :
                    "-"}
                      </TableCell>
                      <TableCell>
                        {material.supplier_name ?
                    <div className="flex items-center gap-2">
                            <Building2 className="w-4 h-4 text-slate-400" />
                            <span className="text-sm">
                              {material.supplier_name}
                            </span>
                    </div> :

                    "-"
                    }
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleViewDetail(material.id)}>

                            <Eye className="w-4 h-4" />
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
        {/* Create Material Dialog */}
        <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
          <DialogContent className="bg-slate-900 border-slate-700">
            <DialogHeader>
              <DialogTitle className="text-slate-200">新建物料</DialogTitle>
            </DialogHeader>
            <DialogBody>
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    物料编码 *
                  </label>
                  <Input
                    value={newMaterial.material_code}
                    onChange={(e) =>
                    setNewMaterial({
                      ...newMaterial,
                      material_code: e.target.value
                    })
                    }
                    placeholder="请输入物料编码" />

                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    物料名称 *
                  </label>
                  <Input
                    value={newMaterial.material_name}
                    onChange={(e) =>
                    setNewMaterial({
                      ...newMaterial,
                      material_name: e.target.value
                    })
                    }
                    placeholder="请输入物料名称" />

                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">规格</label>
                  <Input
                    value={newMaterial.specification}
                    onChange={(e) =>
                    setNewMaterial({
                      ...newMaterial,
                      specification: e.target.value
                    })
                    }
                    placeholder="请输入规格" />

                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">分类</label>
                  <Select
                    value={newMaterial.category_id?.toString() || "none"}
                    onValueChange={(val) =>
                    setNewMaterial({
                      ...newMaterial,
                      category_id:
                      val && val !== "none" ? parseInt(val) : null
                    })
                    }>

                    <SelectTrigger>
                      <SelectValue placeholder="选择分类" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">无</SelectItem>
                      {categories.map((cat) =>
                      <SelectItem key={cat.id} value={cat.id.toString()}>
                          {cat.name}
                      </SelectItem>
                      )}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">单位</label>
                  <Input
                    value={newMaterial.unit}
                    onChange={(e) =>
                    setNewMaterial({ ...newMaterial, unit: e.target.value })
                    }
                    placeholder="PCS" />

                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">单价</label>
                  <Input
                    type="number"
                    value={newMaterial.unit_price}
                    onChange={(e) =>
                    setNewMaterial({
                      ...newMaterial,
                      unit_price: parseFloat(e.target.value) || 0
                    })
                    }
                    placeholder="0.00" />

                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    供应商
                  </label>
                  <Select
                    value={newMaterial.supplier_id?.toString() || "none"}
                    onValueChange={(val) =>
                    setNewMaterial({
                      ...newMaterial,
                      supplier_id:
                      val && val !== "none" ? parseInt(val) : null
                    })
                    }>

                    <SelectTrigger>
                      <SelectValue placeholder="选择供应商" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">无</SelectItem>
                      {suppliers.map((supplier) =>
                      <SelectItem
                        key={supplier.id}
                        value={supplier.id.toString()}>

                          {supplier.name}
                      </SelectItem>
                      )}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">备注</label>
                  <Input
                    value={newMaterial.remark}
                    onChange={(e) =>
                    setNewMaterial({ ...newMaterial, remark: e.target.value })
                    }
                    placeholder="备注信息" />

                </div>
              </div>
            </DialogBody>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setShowCreateDialog(false)}>

                取消
              </Button>
              <Button onClick={handleCreateMaterial}>创建</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
        {/* Material Detail Dialog */}
        <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
          <DialogContent className="bg-slate-900 border-slate-700">
            <DialogHeader>
              <DialogTitle className="text-slate-200">物料详情</DialogTitle>
            </DialogHeader>
            <DialogBody>
              {selectedMaterial &&
              <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <div className="text-sm text-slate-500 mb-1">
                        物料编码
                      </div>
                      <div className="font-mono">
                        {selectedMaterial.material_code}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-slate-500 mb-1">
                        物料名称
                      </div>
                      <div>{selectedMaterial.material_name}</div>
                    </div>
                    <div>
                      <div className="text-sm text-slate-500 mb-1">规格</div>
                      <div>{selectedMaterial.specification || "-"}</div>
                    </div>
                    <div>
                      <div className="text-sm text-slate-500 mb-1">分类</div>
                      <div>{selectedMaterial.category_name || "-"}</div>
                    </div>
                    <div>
                      <div className="text-sm text-slate-500 mb-1">单位</div>
                      <div>{selectedMaterial.unit || "PCS"}</div>
                    </div>
                    <div>
                      <div className="text-sm text-slate-500 mb-1">单价</div>
                      <div>
                        {selectedMaterial.unit_price ?
                      formatCurrency(selectedMaterial.unit_price) :
                      "-"}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-slate-500 mb-1">供应商</div>
                      <div>{selectedMaterial.supplier_name || "-"}</div>
                    </div>
                  </div>
                  {selectedMaterial.remark &&
                <div>
                      <div className="text-sm text-slate-500 mb-1">备注</div>
                      <div>{selectedMaterial.remark}</div>
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
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>);

}