/**
 * Purchase Order Detail - Utility functions for status mapping and data transformation
 */

/**
 * Map backend status to frontend status string
 */
export const mapBackendStatusToFrontend = (backendStatus) => {
  const statusMap = {
    DRAFT: "draft",
    SUBMITTED: "submitted",
    APPROVED: "confirmed",
    CONFIRMED: "confirmed",
    SHIPPED: "shipped",
    RECEIVED: "received",
    INVOICED: "invoiced",
  };
  return statusMap[backendStatus] || backendStatus?.toLowerCase() || "draft";
};

/**
 * Map backend payment status to frontend payment status string
 */
export const mapBackendPaymentStatus = (backendStatus) => {
  const statusMap = {
    UNPAID: "unpaid",
    PARTIAL: "partial",
    PAID: "paid",
  };
  return statusMap[backendStatus] || backendStatus?.toLowerCase() || "unpaid";
};

const toDate = (value) => {
  if (!value) return "";
  return typeof value === "string" ? value.split("T")[0] : String(value);
};

const toNumber = (value, fallback = 0) => {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
};

/**
 * Transform raw backend order data (+ receipts) into the frontend PO shape
 */
export const transformOrderData = (orderData, receipts = []) => {
  const items = Array.isArray(orderData.items) ? orderData.items : [];
  const attachments = Array.isArray(orderData.attachments)
    ? orderData.attachments
    : [];

  return {
    id: orderData.id?.toString(),
    poNumber:
      orderData.order_no ||
      orderData.orderNo ||
      orderData.code ||
      orderData.id?.toString() ||
      "",
    projectName: orderData.project_name || orderData.projectName || "",
    projectCode: orderData.project_code || orderData.projectCode || "",
    supplier: {
      id: orderData.supplier_id?.toString() || orderData.supplierId?.toString() || "",
      name: orderData.supplier_name || orderData.supplierName || "",
      contact: orderData.contact_person || orderData.contactPerson || "",
      phone: orderData.contact_phone || orderData.contactPhone || "",
      email: orderData.contact_email || orderData.contactEmail || "",
      address: orderData.delivery_address || orderData.deliveryAddress || "",
      paymentTerm: orderData.payment_terms || orderData.paymentTerms || "",
    },
    status: mapBackendStatusToFrontend(orderData.status),
    issueDate: toDate(orderData.order_date || orderData.orderDate || orderData.created_at),
    requiredDate: toDate(orderData.required_date || orderData.deliveryDate),
    expectedDelivery: toDate(orderData.required_date || orderData.deliveryDate),
    actualDelivery: receipts.length > 0 ? toDate(receipts[0].receipt_date) : toDate(orderData.receivedDate),
    totalAmount: toNumber(orderData.total_amount ?? orderData.totalAmount, 0),
    taxRate:
      orderData.tax_amount && (orderData.total_amount || orderData.totalAmount)
        ? (toNumber(orderData.tax_amount) /
            toNumber(orderData.total_amount || orderData.totalAmount, 1)) *
          100
        : 13,
    taxAmount: toNumber(orderData.tax_amount, 0),
    totalWithTax: toNumber(
      orderData.amount_with_tax ?? orderData.total_amount ?? orderData.totalAmount,
      0
    ),
    currency: "CNY",
    paymentStatus: mapBackendPaymentStatus(orderData.payment_status),
    paidAmount: toNumber(orderData.paid_amount, 0),
    invoiceStatus: "pending",
    invoicedAmount: 0,
    items: items.map((item, index) => ({
      id: item.id?.toString() || `POL-${index + 1}`,
      itemNo: item.item_no || index + 1,
      materialCode: item.material_code || item.materialCode || "",
      description: item.material_name || item.materialName || "",
      specification: item.specification || "",
      quantity: toNumber(item.quantity, 0),
      unit: item.unit || "个",
      unitPrice: toNumber(item.unit_price ?? item.unitPrice, 0),
      amount: toNumber(
        item.amount ?? item.totalPrice ?? item.total_price ?? item.amount_with_tax,
        0
      ),
      receivedQty: toNumber(item.received_qty ?? item.receivedQuantity, 0),
      status: mapBackendStatusToFrontend(item.status || orderData.status || "confirmed"),
      notes: "",
    })),
    timeline: [
      {
        stage: "draft",
        label: "草稿",
        date: toDate(orderData.created_at || orderData.createdAt),
        status: "completed",
        description: "采购订单创建",
      },
      {
        stage: "submitted",
        label: "已提交",
        date:
          orderData.status && orderData.status !== "DRAFT"
            ? toDate(orderData.updated_at || orderData.approvedAt)
            : null,
        status: [
          "SUBMITTED",
          "APPROVED",
          "CONFIRMED",
          "SHIPPED",
          "RECEIVED",
          "INVOICED",
        ].includes(orderData.status)
          ? "completed"
          : "pending",
        description: "订单已提交给供应商",
      },
      {
        stage: "confirmed",
        label: "已确认",
        date: ["APPROVED", "CONFIRMED", "SHIPPED", "RECEIVED", "INVOICED"].includes(
          orderData.status
        )
          ? toDate(orderData.approvedAt || orderData.updated_at)
          : null,
        status: ["APPROVED", "CONFIRMED", "SHIPPED", "RECEIVED", "INVOICED"].includes(
          orderData.status
        )
          ? "completed"
          : "pending",
        description: "供应商已确认订单",
      },
      {
        stage: "shipped",
        label: "已发货",
        date: ["SHIPPED", "RECEIVED", "INVOICED"].includes(orderData.status)
          ? toDate(orderData.updated_at)
          : null,
        status: ["SHIPPED", "RECEIVED", "INVOICED"].includes(orderData.status)
          ? "completed"
          : "pending",
        description: "等待供应商发货",
      },
      {
        stage: "received",
        label: "已收货",
        date: receipts.length > 0 ? toDate(receipts[0].receipt_date) : toDate(orderData.receivedDate),
        status: receipts.length > 0 || orderData.status === "RECEIVED" ? "completed" : "pending",
        description: "等待物料到达",
      },
      {
        stage: "invoiced",
        label: "已开票",
        date: orderData.status === "INVOICED" ? toDate(orderData.updated_at) : null,
        status: orderData.status === "INVOICED" ? "completed" : "pending",
        description: "等待收票和付款",
      },
    ],
    documents: attachments.map((doc, index) => ({
      id: doc.id?.toString() || `DOC-${index + 1}`,
      name: doc.name || `附件-${index + 1}`,
      size: doc.size || "",
      uploadDate: toDate(doc.uploadDate || doc.upload_date || orderData.created_at),
      url: doc.url || "",
    })),
    remarks: orderData.remark || orderData.notes || "",
    attachedProject: {
      id: orderData.project_id?.toString() || orderData.projectId?.toString() || "",
      name: orderData.project_name || orderData.projectName || "",
      stage: "",
    },
    createdBy: orderData.createdBy || "",
    approvedBy: orderData.approvedBy || "",
    approvedAt: toDate(orderData.approvedAt),
  };
};
