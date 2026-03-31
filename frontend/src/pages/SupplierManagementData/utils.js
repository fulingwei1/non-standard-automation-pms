export const INITIAL_SUPPLIER = {
  supplier_code: "",
  supplier_name: "",
  supplier_short_name: "",
  supplier_type: "MATERIAL",
  contact_person: "",
  contact_phone: "",
  contact_email: "",
  address: "",
  bank_name: "",
  bank_account: "",
  tax_number: "",
  payment_terms: "",
  remark: "",
};

export function getLevelColor(level) {
  switch (level) {
    case "A":
      return "bg-green-500";
    case "B":
      return "bg-blue-500";
    case "C":
      return "bg-yellow-500";
    case "D":
      return "bg-red-500";
    default:
      return "bg-gray-500";
  }
}

export function getStatusBadgeClass(status) {
  if (status === "ACTIVE") return "bg-emerald-500";
  if (status === "SUSPENDED") return "bg-amber-500";
  return "bg-red-500";
}

export function getStatusLabel(status) {
  if (status === "ACTIVE") return "合作中";
  if (status === "SUSPENDED") return "暂停";
  return "黑名单";
}
