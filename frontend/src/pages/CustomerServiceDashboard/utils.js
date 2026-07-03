const firstValue = (...values) =>
  values.find((value) => value !== undefined && value !== null && value !== "");

const toDateOnly = (value) => (value ? String(value).split("T")[0] : "");

const normalizeSearchText = (value) => String(value || "").toLowerCase();

const calculateRemainingDays = (endDate) => {
  if (!endDate) {
    return 0;
  }
  const end = new Date(endDate);
  if (Number.isNaN(end.getTime())) {
    return 0;
  }
  const diff = end.getTime() - Date.now();
  return Math.max(0, Math.ceil(diff / (1000 * 60 * 60 * 24)));
};

const isResolvedOrClosed = (status) =>
  ["RESOLVED", "CLOSED", "PENDING_VERIFY", "resolved", "closed"].includes(status);

export const getTicketId = (ticketOrId) =>
  typeof ticketOrId === "object" && ticketOrId !== null ? ticketOrId.id : ticketOrId;

export const buildTicketClosePayload = (ticket = {}) => ({
  solution:
    firstValue(
      ticket.solution,
      ticket.resolution,
      ticket.closeSolution,
      ticket.description,
      ticket.title,
    ) || "客户问题已解决",
});

export const normalizeDashboardTicket = (ticket = {}) => {
  const assignedName = firstValue(
    ticket.engineer,
    ticket.assigned_to_name,
    ticket.assignee_name,
    ticket.assigned_engineer,
    ticket.assigned_to,
  );
  return {
    ...ticket,
    id: ticket.id,
    title: firstValue(ticket.title, ticket.subject, ticket.problem_desc, ticket.ticket_no, ""),
    customerName: firstValue(ticket.customer_name, ticket.customerName, ""),
    projectName: firstValue(ticket.project_name, ticket.projectName, ""),
    description: firstValue(ticket.description, ticket.problem_desc, ""),
    serviceType: firstValue(
      ticket.service_type,
      ticket.serviceType,
      ticket.ticket_type,
      ticket.problem_type,
      "",
    ),
    status: firstValue(ticket.status, ""),
    priority: firstValue(ticket.priority, ticket.urgency, ""),
    engineer: assignedName || "",
    createdAt: firstValue(ticket.created_at, ticket.createdAt, ticket.reported_time, ""),
    updatedAt: firstValue(ticket.updated_at, ticket.updatedAt, ""),
    responseTime: firstValue(ticket.response_time, ticket.responseTime, 0),
    resolvedDate: firstValue(ticket.resolved_at, ticket.resolved_time, ticket.resolvedDate, null),
    satisfaction: firstValue(ticket.satisfaction, null),
    solution: firstValue(ticket.solution, ticket.resolution, ""),
  };
};

export const normalizeWarrantyProject = (warranty = {}) => {
  const endDate = toDateOnly(
    firstValue(warranty.end_date, warranty.endDate, warranty.warranty_end, warranty.warrantyEnd, ""),
  );
  return {
    id: firstValue(warranty.id, warranty.project_id, warranty.projectId),
    projectName: firstValue(warranty.project_name, warranty.projectName, warranty.name, ""),
    customerName: firstValue(warranty.customer_name, warranty.customerName, ""),
    warrantyType: firstValue(
      warranty.warranty_type,
      warranty.warrantyType,
      warranty.type,
      "standard",
    ),
    startDate: toDateOnly(
      firstValue(
        warranty.start_date,
        warranty.startDate,
        warranty.warranty_start,
        warranty.warrantyStart,
        "",
      ),
    ),
    endDate,
    status: firstValue(warranty.status, "active"),
    remainingDays: firstValue(
      warranty.remaining_days,
      warranty.remainingDays,
      calculateRemainingDays(endDate),
    ),
    totalClaims: firstValue(warranty.total_claims, warranty.totalClaims, 0),
    resolvedClaims: firstValue(warranty.resolved_claims, warranty.resolvedClaims, 0),
  };
};

const isWarrantyTicket = (ticket = {}) => {
  const serviceType = normalizeSearchText(ticket.serviceType);
  const title = normalizeSearchText(ticket.title);
  const description = normalizeSearchText(ticket.description);
  return (
    serviceType.includes("warranty") ||
    serviceType.includes("质保") ||
    title.includes("warranty") ||
    title.includes("质保") ||
    description.includes("warranty") ||
    description.includes("质保")
  );
};

export const buildWarrantyProjects = ({
  dashboardWarrantyProjects = [],
  tickets = [],
} = {}) => {
  const normalizedWarrantyProjects = (dashboardWarrantyProjects || []).map(normalizeWarrantyProject);
  if (normalizedWarrantyProjects.length > 0) {
    return normalizedWarrantyProjects;
  }

  return (tickets || []).filter(isWarrantyTicket).map((ticket) => ({
    id: `ticket-${firstValue(ticket.id, ticket.ticket_no, ticket.title)}`,
    projectName: firstValue(ticket.projectName, ticket.title, `服务工单 ${ticket.id}`),
    customerName: firstValue(ticket.customerName, ""),
    warrantyType: "standard",
    startDate: toDateOnly(ticket.createdAt),
    endDate: toDateOnly(ticket.resolvedDate),
    status: firstValue(ticket.status, "active"),
    remainingDays: 0,
    totalClaims: 1,
    resolvedClaims: isResolvedOrClosed(ticket.status) ? 1 : 0,
  }));
};
