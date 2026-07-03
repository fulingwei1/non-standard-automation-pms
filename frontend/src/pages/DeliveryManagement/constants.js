/**
 * DeliveryManagement — local normalizer helpers
 * Enum-value normalization utilities for delivery data coming from the API.
 */

export const normalizeEnumValue = (value, fallbackMap = {}) => {
  if (!value) { return value; }
  const normalized = String(value)
    .trim()
    .toLowerCase()
    .replace(/[\s-]+/g, "_");
  return fallbackMap[normalized] || normalized;
};

export const normalizeStatus = (value) =>
  normalizeEnumValue(value, {
    draft: "pending",
    intransit: "in_transit",
    in_transit: "in_transit",
    on_the_way: "in_transit",
    approved: "preparing",
    printed: "preparing",
    received: "delivered",
    returned: "cancelled",
    delivered: "delivered",
    shipped: "shipped",
    pending: "pending",
    preparing: "preparing",
    cancelled: "cancelled",
  });

export const normalizePriority = (value) =>
  normalizeEnumValue(value, {
    urgent: "urgent",
    high: "high",
    normal: "normal",
    low: "low",
  });

export const normalizeMethod = (value) =>
  normalizeEnumValue(value, {
    standard_delivery: "standard",
    express_delivery: "express",
    freight_delivery: "freight",
    selfpickup: "self_pickup",
    pickup: "self_pickup",
    self_pickup: "self_pickup",
  });

export const normalizePackageType = (value) =>
  normalizeEnumValue(value, {
    standard_package: "standard",
    fragile_package: "fragile",
    liquid_package: "liquid",
    oversize_package: "oversize",
  });

export const normalizeDelivery = (item = {}) => {
  const deliveryNo =
    item.deliveryNo ||
    item.delivery_no ||
    item.delivery_code ||
    item.code ||
    "";

  const orderNumber =
    item.orderNumber ||
    item.order_no ||
    item.order_number ||
    "";

  const customerName =
    item.customerName ||
    item.customer_name ||
    item.customer?.name ||
    item.customer ||
    item.recipient_name ||
    "";

  return {
    id: item.id || item.delivery_id || deliveryNo || orderNumber,
    deliveryNo,
    orderNumber,
    customerName,
    status: normalizeStatus(item.status || item.delivery_status),
    priority: normalizePriority(item.priority || item.delivery_priority),
    shippingMethod: normalizeMethod(
      item.shippingMethod || item.shipping_method || item.delivery_method || item.delivery_type
    ),
    packageType: normalizePackageType(item.packageType || item.package_type),
    scheduledDate:
      item.scheduledDate ||
      item.scheduled_date ||
      item.delivery_date ||
      item.planned_delivery_time ||
      item.planned_delivery_date ||
      item.plan_delivery_date,
    actualDate:
      item.actualDate || item.actual_date || item.actual_delivery_time || item.ship_date,
    trackingNumber:
      item.trackingNumber || item.tracking_no || item.tracking_number,
    logisticsCompany:
      item.logisticsCompany || item.logistics_company || item.carrier_name,
    receiverName:
      item.receiverName || item.receiver_name || item.recipient_name,
    receiverPhone:
      item.receiverPhone || item.receiver_phone || item.recipient_phone,
    deliveryAddress:
      item.deliveryAddress ||
      item.delivery_address ||
      item.receiver_address ||
      item.recipient_address,
    itemCount: item.itemCount ?? item.item_count ?? item.total_items,
    totalWeight: item.totalWeight ?? item.total_weight ?? item.weight,
    notes: item.notes || item.remark || item.remarks,
    deliveryAmount:
      item.delivery_amount != null && item.delivery_amount !== ""
        ? Number(item.delivery_amount)
        : item.deliveryAmount != null
          ? Number(item.deliveryAmount)
          : 0,
    deliveryDate:
      item.delivery_date ||
      item.deliveryDate ||
      item.scheduled_date ||
      item.scheduledDate ||
      item.actual_date ||
      item.actualDate,
    approvalStatus: item.approval_status ?? item.approvalStatus,
    deliveryStatusRaw: item.delivery_status ?? item.deliveryStatus,
    shipDate: item.ship_date ?? item.shipDate,
    receiveDate: item.receive_date ?? item.receiveDate,
  };
};
