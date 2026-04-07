import { useState, useEffect } from "react";


import { fadeIn, staggerContainer } from "../../lib/animations";
import { supplierApi } from "../../services/api";
import { INITIAL_SUPPLIER } from "./utils";

export default function SupplierManagementData() {
  const [suppliers, setSuppliers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [_showEditDialog, setShowEditDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [showRatingDialog, setShowRatingDialog] = useState(false);
  const [selectedSupplier, setSelectedSupplier] = useState(null);
  const [searchKeyword, setSearchKeyword] = useState("");
  const [filterType, setFilterType] = useState("all");
  const [filterStatus, setFilterStatus] = useState("all");
  const [filterLevel, setFilterLevel] = useState("all");
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [total, setTotal] = useState(0);

  const [newSupplier, setNewSupplier] = useState({ ...INITIAL_SUPPLIER });
  const [editSupplier, setEditSupplier] = useState(null);
  const [ratingData, setRatingData] = useState({
    quality_rating: 0,
    delivery_rating: 0,
    service_rating: 0,
  });

  // 加载供应商列表
  const loadSuppliers = async () => {
    setLoading(true);
    try {
      const params = {
        page,
        page_size: pageSize,
      };
      if (searchKeyword) {
        params.keyword = searchKeyword;
      }
      if (filterType !== "all") {
        params.supplier_type = filterType;
      }
      if (filterStatus !== "all") {
        params.status = filterStatus;
      }
      if (filterLevel !== "all") {
        params.supplier_level = filterLevel;
      }

      const response = await supplierApi.list(params);
      // 使用统一响应格式处理
      const paginatedData = response.formatted || response.data;
      setSuppliers(paginatedData.items || []);
      setTotal(paginatedData.total || 0);
    } catch (error) {
      console.error("加载供应商列表失败:", error);
      alert(
        "加载供应商列表失败: " +
          (error.response?.data?.detail || error.message)
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSuppliers();
  }, [page, searchKeyword, filterType, filterStatus, filterLevel]);

  const handleCreateChange = (e) => {
    const { name, value } = e.target;
    setNewSupplier((prev) => ({ ...prev, [name]: value }));
  };

  const _handleEditChange = (e) => {
    const { name, value } = e.target;
    setEditSupplier((prev) => ({ ...prev, [name]: value }));
  };

  const handleCreateSubmit = async () => {
    try {
      await supplierApi.create(newSupplier);
      setShowCreateDialog(false);
      setNewSupplier({ ...INITIAL_SUPPLIER });
      loadSuppliers();
    } catch (error) {
      alert(
        "创建供应商失败: " + (error.response?.data?.detail || error.message)
      );
    }
  };

  const _handleEditSubmit = async () => {
    try {
      await supplierApi.update(editSupplier.id, editSupplier);
      setShowEditDialog(false);
      setEditSupplier(null);
      loadSuppliers();
    } catch (error) {
      alert(
        "更新供应商失败: " + (error.response?.data?.detail || error.message)
      );
    }
  };

  const handleRatingSubmit = async () => {
    try {
      const params = {};
      if (ratingData.quality_rating > 0) {
        params.quality_rating = ratingData.quality_rating;
      }
      if (ratingData.delivery_rating > 0) {
        params.delivery_rating = ratingData.delivery_rating;
      }
      if (ratingData.service_rating > 0) {
        params.service_rating = ratingData.service_rating;
      }

      await supplierApi.updateRating(selectedSupplier.id, params);
      setShowRatingDialog(false);
      loadSuppliers();
    } catch (error) {
      alert("更新评级失败: " + (error.response?.data?.detail || error.message));
    }
  };

  const handleViewDetail = async (id) => {
    try {
      const response = await supplierApi.get(id);
      setSelectedSupplier(response.data);
      setShowDetailDialog(true);
    } catch (error) {
      alert(
        "获取供应商详情失败: " +
          (error.response?.data?.detail || error.message)
      );
    }
  };

  const handleEdit = async (id) => {
    try {
      const response = await supplierApi.get(id);
      setEditSupplier(response.data);
      setShowEditDialog(true);
    } catch (error) {
      alert(
        "获取供应商信息失败: " +
          (error.response?.data?.detail || error.message)
      );
    }
  };

  const handleRating = async (id) => {
    try {
      const response = await supplierApi.get(id);
      setSelectedSupplier(response.data);
      setRatingData({
        quality_rating: parseFloat(response.data.quality_rating) || 0,
        delivery_rating: parseFloat(response.data.delivery_rating) || 0,
        service_rating: parseFloat(response.data.service_rating) || 0,
      });
      setShowRatingDialog(true);
    } catch (error) {
      alert(
        "获取供应商信息失败: " +
          (error.response?.data?.detail || error.message)
      );
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="container mx-auto px-4 py-6 space-y-6">
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="space-y-6"
        >
          <PageHeader
            title="供应商管理"
            description="管理系统供应商信息，包括创建、编辑、评级等操作。"
            actions={
              <Button onClick={() => setShowCreateDialog(true)}>
                <Plus className="mr-2 h-4 w-4" /> 新增供应商
              </Button>
            }
          />

          <motion.div variants={fadeIn}>
            <Card className="bg-slate-800/50 border-slate-700/50">
              <CardHeader className="flex-row items-center justify-between">
                <CardTitle className="text-slate-200">供应商列表</CardTitle>
                <SupplierFilters
                  searchKeyword={searchKeyword}
                  filterType={filterType}
                  filterStatus={filterStatus}
                  filterLevel={filterLevel}
                  onSearchChange={setSearchKeyword}
                  onFilterTypeChange={setFilterType}
                  onFilterStatusChange={setFilterStatus}
                  onFilterLevelChange={setFilterLevel}
                />
              </CardHeader>
              <CardContent>
                <SupplierTable
                  suppliers={suppliers}
                  loading={loading}
                  total={total}
                  page={page}
                  pageSize={pageSize}
                  onPageChange={setPage}
                  onViewDetail={handleViewDetail}
                  onEdit={handleEdit}
                  onRating={handleRating}
                />
              </CardContent>
            </Card>
          </motion.div>

          <CreateSupplierDialog
            open={showCreateDialog}
            onOpenChange={setShowCreateDialog}
            newSupplier={newSupplier}
            onFieldChange={handleCreateChange}
            onTypeChange={(value) =>
              setNewSupplier((prev) => ({ ...prev, supplier_type: value }))
            }
            onSubmit={handleCreateSubmit}
          />

          <RatingDialog
            open={showRatingDialog}
            onOpenChange={setShowRatingDialog}
            supplierName={selectedSupplier?.supplier_name}
            ratingData={ratingData}
            onRatingChange={(field, value) =>
              setRatingData((prev) => ({ ...prev, [field]: value }))
            }
            onSubmit={handleRatingSubmit}
          />

          <DetailDialog
            open={showDetailDialog}
            onOpenChange={setShowDetailDialog}
            supplier={selectedSupplier}
          />
        </motion.div>
      </div>
    </div>
  );
}
