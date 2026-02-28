import { useState, useEffect } from "react";
import { purchaseApi, bomApi, supplierApi } from "../../../services/api";
import { toast } from "../../../components/ui/toast";

export function usePurchaseOrderFromBOM() {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [step, setStep] = useState(1); // 1: 选择BOM, 2: 预览订单, 3: 完成

    // Step 1: BOM selection
    const [boms, setBoms] = useState([]);
    const [selectedBomId, setSelectedBomId] = useState(null);
    const [selectedBom, setSelectedBom] = useState(null);
    const [defaultSupplierId, setDefaultSupplierId] = useState(null);
    const [suppliers, setSuppliers] = useState([]);

    // Step 2: Preview
    const [preview, setPreview] = useState(null);
    const [editingOrderIndex, setEditingOrderIndex] = useState(null);
    const [editingOrder, setEditingOrder] = useState(null);

    // Step 3: Result
    const [createdOrders, setCreatedOrders] = useState([]);

    useEffect(() => {
        const loadBOMs = async () => {
            try {
                const res = await bomApi.list({ status: "RELEASED", page_size: 1000 });
                const data = res.data?.data || res.data;
                setBoms(data?.items || data || []);
            } catch (err) {
                console.error("Failed to load BOMs:", err);
            }
        };
        loadBOMs();
    }, []);

    useEffect(() => {
        const loadSuppliers = async () => {
            try {
                const res = await supplierApi.list({ page_size: 1000 });
                setSuppliers(res.data?.items || res.data?.items || res.data || []);
            } catch (err) {
                console.error("Failed to load suppliers:", err);
            }
        };
        loadSuppliers();
    }, []);

    const handleGeneratePreview = async () => {
        if (!selectedBomId) {
            toast.error("请选择BOM");
            return;
        }

        try {
            setLoading(true);
            setError(null);

            const params = {
                bom_id: parseInt(selectedBomId),
                create_orders: false // Preview only
            };
            if (defaultSupplierId) {
                params.supplier_id = defaultSupplierId;
            }
            const res = await purchaseApi.orders.createFromBOM(params);
            const data = res.data?.data || res.data;
            setPreview(data);
            setSelectedBom(boms.find((b) => b.id === parseInt(selectedBomId)));
            setStep(2);
        } catch (err) {
            console.error("Failed to generate preview:", err);
            setError(err.response?.data?.detail || "生成预览失败");
            toast.error(err.response?.data?.detail || "生成预览失败");
        } finally {
            setLoading(false);
        }
    };

    const handleEditOrder = (index) => {
        setEditingOrderIndex(index);
        setEditingOrder({ ...preview.preview[index] });
    };

    const handleSaveEditedOrder = () => {
        const newPreview = { ...preview };
        newPreview.preview[editingOrderIndex] = editingOrder;
        setPreview(newPreview);
        setEditingOrderIndex(null);
        setEditingOrder(null);
        toast.success("订单信息已更新");
    };

    const handleCreateOrders = async () => {
        if (!preview || !preview.preview || preview.preview.length === 0) {
            toast.error("没有可创建的订单");
            return;
        }

        try {
            setLoading(true);
            setError(null);

            const params = {
                bom_id: preview.bom_id,
                create_orders: true
            };
            if (defaultSupplierId) {
                params.supplier_id = defaultSupplierId;
            }
            const res = await purchaseApi.orders.createFromBOM(params);
            const data = res.data?.data || res.data;
            setCreatedOrders(data.created_orders || []);
            setStep(3);
            toast.success(`已创建${data.created_orders?.length || 0}个采购订单`);
        } catch (err) {
            console.error("Failed to create orders:", err);
            setError(err.response?.data?.detail || "创建订单失败");
            toast.error(err.response?.data?.detail || "创建订单失败");
        } finally {
            setLoading(false);
        }
    };

    const handleReset = () => {
        setStep(1);
        setSelectedBomId(null);
        setSelectedBom(null);
        setPreview(null);
        setCreatedOrders([]);
        setEditingOrderIndex(null);
        setEditingOrder(null);
        setError(null);
    };

    return {
        loading,
        error,
        step, setStep,
        boms,
        selectedBomId, setSelectedBomId,
        selectedBom,
        defaultSupplierId, setDefaultSupplierId,
        suppliers,
        preview,
        editingOrderIndex,
        editingOrder, setEditingOrder,
        createdOrders,
        handleGeneratePreview,
        handleEditOrder,
        handleSaveEditedOrder,
        handleCreateOrders,
        handleReset
    };
}
