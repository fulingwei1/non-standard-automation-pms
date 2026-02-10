/**
 * DeleteConfirmDialog - 发票删除确认对话框
 * 基于通用 DeleteConfirmDialog 的发票适配
 */

import React from "react";
import DeleteConfirmDialog from "../../common/DeleteConfirmDialog";

const InvoiceDeleteConfirmDialog = ({
 open,
 onOpenChange,
 selectedInvoice,
 onConfirm
}) => {
 return (
 <DeleteConfirmDialog
 open={open}
 onOpenChange={onOpenChange}
  title="确认删除"
 description={`确定要删除发票 ${selectedInvoice?.id} 吗？此操作不可撤销。`}
   onConfirm={onConfirm}
  confirmText="删除"
 />
  );
};

export default InvoiceDeleteConfirmDialog;
