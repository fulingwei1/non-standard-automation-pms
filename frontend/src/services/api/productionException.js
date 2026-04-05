import { api } from "./client.js";

const FRONT_STATUS_TO_BACK = {
  REPORTED: "OPEN",
  IN_PROGRESS: "IN_PROGRESS",
  RESOLVED: "RESOLVED",
  CLOSED: "CLOSED",
};

const BACK_STATUS_TO_FRONT = {
  OPEN: "REPORTED",
  IN_PROGRESS: "IN_PROGRESS",
  RESOLVED: "RESOLVED",
  CLOSED: "CLOSED",
};

const normalizeException = (item = {}) => ({
  ...item,
  exception_no: item.exception_no || item.event_no,
  title: item.title || item.event_title,
  description: item.description || item.event_description,
  exception_type: item.exception_type || item.event_type,
  exception_level: item.exception_level || item.severity,
  report_time: item.report_time || item.discovered_at,
  reporter_name: item.reporter_name || item.discovered_by_name,
  status: BACK_STATUS_TO_FRONT[item.status] || item.status,
});

export const productionExceptionApi = {
  async list(params = {}) {
    const response = await api.get("/exceptions", {
      params: {
        project_id: params.project_id && params.project_id !== "all" ? params.project_id : undefined,
        event_type:
          params.event_type ||
          (params.exception_type && params.exception_type !== "all"
            ? params.exception_type
            : undefined),
        severity:
          params.severity ||
          (params.exception_level && params.exception_level !== "all"
            ? params.exception_level
            : undefined),
        status:
          params.status && params.status !== "all"
            ? FRONT_STATUS_TO_BACK[params.status] || params.status
            : undefined,
        keyword: params.keyword || params.search || undefined,
      },
    });

    const data = response?.data?.data ?? response?.data ?? response;
    return {
      ...response,
      data: {
        ...data,
        items: (data?.items || []).map(normalizeException),
      },
    };
  },

  async create(data) {
    const response = await api.post("/exceptions", {
      source_type: data.source_type || "PRODUCTION",
      project_id: data.project_id || null,
      machine_id: data.equipment_id || null,
      event_type: data.exception_type || "OTHER",
      severity: data.exception_level || "MINOR",
      event_title: data.title,
      event_description: data.description || data.remark || "",
      impact_description: data.remark || null,
      schedule_impact: Math.round(Number(data.impact_hours) || 0),
      cost_impact: Number(data.impact_cost) || 0,
      attachments: [],
    });
    return {
      ...response,
      data: normalizeException(response?.data?.data ?? response?.data ?? response),
    };
  },

  async resolve(id, resolution = {}) {
    if (resolution.handle_plan) {
      await api.post(`/exceptions/${id}/actions`, null, {
        params: {
          action_type: "PLAN",
          action_content: resolution.handle_plan,
        },
      });
    }
    if (resolution.handle_result) {
      await api.post(`/exceptions/${id}/actions`, null, {
        params: {
          action_type: "RESULT",
          action_content: resolution.handle_result,
        },
      });
    }
    return api.put(`/exceptions/${id}/status`, null, {
      params: {
        status: FRONT_STATUS_TO_BACK[resolution.status || "RESOLVED"],
      },
    });
  },
};
