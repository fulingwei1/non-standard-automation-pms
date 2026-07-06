// 验厂资料 API
import api from "./client";

export async function submitAuditPack(payload) {
  const { data } = await api.post("/audit-packs", payload);
  return data?.data || data;
}

export async function reviewAuditPack(id, action, comment) {
  const { data } = await api.post(`/audit-packs/${id}/review`, { action, comment });
  return data?.data || data;
}

export async function listAuditPacks(status = null) {
  const { data } = await api.get("/audit-packs", { params: status ? { status } : {} });
  return data?.data || data;
}

export async function pendingAuditPacks() {
  const { data } = await api.get("/audit-packs/pending");
  return data?.data || data;
}

export async function getAuditPackDetail(id) {
  const { data } = await api.get(`/audit-packs/${id}`);
  return data?.data || data;
}
