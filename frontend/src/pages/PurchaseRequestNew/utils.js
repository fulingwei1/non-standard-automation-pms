/**
 * Calculate the total amount from a list of items.
 */
export function calculateTotalAmount(items) {
  return (items || []).reduce((sum, item) => {
    return sum + parseFloat(item.quantity || 0) * parseFloat(item.unit_price || 0);
  }, 0);
}

/**
 * Filter materials by a search query (matches material_code or material_name).
 */
export function filterMaterials(materials, query) {
  if (!query) return materials || [];
  const lowerQuery = query.toLowerCase();
  return (materials || []).filter(
    (m) =>
      m.material_code?.toLowerCase().includes(lowerQuery) ||
      m.material_name?.toLowerCase().includes(lowerQuery)
  );
}

/**
 * Create a new empty item row with default values.
 */
export function createEmptyItem(requiredDate) {
  return {
    material_id: null,
    material_code: "",
    material_name: "",
    specification: "",
    unit: "件",
    quantity: 1,
    unit_price: 0,
    required_date: requiredDate || "",
    remark: "",
  };
}

/**
 * Build the request payload from form data.
 */
export function buildRequestPayload(formData) {
  return {
    project_id: formData.project_id || null,
    machine_id: formData.machine_id || null,
    supplier_id: formData.supplier_id || null,
    request_type: formData.request_type,
    request_reason: formData.request_reason || null,
    required_date: formData.required_date || null,
    remark: formData.remark || null,
    items: (formData.items || []).map((item) => ({
      material_id: item.material_id || null,
      material_code: item.material_code,
      material_name: item.material_name,
      specification: item.specification || null,
      unit: item.unit || "件",
      quantity: parseFloat(item.quantity),
      unit_price: parseFloat(item.unit_price || 0),
      required_date: item.required_date || null,
      remark: item.remark || null,
    })),
  };
}

/**
 * Default form data for a new purchase request.
 */
export const DEFAULT_FORM_DATA = {
  project_id: null,
  machine_id: null,
  supplier_id: null,
  request_type: "NORMAL",
  request_reason: "",
  required_date: "",
  remark: "",
  items: [],
};
