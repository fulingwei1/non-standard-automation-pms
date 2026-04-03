/**
 * Purchase Order Detail Page - Complete purchase order management
 * Handles PO lifecycle from creation to receipt and invoice
 */

import { useParams, useNavigate } from "react-router-dom";
import { Edit } from "lucide-react";
import { PageHeader } from "../../components/layout";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "../../components/ui";
import { usePurchaseOrder } from "./usePurchaseOrder";
import HeaderCards from "./HeaderCards";
import ProgressCard from "./ProgressCard";
import TimelineCard from "./TimelineCard";
import ItemsTab from "./ItemsTab";
import SupplierTab from "./SupplierTab";
import DocumentsTab from "./DocumentsTab";
import NotesTab from "./NotesTab";
import ActionBar from "./ActionBar";

export default function PurchaseOrderDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { po, loading, error, progress, totalItems } = usePurchaseOrder(id);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <div className="container mx-auto px-4 py-6">
          <div className="text-center py-16">
            <div className="text-slate-400">{"\u52a0\u8f7d\u4e2d..."}</div>
          </div>
        </div>
      </div>
    );
  }

  if (error && !po) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <div className="container mx-auto px-4 py-6">
          <div className="text-center py-16">
            <div className="text-red-400">{error}</div>
          </div>
        </div>
      </div>
    );
  }

  if (!po) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <div className="container mx-auto px-4 py-6">
          <div className="text-center py-16">
            <div className="text-slate-400">{"\u91c7\u8d2d\u8ba2\u5355\u4e0d\u5b58\u5728"}</div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="container mx-auto px-4 py-6 space-y-6 pb-8">
        <PageHeader
          title={po.poNumber}
          description={po.projectName}
          action={
            po.status === "DRAFT" || po.status === "draft"
              ? {
                  label: "\u7f16\u8f91",
                  icon: Edit,
                  onClick: () => {
                    navigate(`/purchase-orders?action=edit&id=${po.id}`);
                  },
                }
              : null
          }
        />

        {/* PO Header Info */}
        <HeaderCards po={po} />

        {/* Progress */}
        <ProgressCard po={po} progress={progress} />

        {/* Timeline */}
        <TimelineCard po={po} />

        {/* Tabs for different sections */}
        <Tabs defaultValue="items" className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="items">{"\u7269\u6599\u6e05\u5355"}</TabsTrigger>
            <TabsTrigger value="supplier">{"\u4f9b\u5e94\u5546\u4fe1\u606f"}</TabsTrigger>
            <TabsTrigger value="documents">{"\u6587\u4ef6\u9644\u4ef6"}</TabsTrigger>
            <TabsTrigger value="notes">{"\u5907\u6ce8"}</TabsTrigger>
          </TabsList>

          <TabsContent value="items">
            <ItemsTab po={po} totalItems={totalItems} />
          </TabsContent>

          <TabsContent value="supplier">
            <SupplierTab po={po} />
          </TabsContent>

          <TabsContent value="documents">
            <DocumentsTab po={po} />
          </TabsContent>

          <TabsContent value="notes">
            <NotesTab po={po} />
          </TabsContent>
        </Tabs>

        {/* Action Bar */}
        <ActionBar po={po} />
      </div>
    </div>
  );
}
