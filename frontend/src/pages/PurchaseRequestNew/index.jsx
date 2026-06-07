import { useState, useEffect } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowLeft } from "lucide-react";
import { PageHeader } from "../../components/layout";
import { Button } from "../../components/ui/button";
import { fadeIn } from "../../lib/animations";
import {
  purchaseApi,
  projectApi,
  materialApi,
  machineApi,
  supplierApi,
} from "../../services/api";
import { toast } from "../../components/ui/toast";
import { LoadingCard } from "../../components/common";
import { ErrorMessage } from "../../components/common";

import BasicInfoCard from "./BasicInfoCard";
import ItemsCard from "./ItemsCard";
import SummaryCard from "./SummaryCard";
import MaterialDialog from "./MaterialDialog";
import {
  calculateTotalAmount,
  filterMaterials,
  createEmptyItem,
  buildRequestPayload,
  DEFAULT_FORM_DATA,
} from "./utils";
import { getProjectContextFilters } from "../../lib/projectContext";

const parseProjectId = (value) => {
  const parsed = Number.parseInt(value, 10);
  return Number.isNaN(parsed) ? null : parsed;
};

export default function PurchaseRequestNew() {
  const navigate = useNavigate();
  const { id } = useParams();
  const [searchParams] = useSearchParams();
  const isEdit = !!id;
  const projectIdFromQuery = getProjectContextFilters(searchParams).project_id || "";
  const contextProjectId = parseProjectId(projectIdFromQuery);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);

  // Form data
  const [formData, setFormData] = useState(() => ({
    ...DEFAULT_FORM_DATA,
    project_id: contextProjectId,
  }));

  // Dropdown data
  const [projects, setProjects] = useState([]);
  const [machines, setMachines] = useState([]);
  const [materials, setMaterials] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [materialSearchQuery, setMaterialSearchQuery] = useState("");
  const [showMaterialDialog, setShowMaterialDialog] = useState(false);
  const [selectedItemIndex, setSelectedItemIndex] = useState(null);

  // Load projects
  useEffect(() => {
    const loadProjects = async () => {
      try {
        const params = { page_size: 1000 };
        if (projectIdFromQuery) {params.project_id = projectIdFromQuery;}
        const res = await projectApi.list(params);
        setProjects(res.data?.items || res.data?.items || res.data || []);
      } catch (err) {
        console.error("Failed to load projects:", err);
      }
    };
    loadProjects();
  }, [projectIdFromQuery]);

  useEffect(() => {
    if (isEdit || !contextProjectId) {
      return;
    }
    setFormData((prev) => ({
      ...prev,
      project_id: prev.project_id || contextProjectId,
    }));
  }, [contextProjectId, isEdit]);

  // Load machines when project changes
  useEffect(() => {
    const loadMachines = async () => {
      if (!formData.project_id) {
        setMachines([]);
        return;
      }

      try {
        const response = await machineApi.list(formData.project_id, {
          page: 1,
          page_size: 100,
        });
        const machineList =
          response.data?.items || response.data?.items || response.data || [];
        setMachines(
          (machineList || []).map((m) => ({
            id: m.id,
            machine_code: m.machine_code || m.machine_no,
            machine_name:
              m.machine_name || m.machine_code || `机台${m.id}`,
          }))
        );
      } catch (err) {
        console.error("Failed to load machines:", err);
        setMachines([]);
      }
    };
    loadMachines();
  }, [formData.project_id]);

  // Load materials
  useEffect(() => {
    const loadMaterials = async () => {
      try {
        const res = await materialApi.list({ page_size: 1000 });
        setMaterials(res.data?.items || res.data?.items || res.data || []);
      } catch (err) {
        console.error("Failed to load materials:", err);
      }
    };
    loadMaterials();
  }, []);

  // Load suppliers
  useEffect(() => {
    const loadSuppliers = async () => {
      try {
        const res = await supplierApi.list({ page: 1, page_size: 1000 });
        setSuppliers(res.data?.items || res.data?.items || res.data || []);
      } catch (err) {
        console.error("Failed to load suppliers:", err);
      }
    };
    loadSuppliers();
  }, []);

  // Load request data if editing
  useEffect(() => {
    if (isEdit && id) {
      const loadRequest = async () => {
        try {
          setLoading(true);
          const res = await purchaseApi.requests.get(id);
          const data = res.data?.data || res.data;
          setFormData({
            project_id: data.project_id,
            machine_id: data.machine_id,
            supplier_id: data.supplier_id || null,
            request_type: data.request_type || "NORMAL",
            request_reason: data.request_reason || "",
            required_date: data.required_date || "",
            remark: data.remark || "",
            items: data.items || [],
          });
        } catch (err) {
          console.error("Failed to load request:", err);
          setError(err.response?.data?.detail || "加载失败");
        } finally {
          setLoading(false);
        }
      };
      loadRequest();
    }
  }, [isEdit, id]);

  // Derived values
  const totalAmount = calculateTotalAmount(formData.items);
  const filteredMaterials = filterMaterials(materials, materialSearchQuery);

  // Item handlers
  const handleAddItem = () => {
    setFormData({
      ...formData,
      items: [...formData.items, createEmptyItem(formData.required_date)],
    });
  };

  const handleRemoveItem = (index) => {
    const newItems = (formData.items || []).filter((_, i) => i !== index);
    setFormData({ ...formData, items: newItems });
  };

  const handleUpdateItem = (index, field, value) => {
    const newItems = [...formData.items];
    newItems[index] = { ...newItems[index], [field]: value };
    setFormData({ ...formData, items: newItems });
  };

  // Material selection
  const handleSelectMaterial = (material) => {
    if (selectedItemIndex !== null) {
      const newItems = [...formData.items];
      newItems[selectedItemIndex] = {
        ...newItems[selectedItemIndex],
        material_id: material.id,
        material_code: material.material_code,
        material_name: material.material_name,
        unit: material.unit || "件",
        unit_price: material.standard_price || material.last_price || 0,
      };
      setFormData({ ...formData, items: newItems });
      setShowMaterialDialog(false);
      setSelectedItemIndex(null);
      setMaterialSearchQuery("");
    }
  };

  const handleOpenMaterialDialog = (index) => {
    setSelectedItemIndex(index);
    setMaterialSearchQuery("");
    setShowMaterialDialog(true);
  };

  // Save request
  const handleSave = async () => {
    if (!formData.items || formData.items?.length === 0) {
      toast.error("请至少添加一个物料");
      return;
    }

    for (let i = 0; i < formData.items?.length; i++) {
      const item = formData.items[i];
      if (!item.material_name || !item.quantity || item.quantity <= 0) {
        toast.error(`物料明细第 ${i + 1} 行填写不完整`);
        return;
      }
    }

    if (!formData.supplier_id) {
      toast.error("请选择供应商");
      return;
    }

    try {
      setSaving(true);
      const requestData = buildRequestPayload(formData);

      if (isEdit) {
        await purchaseApi.requests.update(id, requestData);
        toast.success("采购申请已更新");
        navigate("/purchase-requests");
      } else {
        await purchaseApi.requests.create(requestData);
        toast.success("采购申请已创建");
        navigate("/purchase-requests");
      }
    } catch (err) {
      console.error("Failed to save request:", err);
      toast.error(err.response?.data?.detail || "保存失败");
    } finally {
      setSaving(false);
    }
  };

  // Submit request
  const handleSubmit = async () => {
    if (!formData.items || formData.items?.length === 0) {
      toast.error("请至少添加一个物料");
      return;
    }

    await handleSave();

    if (!error) {
      try {
        toast.success("采购申请已提交");
        navigate("/purchase-requests");
      } catch (err) {
        console.error("Failed to submit request:", err);
        toast.error(err.response?.data?.detail || "提交失败");
      }
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <div className="container mx-auto px-4 py-6">
          <LoadingCard />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="container mx-auto px-4 py-6 space-y-6">
        <PageHeader
          title={isEdit ? "编辑采购申请" : "新建采购申请"}
          description={isEdit ? "修改采购申请信息" : "创建新的采购申请"}
          actions={
            <Button
              variant="outline"
              onClick={() => navigate("/purchase-requests")}
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              返回
            </Button>
          }
        />

        {error && <ErrorMessage message={error} />}

        <motion.div
          variants={fadeIn}
          className="grid grid-cols-1 lg:grid-cols-3 gap-6"
        >
          {/* Main Form */}
          <div className="lg:col-span-2 space-y-6">
            <BasicInfoCard
              formData={formData}
              setFormData={setFormData}
              projects={projects}
              machines={machines}
              suppliers={suppliers}
            />

            <ItemsCard
              items={formData.items}
              onAddItem={handleAddItem}
              onRemoveItem={handleRemoveItem}
              onUpdateItem={handleUpdateItem}
              onOpenMaterialDialog={handleOpenMaterialDialog}
            />
          </div>

          {/* Summary */}
          <div className="lg:col-span-1">
            <SummaryCard
              itemCount={formData.items?.length}
              totalAmount={totalAmount}
              saving={saving}
              onSave={handleSave}
              onSubmit={handleSubmit}
            />
          </div>
        </motion.div>

        <MaterialDialog
          open={showMaterialDialog}
          onOpenChange={setShowMaterialDialog}
          searchQuery={materialSearchQuery}
          onSearchChange={setMaterialSearchQuery}
          filteredMaterials={filteredMaterials}
          onSelectMaterial={handleSelectMaterial}
        />
      </div>
    </div>
  );
}
