// Constants for SalesWorkstation
export const DEFAULT_STATS = {
    monthlyTarget: 1200000,
    monthlyAchieved: 0,
    opportunityCount: 0,
    hotOpportunities: 0,
    pendingPayment: 0,
    overduePayment: 0,
    customerCount: 0,
    newCustomers: 0
};

export const OPPORTUNITY_STAGE_MAP = {
    DISCOVERY: "lead",
    QUALIFIED: "contact",
    PROPOSAL: "quote",
    NEGOTIATION: "negotiate",
    WON: "won",
    LOST: "lost",
    ON_HOLD: "contact"
};

export const PROJECT_STAGE_LABELS = {
    INITIATION: "立项",
    PLAN: "计划",
    DESIGN: "设计",
    PRODUCTION: "生产",
    DELIVERY: "交付",
    ACCEPTANCE: "验收",
    CLOSED: "结项"
};

export const HEALTH_MAP = {
    H1: "good",
    HEALTH_GREEN: "good",
    GREEN: "good",
    H2: "warning",
    HEALTH_YELLOW: "warning",
    YELLOW: "warning",
    H3: "critical",
    HEALTH_RED: "critical",
    RED: "critical"
};

export const todoTypeConfig = {
    follow: { icon: "Phone", color: "text-blue-400", bg: "bg-blue-500/20" },
    quote: { icon: "FileText", color: "text-amber-400", bg: "bg-amber-500/20" },
    payment: { icon: "DollarSign", color: "text-emerald-400", bg: "bg-emerald-500/20" },
    visit: { icon: "Building2", color: "text-purple-400", bg: "bg-purple-500/20" },
    acceptance: { icon: "CheckCircle2", color: "text-pink-400", bg: "bg-pink-500/20" },
    approval: { icon: "CheckCircle2", color: "text-orange-400", bg: "bg-orange-500/20" },
    reminder: { icon: "AlertTriangle", color: "text-red-400", bg: "bg-red-500/20" }
};

export const healthColors = {
    good: "bg-emerald-500",
    warning: "bg-amber-500",
    critical: "bg-red-500"
};
