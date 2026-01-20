import { formatDate } from "../../../lib/utils";
import {
    OPPORTUNITY_STAGE_MAP,
    PROJECT_STAGE_LABELS,
    HEALTH_MAP
} from "../constants";

export const mapOpportunityStage = (stage) =>
    OPPORTUNITY_STAGE_MAP[stage?.toUpperCase?.()] || "lead";

export const mapOpportunityPriority = (priority) => {
    const value = (priority || "").toString().toLowerCase();
    if (value.includes("urgent")) return "urgent";
    if (value.includes("high")) return "high";
    if (value.includes("low")) return "low";
    return "medium";
};

export const mapProjectStageLabel = (stage) => {
    if (!stage) return "进行中";
    const normalized = stage.toString().toUpperCase();
    return PROJECT_STAGE_LABELS[normalized] || stage;
};

export const mapProjectHealth = (health) => {
    if (!health) return "warning";
    const normalized = health.toString().toUpperCase();
    return HEALTH_MAP[normalized] || "warning";
};

export const isCurrentMonth = (date) => {
    if (!date) return false;
    const checkDate = new Date(date);
    if (isNaN(checkDate.getTime())) return false;
    const now = new Date();
    return checkDate.getFullYear() === now.getFullYear() && checkDate.getMonth() === now.getMonth();
};

export const mapTaskToTodoType = (task) => {
    const type = (task.task_type || task.source_type || "").toUpperCase();
    if (type.includes("QUOTE")) return "quote";
    if (type.includes("PAY")) return "payment";
    if (type.includes("VISIT")) return "visit";
    if (type.includes("APPROVAL")) return "approval";
    if (type.includes("FOLLOW")) return "follow";
    return "reminder";
};

export const calculateDaysBetween = (date) => {
    if (!date) return 0;
    const target = new Date(date);
    if (isNaN(target.getTime())) return 0;
    const diff = Date.now() - target.getTime();
    return Math.max(Math.floor(diff / (1000 * 60 * 60 * 24)), 0);
};

export const transformOpportunity = (opportunity) => {
    const stage = mapOpportunityStage(opportunity.stage || opportunity.opportunity_stage);
    const expectedCloseDate = opportunity.estimated_close_date || opportunity.expected_close_date || "";
    const probability = Number(opportunity.win_probability ?? opportunity.success_rate ?? 0);

    return {
        id: opportunity.id,
        name: opportunity.opportunity_name || opportunity.name || opportunity.opportunity_code || "未命名商机",
        customerName: opportunity.customer?.customer_name || opportunity.customer_name || "",
        customerShort: opportunity.customer?.short_name || opportunity.customer?.customer_name || opportunity.customer_name || "",
        stage,
        priority: mapOpportunityPriority(opportunity.priority),
        expectedAmount: parseFloat(opportunity.est_amount || opportunity.expected_amount || 0),
        expectedCloseDate: expectedCloseDate ? formatDate(expectedCloseDate) : "未设置",
        probability,
        owner: opportunity.owner?.real_name || opportunity.owner_name || opportunity.owner?.username || "未分配",
        daysInStage: calculateDaysBetween(opportunity.stage_updated_at || opportunity.updated_at),
        isHot: probability >= 70,
        isOverdue: expectedCloseDate ? new Date(expectedCloseDate) < new Date() && stage !== "won" : false,
        tags: opportunity.industry ? [opportunity.industry] : []
    };
};

export const transformCustomer = (customer) => ({
    id: customer.id,
    name: customer.customer_name || customer.name || "未命名客户",
    shortName: customer.short_name || customer.customer_name || customer.name || "客户",
    grade: (customer.grade || customer.level || "B").toUpperCase(),
    status: (customer.status || "active").toLowerCase(),
    industry: customer.industry || customer.category || "未分类",
    location: [customer.region, customer.city, customer.address].filter(Boolean).slice(0, 2).join(" · ") || "未设置",
    contactPerson: customer.contact_person || customer.primary_contact?.name,
    phone: customer.contact_phone || customer.primary_contact?.phone,
    totalAmount: parseFloat(customer.total_contract_amount || 0),
    pendingAmount: parseFloat(customer.pending_payment || 0),
    projectCount: customer.project_count || 0,
    opportunityCount: customer.opportunity_count || 0,
    tags: customer.tags || [],
    lastContact: customer.last_follow_up_at ? formatDate(customer.last_follow_up_at) : "无记录",
    createdAt: customer.created_at
});

export const transformInvoiceToPayment = (invoice) => {
    const statusMap = { PAID: "paid", PENDING: "pending", ISSUED: "invoiced", OVERDUE: "overdue" };
    const backendStatus = invoice.payment_status || invoice.status;
    const status = statusMap[backendStatus] || "pending";

    return {
        id: invoice.id,
        type: (invoice.payment_type || "progress").toLowerCase(),
        projectName: invoice.project_name || invoice.contract_name || "未关联项目",
        amount: parseFloat(invoice.amount || invoice.invoice_amount || 0),
        dueDate: invoice.due_date || invoice.payment_due_date || invoice.expected_payment_date || "",
        paidDate: invoice.paid_date || "",
        status,
        invoiceNo: invoice.invoice_code,
        notes: invoice.remark || ""
    };
};

export const transformProject = (project) => ({
    id: project.id || project.project_id,
    name: project.project_name || project.name || project.project_code || "项目",
    customer: project.customer?.customer_name || project.customer_name || "未设置",
    stageLabel: mapProjectStageLabel(project.stage || project.project_stage || project.status),
    progress: Math.round(project.progress_pct ?? project.progress ?? 0),
    health: mapProjectHealth(project.health || project.health_status || project.health_level),
    acceptanceDate: project.acceptance_date || project.delivery_date || project.target_acceptance_date || project.expected_acceptance_date || "未设置"
});

export const transformTaskToTodo = (task) => {
    const deadline = task.deadline || task.plan_end_date;
    const priority = (task.priority || "").toLowerCase();

    return {
        id: `task-${task.id}`,
        type: mapTaskToTodoType(task),
        title: task.title,
        target: task.project_name || task.source_name || task.task_code,
        time: deadline ? formatDate(deadline) : "无截止",
        priority: priority === "urgent" ? "urgent" : priority === "high" ? "high" : "normal",
        done: task.status === "COMPLETED"
    };
};
