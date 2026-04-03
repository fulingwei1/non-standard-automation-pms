import { gradeColors } from "./constants";

export const normalizeGrade = (value) => {
  if (!value) {return "B";}
  const upper = String(value).trim().toUpperCase();
  if (upper === "VIP") {return "A";}
  return gradeColors[upper] ? upper : "B";
};

export const normalizeStatus = (value, isActive) => {
  if (value) {
    const raw = String(value).trim().toLowerCase();
    if (["active", "enabled", "enable"].includes(raw)) {return "active";}
    if (["potential", "prospect", "lead"].includes(raw)) {return "potential";}
    if (["dormant", "inactive", "disabled"].includes(raw)) {return "dormant";}
    if (["lost"].includes(raw)) {return "lost";}
  }
  if (isActive === false) {return "dormant";}
  return "active";
};

export const normalizeTags = (value) => {
  if (Array.isArray(value)) {return value;}
  if (typeof value === "string") {
    return value
      .split(/[,，]/)
      .map((tag) => tag.trim())
      .filter(Boolean);
  }
  return [];
};

export const normalizeCustomer = (customer = {}) => {
  const name =
    customer.name || customer.customer_name || customer.customerName || "";
  const shortName =
    customer.shortName ||
    customer.customer_short_name ||
    customer.short_name ||
    customer.customerShortName ||
    name;

  const grade = normalizeGrade(
    customer.grade || customer.level || customer.customer_level
  );
  const status = normalizeStatus(customer.status, customer.is_active);

  return {
    id: customer.id || customer.customer_id,
    name,
    shortName,
    grade,
    status,
    industry: customer.industry || customer.industry_name || "",
    location:
      customer.location ||
      customer.address ||
      customer.company_address ||
      "",
    contactPerson:
      customer.contactPerson ||
      customer.contact_person ||
      customer.contact_name ||
      "",
    phone: customer.phone || customer.contact_phone || customer.mobile || "",
    email: customer.email || customer.contact_email || "",
    totalAmount:
      customer.totalAmount ??
      customer.total_amount ??
      customer.lifetime_value ??
      0,
    pendingAmount:
      customer.pendingAmount ??
      customer.pending_amount ??
      customer.receivable_amount ??
      0,
    projectCount:
      customer.projectCount ??
      customer.project_count ??
      (Array.isArray(customer.projects) ? customer.projects?.length : 0),
    lastContact:
      customer.lastContact ||
      customer.last_contact ||
      customer.last_contact_date ||
      "",
    isWarning:
      Boolean(
        customer.isWarning ??
        customer.is_warning ??
        customer.warning ??
        customer.is_risk
      ),
    tags: normalizeTags(customer.tags)
  };
};
