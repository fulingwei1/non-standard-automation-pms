import { useNavigate } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { PageHeader } from "../../components/layout";
import { Button } from "../../components/ui/button";
import { ErrorMessage } from "../../components/common";
import { usePurchaseOrderFromBOM } from "./hooks";
import {
    BOMSelectionStep,
    OrderPreviewStep,
    OrderCreationResultStep,
    EditOrderDialog
} from "./components";

export default function PurchaseOrderFromBOM() {
    const navigate = useNavigate();
    const {
        loading,
        error,
        step,
        boms,
        suppliers,
        selectedBomId, setSelectedBomId,
        defaultSupplierId, setDefaultSupplierId,
        preview,
        editingOrder, setEditingOrder,
        createdOrders,
        handleGeneratePreview,
        handleEditOrder,
        handleSaveEditedOrder,
        handleCreateOrders,
        handleReset
    } = usePurchaseOrderFromBOM();

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
            <div className="container mx-auto px-4 py-6 space-y-6">
                <PageHeader
                    title="从BOM生成采购订单"
                    description="根据BOM物料清单，按供应商分组批量创建采购订单"
                    actions={
                        <Button variant="outline" onClick={() => navigate("/purchases")}>
                            <ArrowLeft className="w-4 h-4 mr-2" />
                            返回
                        </Button>
                    }
                />

                {error && <ErrorMessage message={error} />}

                {/* Step 1: Select BOM */}
                {step === 1 && (
                    <BOMSelectionStep
                        boms={boms}
                        suppliers={suppliers}
                        selectedBomId={selectedBomId}
                        setSelectedBomId={setSelectedBomId}
                        defaultSupplierId={defaultSupplierId}
                        setDefaultSupplierId={setDefaultSupplierId}
                        loading={loading}
                        onGenerate={handleGeneratePreview}
                    />
                )}

                {/* Step 2: Preview Orders */}
                {step === 2 && (
                    <OrderPreviewStep
                        preview={preview}
                        loading={loading}
                        onEditOrder={handleEditOrder}
                        onReset={handleReset}
                        onCreate={handleCreateOrders}
                    />
                )}

                {/* Step 3: Result */}
                {step === 3 && (
                    <OrderCreationResultStep
                        createdOrders={createdOrders}
                        onReset={handleReset}
                    />
                )}

                {/* Edit Order Dialog */}
                <EditOrderDialog
                    editingOrder={editingOrder}
                    setEditingOrder={setEditingOrder}
                    onSave={handleSaveEditedOrder}
                />
            </div>
        </div>
    );
}
