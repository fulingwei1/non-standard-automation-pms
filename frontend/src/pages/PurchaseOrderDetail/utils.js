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

/**
 * Transform raw backend order data (+ receipts) into the frontend PO shape
 */
export const transformOrderData = (orderData, receipts = []) => {
  return {
    id: orderData.id?.toString(),
    poNumber: orderData.order_no || orderData.id?.toString(),
    projectName: orderData.project_name || "",
    supplier: {
      id: orderData.supplier_id?.toString(),
      name: orderData.supplier_name || "",
      contact: "",
      phone: "",
      email: "",
      address: "",
      paymentTerm: "",
    },
    status: mapBackendStatusToFrontend(orderData.status),
    issueDate:
      orderData.order_date || orderData.created_at?.split("T")[0] || "",
    requiredDate: orderData.required_date || "",
    expectedDelivery: orderData.required_date || "",
    actualDelivery: receipts.length > 0 ? receipts[0].receipt_date : null,
    totalAmount: parseFloat(orderData.total_amount || 0),
    taxRate:
      orderData.tax_amount && orderData.total_amount
        ? (orderData.tax_amount / orderData.total_amount) * 100
        : 13,
    taxAmount: parseFloat(orderData.tax_amount || 0),
    totalWithTax: parseFloat(
      orderData.amount_with_tax || orderData.total_amount || 0
    ),
    currency: "CNY",
    paymentStatus: mapBackendPaymentStatus(orderData.payment_status),
    paidAmount: parseFloat(orderData.paid_amount || 0),
    invoiceStatus: "pending",
    invoicedAmount: 0,
    items: (orderData.items || []).map((item, index) => ({
      id: item.id?.toString() || `POL-${index + 1}`,
      itemNo: item.item_no || index + 1,
      materialCode: item.material_code || "",
      description: item.material_name || "",
      specification: item.specification || "",
      quantity: item.quantity || 0,
      unit: item.unit || "\u4e2a",
      unitPrice: parseFloat(item.unit_price || 0),
      amount: parseFloat(item.amount || item.amount_with_tax || 0),
      receivedQty: item.received_qty || 0,
      status: mapBackendStatusToFrontend(item.status || "confirmed"),
      notes: "",
    })),
    timeline: [
      {
        stage: "draft",
        label: "\u8349\u7a3f",
        date: orderData.created_at?.split("T")[0] || "",
        status: orderData.status === "DRAFT" ? "completed" : "completed",
        description: "\u91c7\u8d2d\u8ba2\u5355\u521b\u5efa",
      },
      {
        stage: "submitted",
        label: "\u5df2\u63d0\u4ea4",
        date:
          orderData.status !== "DRAFT"
            ? orderData.updated_at?.split("T")[0]
            : null,
        status: [
          "SUBMITTED",
          "CONFIRMED",
          "SHIPPED",
          "RECEIVED",
          "INVOICED",
        ].includes(orderData.status)
          ? "completed"
          : "pending",
        description: "\u8ba2\u5355\u5df2\u63d0\u4ea4\u7ed9\u4f9b\u5e94\u5546",
      },
      {
        stage: "confirmed",
        label: "\u5df2\u786e\u8ba4",
        date: ["CONFIRMED", "SHIPPED", "RECEIVED", "INVOICED"].includes(
          orderData.status
        )
          ? orderData.updated_at?.split("T")[0]
          : null,
        status: ["CONFIRMED", "SHIPPED", "RECEIVED", "INVOICED"].includes(
          orderData.status
        )
          ? "completed"
          : "pending",
        description: "\u4f9b\u5e94\u5546\u5df2\u786e\u8ba4\u8ba2\u5355",
      },
      {
        stage: "shipped",
        label: "\u5df2\u53d1\u8d27",
        date: ["SHIPPED", "RECEIVED", "INVOICED"].includes(orderData.status)
          ? orderData.updated_at?.split("T")[0]
          : null,
        status: ["SHIPPED", "RECEIVED", "INVOICED"].includes(orderData.status)
          ? "completed"
          : "pending",
        description: "\u7b49\u5f85\u4f9b\u5e94\u5546\u53d1\u8d27",
      },
      {
        stage: "received",
        label: "\u5df2\u6536\u8d27",
        date: receipts.length > 0 ? receipts[0].receipt_date : null,
        status: receipts.length > 0 ? "completed" : "pending",
        description: "\u7b49\u5f85\u7269\u6599\u5230\u8fbe",
      },
      {
        stage: "invoiced",
        label: "\u5df2\u5f00\u7968",
        date:
          orderData.status === "INVOICED"
            ? orderData.updated_at?.split("T")[0]
            : null,
        status: orderData.status === "INVOICED" ? "completed" : "pending",
        description: "\u7b49\u5f85\u6536\u7968\u548c\u4ed8\u6b3e",
      },
    ],
    documents: [],
    remarks: orderData.remark || "",
    attachedProject: {
      id: orderData.project_id?.toString(),
      name: orderData.project_name || "",
      stage: "",
    },
  };
};
