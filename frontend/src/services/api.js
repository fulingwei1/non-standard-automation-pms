import axios from 'axios';

const api = axios.create({
    baseURL: '/api/v1',
    headers: {
        'Content-Type': 'application/json',
    },
    timeout: 10000, // 10秒超时
});

// Request interceptor for adding auth token
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('token');
        // 如果是演示账号的 token，不发送 Authorization header，避免后端返回 401
        if (token && !token.startsWith('demo_token_')) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// Response interceptor for handling common errors
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response && error.response.status === 401) {
            const token = localStorage.getItem('token');
            const requestUrl = error.config?.url || '';

            // 如果是演示账号的 token，不删除 token，也不重定向
            // 演示账号的 API 调用失败是预期的，因为后端不支持演示账号
            if (token && token.startsWith('demo_token_')) {
                // 对于演示账号，静默处理 401 错误，让页面组件使用 mock 数据
                console.log('演示账号 API 调用失败，将使用 mock 数据');
            } else {
                // 只有在认证相关的 API 返回 401 时才清除 token 并重定向
                // 其他 API 的 401 错误可能是权限问题，不应该导致登出
                const isAuthEndpoint = requestUrl.includes('/auth/');
                if (isAuthEndpoint) {
                    console.log('认证 API 返回 401，清除 token');
                    localStorage.removeItem('token');
                    localStorage.removeItem('user');
                    // Redirect to login
                    if (window.location.pathname !== '/') {
                        window.location.href = '/';
                    }
                } else {
                    // 非认证 API 的 401 错误，只记录日志，不清除 token
                    // 页面组件会使用 mock 数据或显示错误信息
                    console.log('数据 API 返回 401，保持登录状态，使用 mock 数据');
                }
            }
        }
        return Promise.reject(error);
    }
);

export default api;

export const financialCostApi = {
    downloadTemplate: () => api.get('/projects/financial-costs/template', { responseType: 'blob' }),
    uploadCosts: (file) => {
        const formData = new FormData()
        formData.append('file', file)
        return api.post('/projects/financial-costs/upload', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        })
    },
    listCosts: (params) => api.get('/projects/financial-costs', { params }),
    deleteCost: (id) => api.delete(`/projects/financial-costs/${id}`),
};

export const projectWorkspaceApi = {
    getWorkspace: (projectId) => api.get(`/projects/${projectId}/workspace`),
    getBonuses: (projectId) => api.get(`/projects/${projectId}/bonuses`),
    getMeetings: (projectId, params) => api.get(`/projects/${projectId}/meetings`, { params }),
    linkMeeting: (projectId, meetingId, isPrimary) => api.post(`/projects/${projectId}/meetings/${meetingId}/link`, null, { params: { is_primary: isPrimary } }),
    getIssues: (projectId, params) => api.get(`/projects/${projectId}/issues`, { params }),
    getSolutions: (projectId, params) => api.get(`/projects/${projectId}/solutions`, { params }),
};

export const projectContributionApi = {
    getContributions: (projectId, params) => api.get(`/projects/${projectId}/contributions`, { params }),
    rateMember: (projectId, userId, data) => api.post(`/projects/${projectId}/contributions/${userId}/rate`, data),
    getReport: (projectId, params) => api.get(`/projects/${projectId}/contributions/report`, { params }),
    getUserContributions: (userId, params) => api.get(`/users/${userId}/project-contributions`, { params }),
    calculate: (projectId, period) => api.post(`/projects/${projectId}/contributions/calculate`, null, { params: { period } }),
};

export const projectApi = {
    list: (params) => api.get('/projects/', { params }),
    get: (id) => api.get(`/projects/${id}`),
    create: (data) => api.post('/projects/', data),
    update: (id, data) => api.put(`/projects/${id}`, data),
    getMachines: (id) => api.get(`/projects/${id}/machines`),
    getInProductionSummary: (params) => api.get('/projects/in-production/summary', { params }),
    // Sprint 3 & 4: 模板和阶段门校验相关API
    recommendTemplates: (params) => api.get('/projects/templates/recommend', { params }),
    createFromTemplate: (templateId, data) => api.post(`/projects/templates/${templateId}/create-project`, data),
    checkAutoTransition: (id, autoAdvance = false) => api.post(`/projects/${id}/check-auto-transition`, { auto_advance: autoAdvance }),
    getGateCheckResult: (id, targetStage) => api.get(`/projects/${id}/gate-check/${targetStage}`),
    advanceStage: (id, data) => api.post(`/projects/${id}/advance-stage`, data),
    // Sprint 5.3: 缓存管理API
    getCacheStats: () => api.get('/projects/cache/stats'),
    clearCache: (pattern) => api.post('/projects/cache/clear', null, { params: pattern ? { pattern } : {} }),
    resetCacheStats: () => api.post('/projects/cache/reset-stats'),
    // Sprint 3.3: 项目详情页增强
    getStatusLogs: (id, params) => api.get(`/projects/${id}/status-logs`, { params }),
    getHealthDetails: (id) => api.get(`/projects/${id}/health-details`),
    // Sprint 3.2: 项目经理统计
    getStats: (params) => api.get('/projects/stats', { params }),
};

export const machineApi = {
    list: (params) => api.get('/machines/', { params }),
    get: (id) => api.get(`/machines/${id}`),
    create: (data) => api.post('/machines/', data),
    update: (id, data) => api.put(`/machines/${id}`, data),
    delete: (id) => api.delete(`/machines/${id}`),
    getBom: (id) => api.get(`/machines/${id}/bom`),
    getServiceHistory: (id, params) => api.get(`/machines/${id}/service-history`, { params }),
    // 文档管理
    uploadDocument: (machineId, formData) => api.post(`/machines/${machineId}/documents/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
    }),
    getDocuments: (machineId, params) => api.get(`/machines/${machineId}/documents`, { params }),
    downloadDocument: (machineId, docId) => api.get(`/machines/${machineId}/documents/${docId}/download`, {
        responseType: 'blob',
    }),
    getDocumentVersions: (machineId, docId) => api.get(`/machines/${machineId}/documents/${docId}/versions`),
};

export const stageApi = {
    list: (projectId) => api.get('/stages/', { params: { project_id: projectId } }),
    get: (id) => api.get(`/stages/${id}`),
    statuses: (stageId) => api.get('/stages/statuses', { params: { stage_id: stageId } }),
};

export const milestoneApi = {
    list: (projectId) => api.get('/milestones/', { params: { project_id: projectId } }),
    get: (id) => api.get(`/milestones/${id}`),
    create: (data) => api.post('/milestones/', data),
    update: (id, data) => api.put(`/milestones/${id}`, data),
    complete: (id, data) => api.put(`/milestones/${id}/complete`, data || {}),
};

export const memberApi = {
    list: (projectId) => api.get('/members/', { params: { project_id: projectId } }),
    add: (data) => api.post('/members/', data),
    remove: (id) => api.delete(`/members/${id}`),
    batchAdd: (projectId, data) => api.post(`/projects/${projectId}/members/batch`, data),
    checkConflicts: (projectId, userId, params) => api.get(`/projects/${projectId}/members/conflicts`, { params: { user_id: userId, ...params } }),
    getDeptUsers: (projectId, deptId) => api.get(`/projects/${projectId}/members/from-dept/${deptId}`),
    notifyDeptManager: (projectId, memberId) => api.post(`/projects/${projectId}/members/${memberId}/notify-dept-manager`),
    update: (memberId, data) => api.put(`/project-members/${memberId}`, data),
};

export const costApi = {
    list: (params) => api.get('/costs/', { params }),
    get: (id) => api.get(`/costs/${id}`),
    create: (data) => api.post('/costs/', data),
    update: (id, data) => api.put(`/costs/${id}`, data),
    delete: (id) => api.delete(`/costs/${id}`),
    getProjectCosts: (projectId, params) => api.get(`/costs/projects/${projectId}/costs`, { params }),
    getProjectSummary: (projectId) => api.get(`/costs/projects/${projectId}/costs/summary`),
};

export const documentApi = {
    list: (projectId) => api.get('/documents/', { params: { project_id: projectId } }),
    create: (data) => api.post('/documents/', data),
};

export const authApi = {
    login: (formData) => {
        // FastAPI的OAuth2PasswordRequestForm需要application/x-www-form-urlencoded格式
        if (formData instanceof URLSearchParams) {
            return api.post('/auth/login', formData.toString(), {
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
            });
        }
        // 如果已经是FormData，使用multipart/form-data
        return api.post('/auth/login', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
    },
    me: () => api.get('/auth/me'),
    refresh: () => api.post('/auth/refresh'),
    logout: () => api.post('/auth/logout'),
    changePassword: (data) => api.put('/auth/password', data),
};

export const userApi = {
    list: (params) => api.get('/users/', { params }),
    get: (id) => api.get(`/users/${id}`),
    create: (data) => api.post('/users/', data),
    update: (id, data) => api.put(`/users/${id}`, data),
    delete: (id) => api.delete(`/users/${id}`),
    assignRoles: (id, roleIds) => api.put(`/users/${id}/roles`, roleIds),
};

export const roleApi = {
    list: (params) => api.get('/roles/', { params }),
    get: (id) => api.get(`/roles/${id}`),
    create: (data) => api.post('/roles/', data),
    update: (id, data) => api.put(`/roles/${id}`, data),
    assignPermissions: (id, permissionIds) => api.put(`/roles/${id}/permissions`, permissionIds),
    permissions: () => api.get('/roles/permissions'),
    // 菜单配置相关
    getNavGroups: (id) => api.get(`/roles/${id}/nav-groups`),
    updateNavGroups: (id, navGroups) => api.put(`/roles/${id}/nav-groups`, navGroups),
    getMyNavGroups: () => api.get('/roles/my/nav-groups'),
    getAllConfig: () => api.get('/roles/config/all'),
};

export const customerApi = {
    list: (params) => api.get('/customers/', { params }),
    get: (id) => api.get(`/customers/${id}`),
    create: (data) => api.post('/customers/', data),
    update: (id, data) => api.put(`/customers/${id}`, data),
    delete: (id) => api.delete(`/customers/${id}`),
    getProjects: (id, params) => api.get(`/customers/${id}/projects`, { params }),
    get360: (id) => api.get(`/customers/${id}/360`),
};

export const supplierApi = {
    list: (params) => api.get('/suppliers/', { params }),
    get: (id) => api.get(`/suppliers/${id}`),
    create: (data) => api.post('/suppliers/', data),
    update: (id, data) => api.put(`/suppliers/${id}`, data),
    updateRating: (id, params) => api.put(`/suppliers/${id}/rating`, null, { params }),
    getMaterials: (id, params) => api.get(`/suppliers/${id}/materials`, { params }),
};

export const orgApi = {
    departments: (params) => api.get('/org/departments', { params }),
    departmentTree: (params) => api.get('/org/departments/tree', { params }),
    createDepartment: (data) => api.post('/org/departments', data),
    updateDepartment: (id, data) => api.put(`/org/departments/${id}`, data),
    getDepartment: (id) => api.get(`/org/departments/${id}`),
    getDepartmentUsers: (id, params) => api.get(`/org/departments/${id}/users`, { params }),
    employees: () => api.get('/org/employees'),
};

// Sales Module APIs
export const leadApi = {
    list: (params) => api.get('/sales/leads', { params }),
    get: (id) => api.get(`/sales/leads/${id}`),
    create: (data) => api.post('/sales/leads', data),
    update: (id, data) => api.put(`/sales/leads/${id}`, data),
    getFollowUps: (id) => api.get(`/sales/leads/${id}/follow-ups`),
    createFollowUp: (id, data) => api.post(`/sales/leads/${id}/follow-ups`, data),
    convert: (id, customerId, requirementData, skipValidation) => api.post(`/sales/leads/${id}/convert`, requirementData, { 
        params: { customer_id: customerId, skip_validation: skipValidation || false } 
    }),
};

export const opportunityApi = {
    list: (params) => api.get('/sales/opportunities', { params }),
    get: (id) => api.get(`/sales/opportunities/${id}`),
    create: (data) => api.post('/sales/opportunities', data),
    update: (id, data) => api.put(`/sales/opportunities/${id}`, data),
    submitGate: (id, data, gateType) => api.post(`/sales/opportunities/${id}/gate`, data, { 
        params: { gate_type: gateType || 'G2' } 
    }),
};

export const quoteApi = {
    list: (params) => api.get('/sales/quotes', { params }),
    get: (id) => api.get(`/sales/quotes/${id}`),
    create: (data) => api.post('/sales/quotes', data),
    update: (id, data) => api.put(`/sales/quotes/${id}`, data),
    createVersion: (id, data) => api.post(`/sales/quotes/${id}/versions`, data),
    getVersions: (id) => api.get(`/sales/quotes/${id}/versions`),
    approve: (id, data) => api.post(`/sales/quotes/${id}/approve`, data),
    // Approval Workflow APIs (Sprint 2)
    startApproval: (id) => api.post(`/sales/quotes/${id}/approval/start`),
    getApprovalStatus: (id) => api.get(`/sales/quotes/${id}/approval-status`),
    approvalAction: (id, data) => api.post(`/sales/quotes/${id}/approval/action`, data),
    getApprovalHistory: (id) => api.get(`/sales/quotes/${id}/approval-history`),
    // Quote Items APIs
    getItems: (id, versionId) => api.get(`/sales/quotes/${id}/items`, { params: { version_id: versionId } }),
    createItem: (id, data, versionId) => api.post(`/sales/quotes/${id}/items`, data, { params: { version_id: versionId } }),
    updateItem: (id, itemId, data) => api.put(`/sales/quotes/${id}/items/${itemId}`, data),
    deleteItem: (id, itemId) => api.delete(`/sales/quotes/${id}/items/${itemId}`),
    batchUpdateItems: (id, data, versionId) => api.put(`/sales/quotes/${id}/items/batch`, data, { params: { version_id: versionId } }),
    // Cost Management APIs
    getCostBreakdown: (id) => api.get(`/sales/quotes/${id}/cost-breakdown`),
    applyCostTemplate: (id, templateId, versionId, adjustments) => api.post(`/sales/quotes/${id}/apply-template`, adjustments || {}, { params: { template_id: templateId, version_id: versionId } }),
    calculateCost: (id, versionId) => api.post(`/sales/quotes/${id}/calculate-cost`, null, { params: { version_id: versionId } }),
    checkCost: (id, versionId) => api.get(`/sales/quotes/${id}/cost-check`, { params: { version_id: versionId } }),
    submitCostApproval: (id, data) => api.post(`/sales/quotes/${id}/cost-approval/submit`, data),
    approveCost: (id, approvalId, data) => api.post(`/sales/quotes/${id}/cost-approval/${approvalId}/approve`, data),
    rejectCost: (id, approvalId, data) => api.post(`/sales/quotes/${id}/cost-approval/${approvalId}/reject`, data),
    getCostApprovalHistory: (id) => api.get(`/sales/quotes/${id}/cost-approval/history`),
    compareCosts: (id, params) => api.get(`/sales/quotes/${id}/cost-comparison`, { params }),
    getCostTrend: (id, params) => api.get(`/sales/quotes/${id}/cost-trend`, { params }),
    getCostStructure: (id, versionId) => api.get(`/sales/quotes/${id}/cost-structure`, { params: { version_id: versionId } }),
    getCostMatchSuggestions: (id, versionId) => api.post(`/sales/quotes/${id}/items/auto-match-cost-suggestions`, null, { params: { version_id: versionId } }),
    applyCostSuggestions: (id, versionId, data) => api.post(`/sales/quotes/${id}/items/apply-cost-suggestions`, data, { params: { version_id: versionId } }),
};

export const salesTemplateApi = {
    listQuoteTemplates: (params) => api.get('/sales/quote-templates', { params }),
    createQuoteTemplate: (data) => api.post('/sales/quote-templates', data),
    updateQuoteTemplate: (id, data) => api.put(`/sales/quote-templates/${id}`, data),
    createQuoteVersion: (id, data) => api.post(`/sales/quote-templates/${id}/versions`, data),
    publishQuoteVersion: (templateId, versionId) => api.post(`/sales/quote-templates/${templateId}/versions/${versionId}/publish`),
    applyQuoteTemplate: (id, data) => api.post(`/sales/quote-templates/${id}/apply`, data || {}),
    listContractTemplates: (params) => api.get('/sales/contract-templates', { params }),
    createContractTemplate: (data) => api.post('/sales/contract-templates', data),
    updateContractTemplate: (id, data) => api.put(`/sales/contract-templates/${id}`, data),
    createContractVersion: (id, data) => api.post(`/sales/contract-templates/${id}/versions`, data),
    publishContractVersion: (templateId, versionId) => api.post(`/sales/contract-templates/${templateId}/versions/${versionId}/publish`),
    applyContractTemplate: (id, params) => api.get(`/sales/contract-templates/${id}/apply`, { params }),
    listRuleSets: (params) => api.get('/sales/cpq/rule-sets', { params }),
    createRuleSet: (data) => api.post('/sales/cpq/rule-sets', data),
    updateRuleSet: (id, data) => api.put(`/sales/cpq/rule-sets/${id}`, data),
    previewPrice: (data) => api.post('/sales/cpq/price-preview', data),
    // Cost Template APIs
    listCostTemplates: (params) => api.get('/sales/cost-templates', { params }),
    getCostTemplate: (id) => api.get(`/sales/cost-templates/${id}`),
    createCostTemplate: (data) => api.post('/sales/cost-templates', data),
    updateCostTemplate: (id, data) => api.put(`/sales/cost-templates/${id}`, data),
    deleteCostTemplate: (id) => api.delete(`/sales/cost-templates/${id}`),
    // Purchase Material Cost APIs
    listPurchaseMaterialCosts: (params) => api.get('/sales/purchase-material-costs', { params }),
    getPurchaseMaterialCost: (id) => api.get(`/sales/purchase-material-costs/${id}`),
    createPurchaseMaterialCost: (data) => api.post('/sales/purchase-material-costs', data),
    updatePurchaseMaterialCost: (id, data) => api.put(`/sales/purchase-material-costs/${id}`, data),
    deletePurchaseMaterialCost: (id) => api.delete(`/sales/purchase-material-costs/${id}`),
    matchMaterialCost: (data) => api.post('/sales/purchase-material-costs/match', data),
    getCostUpdateReminder: () => api.get('/sales/purchase-material-costs/reminder'),
    updateCostUpdateReminder: (data) => api.put('/sales/purchase-material-costs/reminder', data),
    acknowledgeCostUpdateReminder: () => api.post('/sales/purchase-material-costs/reminder/acknowledge'),
};

export const contractApi = {
    list: (params) => api.get('/sales/contracts', { params }),
    get: (id) => api.get(`/sales/contracts/${id}`),
    create: (data) => api.post('/sales/contracts', data),
    update: (id, data) => api.put(`/sales/contracts/${id}`, data),
    sign: (id, data) => api.post(`/sales/contracts/${id}/sign`, data),
    createProject: (id, data) => api.post(`/sales/contracts/${id}/project`, data),
    getDeliverables: (id) => api.get(`/sales/contracts/${id}/deliverables`),
    // Approval Workflow APIs (Sprint 2)
    startApproval: (id) => api.post(`/sales/contracts/${id}/approval/start`),
    getApprovalStatus: (id) => api.get(`/sales/contracts/${id}/approval-status`),
    approvalAction: (id, data) => api.post(`/sales/contracts/${id}/approval/action`, data),
    getApprovalHistory: (id) => api.get(`/sales/contracts/${id}/approval-history`),
};

export const invoiceApi = {
    list: (params) => api.get('/sales/invoices', { params }),
    get: (id) => api.get(`/sales/invoices/${id}`),
    create: (data) => api.post('/sales/invoices', data),
    update: (id, data) => api.put(`/sales/invoices/${id}`, data),
    issue: (id, data) => api.post(`/sales/invoices/${id}/issue`, data),
    receivePayment: (id, data) => api.post(`/sales/invoices/${id}/receive-payment`, null, { params: data }),
    approve: (id, params) => api.put(`/sales/invoices/${id}/approve`, null, { params }),
    getApprovals: (id) => api.get(`/sales/invoices/${id}/approvals`),
    approveApproval: (approvalId, params) => api.put(`/sales/invoice-approvals/${approvalId}/approve`, null, { params }),
    rejectApproval: (approvalId, params) => api.put(`/sales/invoice-approvals/${approvalId}/reject`, null, { params }),
    // Approval Workflow APIs (Sprint 2)
    startApproval: (id) => api.post(`/sales/invoices/${id}/approval/start`),
    getApprovalStatus: (id) => api.get(`/sales/invoices/${id}/approval-status`),
    approvalAction: (id, data) => api.post(`/sales/invoices/${id}/approval/action`, data),
    getApprovalHistory: (id) => api.get(`/sales/invoices/${id}/approval-history`),
};

export const paymentApi = {
    list: (params) => api.get('/sales/payments', { params }),
    get: (id) => api.get(`/sales/payments/${id}`),
    create: (params) => api.post('/sales/payments', null, { params }),
    matchInvoice: (id, params) => api.put(`/sales/payments/${id}/match-invoice`, null, { params }),
};

export const receivableApi = {
    list: (params) => api.get('/sales/receivables/overdue', { params }),
    getAging: (params) => api.get('/sales/receivables/aging', { params }),
    getSummary: (params) => api.get('/sales/receivables/summary', { params }),
};

export const disputeApi = {
    list: (params) => api.get('/sales/disputes', { params }),
    get: (id) => api.get(`/sales/disputes/${id}`),
    create: (data) => api.post('/sales/disputes', data),
    update: (id, data) => api.put(`/sales/disputes/${id}`, data),
};

export const salesStatisticsApi = {
    funnel: (params) => api.get('/sales/statistics/funnel', { params }),
    opportunitiesByStage: () => api.get('/sales/statistics/opportunities-by-stage'),
    revenueForecast: (params) => api.get('/sales/statistics/revenue-forecast', { params }),
    summary: (params) => api.get('/sales/statistics/summary', { params }),
};

// Alert Management APIs
export const alertApi = {
    // Alert Records
    list: (params) => api.get('/alerts', { params }),
    get: (id) => api.get(`/alerts/${id}`),
    acknowledge: (id) => api.put(`/alerts/${id}/acknowledge`),
    resolve: (id, data) => api.put(`/alerts/${id}/resolve`, data),
    close: (id, data) => api.put(`/alerts/${id}/close`, data),
    ignore: (id, data) => api.put(`/alerts/${id}/ignore`, data),
    
    // Alert Rules
    rules: {
        list: (params) => api.get('/alert-rules', { params }),
        get: (id) => api.get(`/alert-rules/${id}`),
        create: (data) => api.post('/alert-rules', data),
        update: (id, data) => api.put(`/alert-rules/${id}`, data),
        delete: (id) => api.delete(`/alert-rules/${id}`),
        toggle: (id) => api.put(`/alert-rules/${id}/toggle`),
    },
    
    // Alert Rule Templates
    templates: (params) => api.get('/alert-rule-templates', { params }),
    
    // Alert Statistics
    statistics: (params) => api.get('/alerts/statistics', { params }),
    dashboard: () => api.get('/alerts/statistics/dashboard'),
    trends: (params) => api.get('/alerts/statistics/trends', { params }),
    responseMetrics: (params) => api.get('/alerts/statistics/response-metrics', { params }),
    efficiencyMetrics: (params) => api.get('/alerts/statistics/efficiency-metrics', { params }),
    exportExcel: (params) => api.get('/alerts/export/excel', { params, responseType: 'blob' }),
    exportPdf: (params) => api.get('/alerts/export/pdf', { params, responseType: 'blob' }),
    
    // Alert Subscriptions
    subscriptions: {
        list: (params) => api.get('/alerts/subscriptions', { params }),
        get: (id) => api.get(`/alerts/subscriptions/${id}`),
        create: (data) => api.post('/alerts/subscriptions', data),
        update: (id, data) => api.put(`/alerts/subscriptions/${id}`, data),
        delete: (id) => api.delete(`/alerts/subscriptions/${id}`),
        toggle: (id) => api.put(`/alerts/subscriptions/${id}/toggle`),
    },
};

// Progress & Task Management APIs
export const progressApi = {
    // Tasks - Note: Tasks are project-specific, use project_id in params
    tasks: {
        list: (params) => {
            // If project_id is provided, use project-specific endpoint
            if (params?.project_id) {
                return api.get(`/projects/${params.project_id}/tasks`, { params: { ...params, project_id: undefined } });
            }
            // Otherwise, need to fetch from all projects (not directly supported)
            return Promise.reject(new Error('project_id is required'));
        },
        get: (id) => api.get(`/tasks/${id}`),
        create: (projectId, data) => api.post(`/projects/${projectId}/tasks`, data),
        update: (id, data) => api.put(`/tasks/${id}`, data),
        delete: (id) => api.delete(`/tasks/${id}`),
        updateProgress: (id, data) => api.put(`/tasks/${id}/progress`, data),
        updateAssignee: (id, data) => api.put(`/tasks/${id}/assignee`, data),
        complete: (id) => api.put(`/tasks/${id}/complete`),
    },
    
    // Progress Reports
    reports: {
        list: (params) => api.get('/progress-reports', { params }),
        create: (data) => api.post('/progress-reports', data),
        get: (id) => api.get(`/progress-reports/${id}`),
        getSummary: (projectId) => api.get(`/projects/${projectId}/progress-summary`),
        getGantt: (projectId) => api.get(`/projects/${projectId}/gantt`),
        getBoard: (projectId) => api.get(`/projects/${projectId}/progress-board`),
        getMilestoneRate: (projectId) => api.get('/reports/milestone-rate', { params: projectId ? { project_id: projectId } : {} }),
        getDelayReasons: (projectId, topN = 10) => api.get('/reports/delay-reasons', { params: { project_id: projectId, top_n: topN } }),
    },
    analytics: {
        getForecast: (projectId) => api.get(`/progress/projects/${projectId}/progress-forecast`),
        checkDependencies: (projectId) => api.get(`/progress/projects/${projectId}/dependency-check`),
    },
    // WBS Templates
    wbsTemplates: {
        list: (params) => api.get('/wbs-templates', { params }),
        get: (id) => api.get(`/wbs-templates/${id}`),
        create: (data) => api.post('/wbs-templates', data),
        update: (id, data) => api.put(`/wbs-templates/${id}`, data),
        delete: (id) => api.delete(`/wbs-templates/${id}`),
        getTasks: (templateId) => api.get(`/wbs-templates/${templateId}/tasks`),
        addTask: (templateId, data) => api.post(`/wbs-templates/${templateId}/tasks`, data),
        updateTask: (taskId, data) => api.put(`/wbs-template-tasks/${taskId}`, data),
    },
    
    // Projects WBS Init
    projects: {
        initWBS: (projectId, data) => api.post(`/projects/${projectId}/init-wbs`, data),
    },
};

// Customer Service APIs
export const serviceApi = {
    tickets: {
        list: (params) => api.get('/service-tickets', { params }),
        get: (id) => api.get(`/service-tickets/${id}`),
        create: (data) => api.post('/service-tickets', data),
        update: (id, data) => api.put(`/service-tickets/${id}`, data),
        assign: (id, data) => api.put(`/service-tickets/${id}/assign`, data),
        batchAssign: (data) => api.post('/service-tickets/batch-assign', data),
        close: (id, data) => api.put(`/service-tickets/${id}/close`, data),
        getStatistics: () => api.get('/service-tickets/statistics'),
    },
    records: {
        list: (params) => api.get('/service-records', { params }),
        get: (id) => api.get(`/service-records/${id}`),
        create: (data) => api.post('/service-records', data),
        update: (id, data) => api.put(`/service-records/${id}`, data),
        uploadPhoto: (recordId, file, description) => {
            const formData = new FormData();
            formData.append('file', file);
            if (description) formData.append('description', description);
            return api.post(`/service-records/${recordId}/photos`, formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
        },
        deletePhoto: (recordId, photoIndex) => api.delete(`/service-records/${recordId}/photos/${photoIndex}`),
        getStatistics: () => api.get('/service-records/statistics'),
    },
    communications: {
        list: (params) => api.get('/customer-communications', { params }),
        get: (id) => api.get(`/customer-communications/${id}`),
        create: (data) => api.post('/customer-communications', data),
        update: (id, data) => api.put(`/customer-communications/${id}`, data),
    },
    satisfaction: {
        list: (params) => api.get('/customer-satisfactions', { params }),
        get: (id) => api.get(`/customer-satisfactions/${id}`),
        create: (data) => api.post('/customer-satisfactions', data),
        update: (id, data) => api.put(`/customer-satisfactions/${id}`, data),
        send: (id, data) => api.post(`/customer-satisfactions/${id}/send`, data),
        submit: (id, data) => api.post(`/customer-satisfactions/${id}/submit`, data),
        statistics: () => api.get('/customer-satisfactions/statistics'),
        templates: {
            list: (params) => api.get('/satisfaction-templates', { params }),
            get: (id) => api.get(`/satisfaction-templates/${id}`),
        },
    },
    dashboardStatistics: () => api.get('/service/dashboard-statistics'),
    knowledgeBase: {
        list: (params) => api.get('/knowledge-base', { params }),
        get: (id) => api.get(`/knowledge-base/${id}`),
        create: (data) => api.post('/knowledge-base', data),
        update: (id, data) => api.put(`/knowledge-base/${id}`, data),
        delete: (id) => api.delete(`/knowledge-base/${id}`),
        publish: (id) => api.put(`/knowledge-base/${id}/publish`),
        archive: (id) => api.put(`/knowledge-base/${id}/archive`),
        statistics: () => api.get('/knowledge-base/statistics'),
    },
};

// Installation Dispatch APIs
export const installationDispatchApi = {
    orders: {
        list: (params) => api.get('/installation-dispatch/orders', { params }),
        get: (id) => api.get(`/installation-dispatch/orders/${id}`),
        create: (data) => api.post('/installation-dispatch/orders', data),
        update: (id, data) => api.put(`/installation-dispatch/orders/${id}`, data),
        assign: (id, data) => api.put(`/installation-dispatch/orders/${id}/assign`, data),
        batchAssign: (data) => api.post('/installation-dispatch/orders/batch-assign', data),
        start: (id, data) => api.put(`/installation-dispatch/orders/${id}/start`, data),
        progress: (id, data) => api.put(`/installation-dispatch/orders/${id}/progress`, data),
        complete: (id, data) => api.put(`/installation-dispatch/orders/${id}/complete`, data),
        cancel: (id) => api.put(`/installation-dispatch/orders/${id}/cancel`),
    },
    statistics: () => api.get('/installation-dispatch/statistics'),
};

// Issue Management APIs
export const issueApi = {
    list: (params) => api.get('/issues', { params }),
    get: (id) => api.get(`/issues/${id}`),
    create: (data) => api.post('/issues', data),
    update: (id, data) => api.put(`/issues/${id}`, data),
    delete: (id) => api.delete(`/issues/${id}`),
    assign: (id, data) => api.post(`/issues/${id}/assign`, data),
    resolve: (id, data) => api.post(`/issues/${id}/resolve`, data),
    verify: (id, data) => api.post(`/issues/${id}/verify`, data),
    close: (id, data) => api.post(`/issues/${id}/close`, data),
    cancel: (id, data) => api.post(`/issues/${id}/cancel`, data),
    changeStatus: (id, data) => api.post(`/issues/${id}/status`, data),
    getStatistics: (params) => api.get('/issues/statistics/overview', { params }),
    getTrend: (params) => api.get('/issues/statistics/trend', { params }),
    getEngineerStatistics: (params) => api.get('/issues/statistics/engineer', { params }),
    getCauseAnalysis: (params) => api.get('/issues/statistics/cause-analysis', { params }),
    getSnapshots: (params) => api.get('/issues/statistics/snapshots', { params }),
    getSnapshot: (id) => api.get(`/issues/statistics/snapshots/${id}`),
    getFollowUps: (id) => api.get(`/issues/${id}/follow-ups`),
    addFollowUp: (id, data) => api.post(`/issues/${id}/follow-ups`, data),
    getRelated: (id) => api.get(`/issues/${id}/related`),
    createRelated: (id, data) => api.post(`/issues/${id}/related`, data),
    batchAssign: (data) => api.post('/issues/batch-assign', data),
    batchStatus: (data) => api.post('/issues/batch-status', data),
    batchClose: (data) => api.post('/issues/batch-close', data),
    export: (params) => api.get('/issues/export', { params, responseType: 'blob' }),
    import: (file) => {
        const formData = new FormData();
        formData.append('file', file);
        return api.post('/issues/import', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        });
    },
    getBoard: (params) => api.get('/issues/board', { params }),
};

// Acceptance Management APIs
export const acceptanceApi = {
    // Templates
    templates: {
        list: (params) => api.get('/acceptance-templates', { params }),
        get: (id) => api.get(`/acceptance-templates/${id}`),
        create: (data) => api.post('/acceptance-templates', data),
        getItems: (id) => api.get(`/acceptance-templates/${id}/items`),
        addItems: (id, data) => api.post(`/acceptance-templates/${id}/items`, data),
    },
    
    // Orders
    orders: {
        list: (params) => api.get('/acceptance-orders', { params }),
        get: (id) => api.get(`/acceptance-orders/${id}`),
        create: (data) => api.post('/acceptance-orders', data),
        start: (id, data) => api.put(`/acceptance-orders/${id}/start`, data),
        complete: (id, data) => api.put(`/acceptance-orders/${id}/complete`, data),
        getItems: (id) => api.get(`/acceptance-orders/${id}/items`),
        updateItem: (itemId, data) => api.put(`/acceptance-items/${itemId}`, data),
    },
    
    // Issues
    issues: {
        list: (orderId) => api.get(`/acceptance-orders/${orderId}/issues`),
        create: (orderId, data) => api.post(`/acceptance-orders/${orderId}/issues`, data),
        update: (issueId, data) => api.put(`/acceptance-issues/${issueId}`, data),
        close: (issueId, data) => api.put(`/acceptance-issues/${issueId}/close`, data),
        addFollowUp: (issueId, data) => api.post(`/acceptance-issues/${issueId}/follow-ups`, data),
    },
    
    // Signatures
    signatures: {
        list: (orderId) => api.get(`/acceptance-orders/${orderId}/signatures`),
        create: (orderId, data) => api.post(`/acceptance-orders/${orderId}/signatures`, data),
    },
    
    // Reports
    reports: {
        generate: (orderId, data) => api.post(`/acceptance-orders/${orderId}/report`, data),
        download: (reportId) => api.get(`/acceptance-reports/${reportId}/download`, { responseType: 'blob' }),
    },
};

// Purchase Management APIs
export const purchaseApi = {
    orders: {
        list: (params) => api.get('/purchase-orders', { params }),
        get: (id) => api.get(`/purchase-orders/${id}`),
        create: (data) => api.post('/purchase-orders', data),
        update: (id, data) => api.put(`/purchase-orders/${id}`, data),
        submit: (id) => api.put(`/purchase-orders/${id}/submit`),
        approve: (id, data) => api.put(`/purchase-orders/${id}/approve`, data),
        getItems: (id) => api.get(`/purchase-orders/${id}/items`),
        createFromBOM: (params) => api.post('/purchase-orders/from-bom', null, { params }),
    },
    
    requests: {
        list: (params) => api.get('/purchase-orders/requests', { params }),
        get: (id) => api.get(`/purchase-orders/requests/${id}`),
        create: (data) => api.post('/purchase-orders/requests', data),
        update: (id, data) => api.put(`/purchase-orders/requests/${id}`, data),
        submit: (id) => api.put(`/purchase-orders/requests/${id}/submit`),
        approve: (id, data) => api.put(`/purchase-orders/requests/${id}/approve`, { params: data }),
        generateOrders: (id, params) => api.post(`/purchase-orders/requests/${id}/generate-orders`, null, { params }),
        delete: (id) => api.delete(`/purchase-orders/requests/${id}`),
    },
    
    receipts: {
        list: (params) => api.get('/goods-receipts', { params }),
        get: (id) => api.get(`/goods-receipts/${id}`),
        create: (data) => api.post('/goods-receipts', data),
        getItems: (id) => api.get(`/goods-receipts/${id}/items`),
        receive: (id, data) => api.put(`/goods-receipts/${id}/receive`, null, { params: data }),
        updateStatus: (id, status) => api.put(`/goods-receipts/${id}/receive`, null, { params: { status } }),
        inspectItem: (receiptId, itemId, data) => api.put(`/goods-receipts/${receiptId}/items/${itemId}/inspect`, null, { params: data }),
    },
    
    items: {
        receive: (itemId, data) => api.put(`/purchase-order-items/${itemId}/receive`, data),
    },
    
    // Kit Rate
    kitRate: {
        getProject: (projectId, params) => api.get(`/projects/${projectId}/kit-rate`, { params }),
        getMachine: (machineId, params) => api.get(`/machines/${machineId}/kit-rate`, { params }),
        getMachineStatus: (machineId) => api.get(`/machines/${machineId}/material-status`),
        getProjectMaterialStatus: (projectId) => api.get(`/projects/${projectId}/material-status`),
        dashboard: (params) => api.get('/kit-rate/dashboard', { params }),
        trend: (params) => api.get('/kit-rate/trend', { params }),
    },
};

// PMO Management APIs
export const pmoApi = {
    // Dashboard
    dashboard: () => api.get('/pmo/dashboard'),
    weeklyReport: (params) => api.get('/pmo/weekly-report', { params }),
    resourceOverview: () => api.get('/pmo/resource-overview'),
    riskWall: () => api.get('/pmo/risk-wall'),
    
    // Initiation Management
    initiations: {
        list: (params) => api.get('/pmo/initiations', { params }),
        get: (id) => api.get(`/pmo/initiations/${id}`),
        create: (data) => api.post('/pmo/initiations', data),
        update: (id, data) => api.put(`/pmo/initiations/${id}`, data),
        submit: (id) => api.put(`/pmo/initiations/${id}/submit`),
        approve: (id, data) => api.put(`/pmo/initiations/${id}/approve`, data),
        reject: (id, data) => api.put(`/pmo/initiations/${id}/reject`, data),
    },
    
    // Project Phases
    phases: {
        list: (projectId) => api.get(`/pmo/projects/${projectId}/phases`),
        entryCheck: (phaseId, data) => api.post(`/pmo/phases/${phaseId}/entry-check`, data),
        exitCheck: (phaseId, data) => api.post(`/pmo/phases/${phaseId}/exit-check`, data),
        review: (phaseId, data) => api.post(`/pmo/phases/${phaseId}/review`, data),
        advance: (phaseId, data) => api.put(`/pmo/phases/${phaseId}/advance`, data),
    },
    
    // Risk Management
    risks: {
        list: (projectId, params) => api.get(`/pmo/projects/${projectId}/risks`, { params }),
        get: (id) => api.get(`/pmo/risks/${id}`),
        create: (projectId, data) => api.post(`/pmo/projects/${projectId}/risks`, data),
        assess: (riskId, data) => api.put(`/pmo/risks/${riskId}/assess`, data),
        response: (riskId, data) => api.put(`/pmo/risks/${riskId}/response`, data),
        updateStatus: (riskId, data) => api.put(`/pmo/risks/${riskId}/status`, data),
        close: (riskId, data) => api.put(`/pmo/risks/${riskId}/close`, data),
    },
    
    // Project Closure
    closures: {
        create: (projectId, data) => api.post(`/pmo/projects/${projectId}/closure`, data),
        get: (projectId) => api.get(`/pmo/projects/${projectId}/closure`),
        review: (closureId, data) => api.put(`/pmo/closures/${closureId}/review`, data),
        updateLessons: (closureId, data) => api.put(`/pmo/closures/${closureId}/lessons`, data),
    },
    
    // Meeting Management
    meetings: {
        list: (params) => api.get('/pmo/meetings', { params }),
        get: (id) => api.get(`/pmo/meetings/${id}`),
        create: (data) => api.post('/pmo/meetings', data),
        update: (id, data) => api.put(`/pmo/meetings/${id}`, data),
        updateMinutes: (id, data) => api.put(`/pmo/meetings/${id}/minutes`, data),
        getActions: (id) => api.get(`/pmo/meetings/${id}/actions`),
    },
};

// Production Management APIs
export const shortageApi = {
    // 缺料上报
    reports: {
        list: (params) => api.get('/shortage/reports', { params }),
        get: (id) => api.get(`/shortage/reports/${id}`),
        create: (data) => api.post('/shortage/reports', data),
        confirm: (id) => api.put(`/shortage/reports/${id}/confirm`),
        handle: (id, data) => api.put(`/shortage/reports/${id}/handle`, data),
        resolve: (id) => api.put(`/shortage/reports/${id}/resolve`),
    },
    // 到货跟踪
    arrivals: {
        list: (params) => api.get('/shortage/arrivals', { params }),
        get: (id) => api.get(`/shortage/arrivals/${id}`),
        create: (data) => api.post('/shortage/arrivals', data),
        updateStatus: (id, status) => api.put(`/shortage/arrivals/${id}/status`, { status }),
        createFollowUp: (id, data) => api.post(`/shortage/arrivals/${id}/follow-up`, data),
        getFollowUps: (id, params) => api.get(`/shortage/arrivals/${id}/follow-ups`, { params }),
        receive: (id, receivedQty) => api.post(`/shortage/arrivals/${id}/receive`, { received_qty: receivedQty }),
        getDelayed: (params) => api.get('/shortage/arrivals/delayed', { params }),
    },
    // 物料替代
    substitutions: {
        list: (params) => api.get('/shortage/substitutions', { params }),
        get: (id) => api.get(`/shortage/substitutions/${id}`),
        create: (data) => api.post('/shortage/substitutions', data),
        techApprove: (id, approved, note) => api.put(`/shortage/substitutions/${id}/tech-approve`, { approved, approval_note: note }),
        prodApprove: (id, approved, note) => api.put(`/shortage/substitutions/${id}/prod-approve`, { approved, approval_note: note }),
        execute: (id, note) => api.put(`/shortage/substitutions/${id}/execute`, { execution_note: note }),
    },
    // 物料调拨
    transfers: {
        list: (params) => api.get('/shortage/transfers', { params }),
        get: (id) => api.get(`/shortage/transfers/${id}`),
        create: (data) => api.post('/shortage/transfers', data),
        approve: (id, approved, note) => api.put(`/shortage/transfers/${id}/approve`, { approved, approval_note: note }),
        execute: (id, actualQty, note) => api.put(`/shortage/transfers/${id}/execute`, { actual_qty: actualQty, execution_note: note }),
    },
    // 统计分析
    statistics: {
        dashboard: () => api.get('/shortage/dashboard'),
        supplierDelivery: (params) => api.get('/shortage/supplier-delivery', { params }),
        dailyReport: (date) => api.get('/shortage/daily-report', { params: { report_date: date } }),
        latestDailyReport: () => api.get('/shortage/daily-report/latest'),
        dailyReportByDate: (date) => api.get('/shortage/daily-report/by-date', { params: { report_date: date } }),
    },
};

export const productionApi = {
    dashboard: () => api.get('/production/dashboard'),
    reports: {
        daily: (params) => api.get('/production-daily-reports', { params }),
        latestDaily: () => api.get('/production-daily-reports/latest'),
    },
    workshops: {
        list: (params) => api.get('/workshops', { params }),
        get: (id) => api.get(`/workshops/${id}`),
        create: (data) => api.post('/workshops', data),
        update: (id, data) => api.put(`/workshops/${id}`, data),
        getWorkstations: (id) => api.get(`/production/workshops/${id}/workstations`),
        addWorkstation: (id, data) => api.post(`/production/workshops/${id}/workstations`, data),
    },
    workstations: {
        list: (params) => api.get('/workstations', { params }),
        get: (id) => api.get(`/workstations/${id}`),
        getStatus: (id) => api.get(`/workstations/${id}/status`),
    },
    productionPlans: {
        list: (params) => api.get('/production-plans', { params }),
        get: (id) => api.get(`/production-plans/${id}`),
        create: (data) => api.post('/production-plans', data),
        update: (id, data) => api.put(`/production-plans/${id}`, data),
        submit: (id) => api.put(`/production/production-plans/${id}/submit`),
        approve: (id) => api.put(`/production/production-plans/${id}/approve`),
        publish: (id) => api.put(`/production-plans/${id}/publish`),
        calendar: (params) => api.get('/production-plans/calendar', { params }),
    },
    workOrders: {
        list: (params) => api.get('/work-orders', { params }),
        get: (id) => api.get(`/work-orders/${id}`),
        create: (data) => api.post('/work-orders', data),
        update: (id, data) => api.put(`/work-orders/${id}`, data),
        assign: (id, data) => api.put(`/work-orders/${id}/assign`, data),
        start: (id) => api.put(`/work-orders/${id}/start`),
        pause: (id) => api.put(`/work-orders/${id}/pause`),
        resume: (id) => api.put(`/work-orders/${id}/resume`),
        complete: (id, data) => api.put(`/work-orders/${id}/complete`, data),
        getProgress: (id) => api.get(`/work-orders/${id}/progress`),
        getReports: (id) => api.get('/work-reports', { params: { work_order_id: id, page_size: 1000 } }),
    },
    workers: {
        list: (params) => api.get('/workers', { params }),
        get: (id) => api.get(`/workers/${id}`),
        create: (data) => api.post('/workers', data),
        update: (id, data) => api.put(`/workers/${id}`, data),
    },
    workReports: {
        list: (params) => api.get('/work-reports', { params }),
        get: (id) => api.get(`/work-reports/${id}`),
        create: (data) => api.post('/work-reports', data),
        start: (data) => api.post('/production/work-reports/start', data),
        progress: (data) => api.post('/production/work-reports/progress', data),
        complete: (data) => api.post('/production/work-reports/complete', data),
        approve: (id) => api.put(`/work-reports/${id}/approve`),
        my: (params) => api.get('/work-reports/my', { params }),
    },
    materialRequisitions: {
        list: (params) => api.get('/material-requisitions', { params }),
        get: (id) => api.get(`/material-requisitions/${id}`),
        create: (data) => api.post('/material-requisitions', data),
        approve: (id, data) => api.put(`/material-requisitions/${id}/approve`, data),
        issue: (id, data) => api.put(`/material-requisitions/${id}/issue`, data),
    },
    exceptions: {
        list: (params) => api.get('/production-exceptions', { params }),
        get: (id) => api.get(`/production-exceptions/${id}`),
        create: (data) => api.post('/production-exceptions', data),
        handle: (id, data) => api.put(`/production-exceptions/${id}/handle`, data),
        close: (id) => api.put(`/production-exceptions/${id}/close`),
    },
    taskBoard: (workshopId) => api.get(`/workshops/${workshopId}/task-board`),
    reports: {
        workerPerformance: (params) => api.get('/production/reports/worker-performance', { params }),
        workerRanking: (params) => api.get('/production/reports/worker-ranking', { params }),
    },
};

// Material Management APIs
export const materialApi = {
    list: (params) => api.get('/materials/', { params }),
    get: (id) => api.get(`/materials/${id}`),
    create: (data) => api.post('/materials/', data),
    update: (id, data) => api.put(`/materials/${id}`, data),
    search: (params) => api.get('/materials/search', { params }),
    warehouse: {
        statistics: () => api.get('/materials/warehouse/statistics'),
    },
    categories: {
        list: (params) => api.get('/materials/categories/', { params }),
    },
    search: (params) => api.get('/materials/search', { params }),
    warehouse: {
        statistics: () => api.get('/materials/warehouse/statistics'),
    },
};

// Material Demand APIs
export const materialDemandApi = {
    list: (params) => api.get('/material-demands', { params }),
    getVsStock: (materialId, params) => api.get(`/material-demands/vs-stock`, {
        params: { material_id: materialId, ...params }
    }),
    getSchedule: (params) => api.get('/material-demands/schedule', { params }),
    generatePR: (params) => api.post('/material-demands/generate-pr', null, { params }),
};

// Shortage Alert APIs
export const shortageAlertApi = {
    list: (params) => api.get('/shortage-alerts', { params }),
    get: (id) => api.get(`/shortage-alerts/${id}`),
    acknowledge: (id) => api.put(`/shortage-alerts/${id}/acknowledge`),
    resolve: (id, data) => api.put(`/shortage-alerts/${id}/resolve`, data),
    getSummary: (params) => api.get('/shortage-alerts/summary', { params }),
};

// ECN Management APIs
export const ecnApi = {
    list: (params) => api.get('/ecns', { params }),
    get: (id) => api.get(`/ecns/${id}`),
    create: (data) => api.post('/ecns', data),
    update: (id, data) => api.put(`/ecns/${id}`, data),
    submit: (id, data) => api.put(`/ecns/${id}/submit`, data || {}),
    cancel: (id) => api.put(`/ecns/${id}/cancel`),
    // Evaluations
    getEvaluations: (id) => api.get(`/ecns/${id}/evaluations`),
    createEvaluation: (id, data) => api.post(`/ecns/${id}/evaluations`, data),
    getEvaluation: (evalId) => api.get(`/ecn-evaluations/${evalId}`),
    submitEvaluation: (evalId) => api.put(`/ecn-evaluations/${evalId}/submit`),
    getEvaluationSummary: (id) => api.get(`/ecns/${id}/evaluation-summary`),
    // Approvals
    getApprovals: (id) => api.get(`/ecns/${id}/approvals`),
    createApproval: (id, data) => api.post(`/ecns/${id}/approvals`, data),
    getApproval: (approvalId) => api.get(`/ecn-approvals/${approvalId}`),
    approve: (approvalId, comment) => api.put(`/ecn-approvals/${approvalId}/approve`, null, { params: { approval_comment: comment } }),
    reject: (approvalId, reason) => api.put(`/ecn-approvals/${approvalId}/reject`, null, { params: { reason } }),
    // Tasks
    getTasks: (id) => api.get(`/ecns/${id}/tasks`),
    createTask: (id, data) => api.post(`/ecns/${id}/tasks`, data),
    getTask: (taskId) => api.get(`/ecn-tasks/${taskId}`),
    updateTaskProgress: (taskId, progress) => api.put(`/ecn-tasks/${taskId}/progress`, null, { params: { progress } }),
    completeTask: (taskId) => api.put(`/ecn-tasks/${taskId}/complete`),
    // Affected materials
    getAffectedMaterials: (id) => api.get(`/ecns/${id}/affected-materials`),
    createAffectedMaterial: (id, data) => api.post(`/ecns/${id}/affected-materials`, data),
    updateAffectedMaterial: (id, materialId, data) => api.put(`/ecns/${id}/affected-materials/${materialId}`, data),
    deleteAffectedMaterial: (id, materialId) => api.delete(`/ecns/${id}/affected-materials/${materialId}`),
    // Affected orders
    getAffectedOrders: (id) => api.get(`/ecns/${id}/affected-orders`),
    createAffectedOrder: (id, data) => api.post(`/ecns/${id}/affected-orders`, data),
    updateAffectedOrder: (id, orderId, data) => api.put(`/ecns/${id}/affected-orders/${orderId}`, data),
    deleteAffectedOrder: (id, orderId) => api.delete(`/ecns/${id}/affected-orders/${orderId}`),
    // Execution
    startExecution: (id, data) => api.put(`/ecns/${id}/start-execution`, data || {}),
    verify: (id, data) => api.put(`/ecns/${id}/verify`, data),
    close: (id, data) => api.put(`/ecns/${id}/close`, data || {}),
    // BOM Analysis
    analyzeBomImpact: (id, params) => api.post(`/ecns/${id}/analyze-bom-impact`, null, { params }),
    getBomImpactSummary: (id) => api.get(`/ecns/${id}/bom-impact-summary`),
    checkObsoleteRisk: (id) => api.post(`/ecns/${id}/check-obsolete-risk`),
    getObsoleteAlerts: (id) => api.get(`/ecns/${id}/obsolete-material-alerts`),
    // Responsibility Allocation
    createResponsibilityAnalysis: (id, data) => api.post(`/ecns/${id}/responsibility-analysis`, data),
    getResponsibilitySummary: (id) => api.get(`/ecns/${id}/responsibility-summary`),
    // RCA Analysis
    updateRcaAnalysis: (id, data) => api.put(`/ecns/${id}/rca-analysis`, data),
    getRcaAnalysis: (id) => api.get(`/ecns/${id}/rca-analysis`),
    // Knowledge Base
    extractSolution: (id, autoExtract = true) => api.post(`/ecns/${id}/extract-solution`, { auto_extract: autoExtract }),
    getSimilarEcns: (id, params) => api.get(`/ecns/${id}/similar-ecns`, { params }),
    recommendSolutions: (id, params) => api.get(`/ecns/${id}/recommend-solutions`, { params }),
    createSolutionTemplate: (id, data) => api.post(`/ecns/${id}/create-solution-template`, data),
    applySolutionTemplate: (id, templateId) => api.post(`/ecns/${id}/apply-solution-template`, { template_id: templateId }),
    listSolutionTemplates: (params) => api.get('/ecn-solution-templates', { params }),
    getSolutionTemplate: (templateId) => api.get(`/ecn-solution-templates/${templateId}`),
    // ECN Types
    getEcnTypes: (params) => api.get('/ecn-types', { params }),
    getEcnType: (typeId) => api.get(`/ecn-types/${typeId}`),
    createEcnType: (data) => api.post('/ecn-types', data),
    updateEcnType: (typeId, data) => api.put(`/ecn-types/${typeId}`, data),
    deleteEcnType: (typeId) => api.delete(`/ecn-types/${typeId}`),
    // Overdue alerts
    getOverdueAlerts: () => api.get('/ecns/overdue-alerts'),
    batchProcessOverdueAlerts: (alerts) => api.post('/ecns/batch-process-overdue-alerts', alerts),
    // Module integration
    syncToBom: (id) => api.post(`/ecns/${id}/sync-to-bom`),
    syncToProject: (id) => api.post(`/ecns/${id}/sync-to-project`),
    syncToPurchase: (id) => api.post(`/ecns/${id}/sync-to-purchase`),
    // Logs
    getLogs: (id) => api.get(`/ecns/${id}/logs`),
    // Statistics
    getStatistics: (params) => api.get('/ecns/statistics', { params }),
    // Batch operations
    batchSyncToBom: (ecnIds) => api.post('/ecns/batch-sync-to-bom', ecnIds),
    batchSyncToProject: (ecnIds) => api.post('/ecns/batch-sync-to-project', ecnIds),
    batchSyncToPurchase: (ecnIds) => api.post('/ecns/batch-sync-to-purchase', ecnIds),
    batchCreateTasks: (ecnId, tasks) => api.post(`/ecns/${ecnId}/batch-create-tasks`, tasks),
};

// Presales APIs
export const presaleApi = {
    tickets: {
        list: (params) => api.get('/presale/tickets', { params }),
        get: (id) => api.get(`/presale/tickets/${id}`),
        create: (data) => api.post('/presale/tickets', data),
        update: (id, data) => api.put(`/presale/tickets/${id}`, data),
        accept: (id, data) => api.put(`/presale/tickets/${id}/accept`, data),
        updateProgress: (id, data) => api.put(`/presale/tickets/${id}/progress`, data),
        complete: (id, data) => api.put(`/presale/tickets/${id}/complete`, data),
        rate: (id, data) => api.put(`/presale/tickets/${id}/rate`, data),
        getBoard: (params) => api.get('/presale/tickets/board', { params }),
    },
    solutions: {
        list: (params) => api.get('/presale/solutions', { params }),
        get: (id) => api.get(`/presale/solutions/${id}`),
        create: (data) => api.post('/presale/solutions', data),
        update: (id, data) => api.put(`/presale/solutions/${id}`, data),
        review: (id, data) => api.put(`/presale/solutions/${id}/review`, data),
        getVersions: (id) => api.get(`/presale/solutions/${id}/versions`),
        getCost: (id) => api.get(`/presale/solutions/${id}/cost`),
    },
    templates: {
        list: (params) => api.get('/presale/templates', { params }),
        get: (id) => api.get(`/presale/templates/${id}`),
        create: (data) => api.post('/presale/templates', data),
        update: (id, data) => api.put(`/presale/templates/${id}`, data),
    },
    tenders: {
        list: (params) => api.get('/presale/tenders', { params }),
        get: (id) => api.get(`/presale/tenders/${id}`),
        create: (data) => api.post('/presale/tenders', data),
        update: (id, data) => api.put(`/presale/tenders/${id}`, data),
        updateResult: (id, data) => api.put(`/presale/tenders/${id}/result`, data),
    },
    statistics: {
        workload: (params) => api.get('/presale/stats/workload', { params }),
        responseTime: (params) => api.get('/presale/stats/response-time', { params }),
        conversion: (params) => api.get('/presale/stats/conversion', { params }),
        performance: (params) => api.get('/presale/stats/performance', { params }),
    },
};

// BOM Management APIs
export const bomApi = {
    getByMachine: (machineId) => api.get(`/bom/machines/${machineId}/bom`).then(res => {
        // Get the latest BOM from the list
        const bomList = res.data || res || []
        if (bomList.length > 0) {
            // Find the latest BOM (is_latest = true or most recent)
            const latestBom = bomList.find(bom => bom.is_latest) || bomList[0]
            return { data: latestBom }
        }
        return { data: null }
    }),
    list: (params) => api.get('/bom/', { params }),
    get: (id) => api.get(`/bom/${id}`),
    create: (machineId, data) => api.post(`/bom/machines/${machineId}/bom`, data),
    update: (id, data) => api.put(`/bom/${id}`, data),
    // BOM Items
    getItems: (bomId) => api.get(`/bom/${bomId}/items`),
    addItem: (bomId, data) => api.post(`/bom/${bomId}/items`, data),
    updateItem: (itemId, data) => api.put(`/bom/items/${itemId}`, data),
    deleteItem: (itemId) => api.delete(`/bom/items/${itemId}`),
    // BOM Versions
    getVersions: (bomId) => api.get(`/bom/${bomId}/versions`),
    compareVersions: (bomId, version1Id, version2Id) => api.get(`/bom/${bomId}/versions/compare`, {
        params: { version1_id: version1Id, version2_id: version2Id }
    }),
    // BOM Operations
    release: (bomId, changeNote) => api.post(`/bom/${bomId}/release`, null, {
        params: { change_note: changeNote }
    }),
    // BOM Import/Export
    import: (bomId, file) => {
        const formData = new FormData();
        formData.append('file', file);
        return api.post(`/bom/${bomId}/import`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        });
    },
    export: (bomId) => api.get(`/bom/${bomId}/export`, { responseType: 'blob' }),
    // Generate Purchase Requirements
    generatePR: (bomId, params) => api.post(`/bom/${bomId}/generate-pr`, null, { params }),
};

// Notification Management APIs
export const notificationApi = {
    list: (params) => api.get('/notifications', { params }),
    get: (id) => api.get(`/notifications/${id}`),
    getUnreadCount: () => api.get('/notifications/unread-count'),
    markRead: (id) => api.put(`/notifications/${id}/read`),
    batchRead: (data) => api.put('/notifications/batch-read', data),
    readAll: () => api.put('/notifications/read-all'),
    delete: (id) => api.delete(`/notifications/${id}`),
    getSettings: () => api.get('/notifications/settings'),
    updateSettings: (data) => api.put('/notifications/settings', data),
};

// Task Center APIs (Personal Task Center)
export const taskCenterApi = {
    getOverview: () => api.get('/task-center/overview'),
    myTasks: (params) => api.get('/task-center/my-tasks', { params }),
    getMyTasks: (params) => api.get('/task-center/my-tasks', { params }),
    getTask: (id) => api.get(`/task-center/tasks/${id}`),
    createTask: (data) => api.post('/task-center/tasks', data),
    updateTask: (id, data) => api.put(`/task-center/tasks/${id}`, data),
    updateProgress: (id, data) => api.put(`/task-center/tasks/${id}/progress`, data),
    completeTask: (id) => api.put(`/task-center/tasks/${id}/complete`),
    transferTask: (id, data) => api.post(`/task-center/tasks/${id}/transfer`, data),
    acceptTransfer: (id) => api.put(`/task-center/tasks/${id}/accept`),
    rejectTransfer: (id) => api.put(`/task-center/tasks/${id}/reject`),
    addComment: (id, data) => api.post(`/task-center/tasks/${id}/comments`, data),
    getComments: (id) => api.get(`/task-center/tasks/${id}/comments`),
};

// Workload Management APIs
export const workloadApi = {
    user: (userId, params) => api.get(`/workload/user/${userId}`, { params }),
    team: (params) => api.get('/workload/team', { params }),
    dashboard: (params) => api.get('/workload/dashboard', { params }),
    heatmap: (params) => api.get('/workload/heatmap', { params }),
    availableResources: (params) => api.get('/workload/available-resources', { params }),
    gantt: (params) => api.get('/workload/gantt', { params }),
};


// Outsourcing Management APIs
export const outsourcingApi = {
    vendors: {
        list: (params) => api.get('/outsourcing-vendors', { params }),
        get: (id) => api.get(`/outsourcing-vendors/${id}`),
        create: (data) => api.post('/outsourcing-vendors', data),
        update: (id, data) => api.put(`/outsourcing-vendors/${id}`, data),
        evaluate: (id, data) => api.post(`/outsourcing-vendors/${id}/evaluations`, data),
    },
    orders: {
        list: (params) => api.get('/outsourcing-orders', { params }),
        get: (id) => api.get(`/outsourcing-orders/${id}`),
        create: (data) => api.post('/outsourcing-orders', data),
        update: (id, data) => api.put(`/outsourcing-orders/${id}`, data),
        submit: (id) => api.put(`/outsourcing-orders/${id}/submit`),
        approve: (id, data) => api.put(`/outsourcing-orders/${id}/approve`, data),
        getItems: (id) => api.get(`/outsourcing-orders/${id}/items`),
        addItem: (id, data) => api.post(`/outsourcing-orders/${id}/items`, data),
        updateItem: (itemId, data) => api.put(`/outsourcing-order-items/${itemId}`, data),
        getDeliveries: (id) => api.get('/outsourcing-deliveries', { params: { order_id: id, page_size: 1000 } }),
        getInspections: (id) => api.get('/outsourcing-inspections', { params: { order_id: id, page_size: 1000 } }),
        getProgress: (id) => api.get(`/outsourcing-orders/${id}/progress-logs`),
    },
    deliveries: {
        list: (orderId) => api.get(`/outsourcing-orders/${orderId}/deliveries`),
        create: (orderId, data) => api.post(`/outsourcing-orders/${orderId}/deliveries`, data),
        get: (id) => api.get(`/outsourcing-deliveries/${id}`),
    },
    inspections: {
        list: (orderId) => api.get(`/outsourcing-orders/${orderId}/inspections`),
        create: (orderId, data) => api.post(`/outsourcing-orders/${orderId}/inspections`, data),
        get: (id) => api.get(`/outsourcing-inspections/${id}`),
    },
    progress: {
        list: (orderId) => api.get(`/outsourcing-orders/${orderId}/progress`),
        create: (orderId, data) => api.post(`/outsourcing-orders/${orderId}/progress`, data),
    },
    payments: {
        list: (orderId) => api.get(`/outsourcing-orders/${orderId}/payments`),
        create: (orderId, data) => api.post(`/outsourcing-orders/${orderId}/payments`, data),
        update: (id, data) => api.put(`/outsourcing-payments/${id}`, data),
    },
};

// Business Support APIs
export const businessSupportApi = {
    dashboard: () => api.get('/business-support/dashboard'),
    getActiveContracts: (params) => api.get('/business-support/dashboard/active-contracts', { params }),
    getActiveBidding: (params) => api.get('/business-support/dashboard/active-bidding', { params }),
    getTodos: (params) => api.get('/business-support/dashboard/todos', { params }),
    bidding: {
        list: (params) => api.get('/business-support/bidding', { params }),
        get: (id) => api.get(`/business-support/bidding/${id}`),
        create: (data) => api.post('/business-support/bidding', data),
        update: (id, data) => api.put(`/business-support/bidding/${id}`, data),
    },
    contractReview: {
        list: (params) => api.get('/business-support/contract-review', { params }),
        get: (id) => api.get(`/business-support/contract-review/${id}`),
        create: (data) => api.post('/business-support/contract-review', data),
        update: (id, data) => api.put(`/business-support/contract-review/${id}`, data),
    },
    paymentReminder: {
        list: (params) => api.get('/business-support/payment-reminder', { params }),
        get: (id) => api.get(`/business-support/payment-reminder/${id}`),
        create: (data) => api.post('/business-support/payment-reminder', data),
        update: (id, data) => api.put(`/business-support/payment-reminder/${id}`, data),
    },
    deliveryOrders: {
        list: (params) => api.get('/business-support/delivery-orders', { params }),
        get: (id) => api.get(`/business-support/delivery-orders/${id}`),
        create: (data) => api.post('/business-support/delivery-orders', data),
        update: (id, data) => api.put(`/business-support/delivery-orders/${id}`, data),
        statistics: () => api.get('/business-support/delivery-orders/statistics'),
    },
    salesOrders: {
        list: (params) => api.get('/business-support/sales-orders', { params }),
        get: (id) => api.get(`/business-support/sales-orders/${id}`),
    },
};

// Exception Management APIs
export const exceptionApi = {
    list: (params) => api.get('/exceptions', { params }),
    get: (id) => api.get(`/exceptions/${id}`),
    create: (data) => api.post('/exceptions', data),
    update: (id, data) => api.put(`/exceptions/${id}`, data),
    delete: (id) => api.delete(`/exceptions/${id}`),
    getStatistics: (params) => api.get('/exceptions/statistics', { params }),
};

// Kit Check APIs
export const kitCheckApi = {
    list: (params) => api.get('/kit-checks', { params }),
    get: (id) => api.get(`/kit-checks/${id}`),
    create: (data) => api.post('/kit-checks', data),
    update: (id, data) => api.put(`/kit-checks/${id}`, data),
    delete: (id) => api.delete(`/kit-checks/${id}`),
    getStatistics: (params) => api.get('/kit-checks/statistics', { params }),
};

// Employee Management APIs
export const employeeApi = {
    list: (params) => api.get('/employees', { params }),
    get: (id) => api.get(`/employees/${id}`),
    create: (data) => api.post('/employees', data),
    update: (id, data) => api.put(`/employees/${id}`, data),
    delete: (id) => api.delete(`/employees/${id}`),
    getStatistics: (params) => api.get('/employees/statistics', { params }),
};

// Department Management APIs
export const departmentApi = {
    list: (params) => api.get('/departments', { params }),
    get: (id) => api.get(`/departments/${id}`),
    create: (data) => api.post('/departments', data),
    update: (id, data) => api.put(`/departments/${id}`, data),
    delete: (id) => api.delete(`/departments/${id}`),
    getStatistics: (params) => api.get('/departments/statistics', { params }),
};

// Issue Template APIs
export const issueTemplateApi = {
    list: (params) => api.get('/issue-templates', { params }),
    get: (id) => api.get(`/issue-templates/${id}`),
    create: (data) => api.post('/issue-templates', data),
    update: (id, data) => api.put(`/issue-templates/${id}`, data),
    delete: (id) => api.delete(`/issue-templates/${id}`),
    createIssue: (templateId, data) => api.post(`/issue-templates/${templateId}/create-issue`, data),
};

// Project Review APIs (项目复盘)
export const projectReviewApi = {
    // 复盘报告
    list: (params) => api.get('/projects/project-reviews', { params }),
    get: (id) => api.get(`/projects/project-reviews/${id}`),
    create: (data) => api.post('/projects/project-reviews', data),
    update: (id, data) => api.put(`/projects/project-reviews/${id}`, data),
    delete: (id) => api.delete(`/projects/project-reviews/${id}`),
    publish: (id) => api.put(`/projects/project-reviews/${id}/publish`),
    archive: (id) => api.put(`/projects/project-reviews/${id}/archive`),
    
    // 经验教训
    getLessons: (reviewId, params) => api.get(`/projects/project-reviews/${reviewId}/lessons`, { params }),
    createLesson: (reviewId, data) => api.post(`/projects/project-reviews/${reviewId}/lessons`, data),
    getLesson: (lessonId) => api.get(`/projects/project-reviews/lessons/${lessonId}`),
    updateLesson: (lessonId, data) => api.put(`/projects/project-reviews/lessons/${lessonId}`, data),
    deleteLesson: (lessonId) => api.delete(`/projects/project-reviews/lessons/${lessonId}`),
    resolveLesson: (lessonId) => api.put(`/projects/project-reviews/lessons/${lessonId}/resolve`),
    
    // 最佳实践
    getBestPractices: (reviewId, params) => api.get(`/projects/project-reviews/${reviewId}/best-practices`, { params }),
    createBestPractice: (reviewId, data) => api.post(`/projects/project-reviews/${reviewId}/best-practices`, data),
    getBestPractice: (practiceId) => api.get(`/projects/project-reviews/best-practices/${practiceId}`),
    updateBestPractice: (practiceId, data) => api.put(`/projects/project-reviews/best-practices/${practiceId}`, data),
    deleteBestPractice: (practiceId) => api.delete(`/projects/project-reviews/best-practices/${practiceId}`),
    validateBestPractice: (practiceId, data) => api.put(`/projects/project-reviews/best-practices/${practiceId}/validate`, data),
    reuseBestPractice: (practiceId, data) => api.post(`/projects/project-reviews/best-practices/${practiceId}/reuse`, data),
    
    // 最佳实践库
    searchBestPractices: (params) => api.get('/projects/best-practices', { params }),
    getBestPracticeCategories: () => api.get('/projects/best-practices/categories'),
    getBestPracticeStatistics: () => api.get('/projects/best-practices/statistics'),
    
    // 项目经验教训（从结项记录提取）
    getProjectLessons: (projectId) => api.get(`/projects/${projectId}/lessons-learned`),
    
    // 经验教训高级管理
    searchLessonsLearned: (params) => api.get('/projects/lessons-learned', { params }),
    getLessonsStatistics: (params) => api.get('/projects/lessons-learned/statistics', { params }),
    getLessonCategories: () => api.get('/projects/lessons-learned/categories'),
    updateLessonStatus: (lessonId, status) => api.put(`/projects/project-reviews/lessons/${lessonId}/status`, { new_status: status }),
    batchUpdateLessons: (lessonIds, updateData) => api.post('/projects/project-reviews/lessons/batch-update', { lesson_ids: lessonIds, update_data: updateData }),
    
    // 最佳实践高级管理
    recommendBestPractices: (data) => api.post('/projects/best-practices/recommend', data),
    getProjectBestPracticeRecommendations: (projectId, limit) => api.get(`/projects/${projectId}/best-practices/recommend`, { params: { limit } }),
    applyBestPractice: (practiceId, targetProjectId, notes) => api.post(`/projects/project-reviews/best-practices/${practiceId}/apply`, { target_project_id: targetProjectId, notes }),
    getPopularBestPractices: (params) => api.get('/projects/best-practices/popular', { params }),
};

// Technical Review APIs (技术评审)
export const technicalReviewApi = {
    // 评审主表
    list: (params) => api.get('/technical-reviews', { params }),
    get: (id) => api.get(`/technical-reviews/${id}`),
    create: (data) => api.post('/technical-reviews', data),
    update: (id, data) => api.put(`/technical-reviews/${id}`, data),
    delete: (id) => api.delete(`/technical-reviews/${id}`),
    
    // 评审参与人
    getParticipants: (reviewId) => api.get(`/technical-reviews/${reviewId}/participants`),
    addParticipant: (reviewId, data) => api.post(`/technical-reviews/${reviewId}/participants`, data),
    updateParticipant: (participantId, data) => api.put(`/technical-reviews/participants/${participantId}`, data),
    deleteParticipant: (participantId) => api.delete(`/technical-reviews/participants/${participantId}`),
    
    // 评审材料
    getMaterials: (reviewId) => api.get(`/technical-reviews/${reviewId}/materials`),
    addMaterial: (reviewId, data) => api.post(`/technical-reviews/${reviewId}/materials`, data),
    deleteMaterial: (materialId) => api.delete(`/technical-reviews/materials/${materialId}`),
    
    // 检查项记录
    getChecklistRecords: (reviewId) => api.get(`/technical-reviews/${reviewId}/checklist-records`),
    createChecklistRecord: (reviewId, data) => api.post(`/technical-reviews/${reviewId}/checklist-records`, data),
    updateChecklistRecord: (recordId, data) => api.put(`/technical-reviews/checklist-records/${recordId}`, data),
    
    // 评审问题
    getIssues: (params) => api.get('/technical-reviews/issues', { params }),
    createIssue: (reviewId, data) => api.post(`/technical-reviews/${reviewId}/issues`, data),
    updateIssue: (issueId, data) => api.put(`/technical-reviews/issues/${issueId}`, data),
};

// Engineers Progress Visibility APIs (工程师跨部门进度可见性)
export const engineersApi = {
    // 获取项目的跨部门进度可见性视图
    getProgressVisibility: (projectId) => api.get(`/engineers/projects/${projectId}/progress-visibility`),
};

// Technical Assessment APIs (技术评估)
export const technicalAssessmentApi = {
    // 申请技术评估
    applyForLead: (leadId, data) => api.post(`/sales/leads/${leadId}/assessments/apply`, data),
    applyForOpportunity: (oppId, data) => api.post(`/sales/opportunities/${oppId}/assessments/apply`, data),
    
    // 执行技术评估
    evaluate: (assessmentId, data) => api.post(`/sales/assessments/${assessmentId}/evaluate`, data),
    
    // 获取评估列表
    getLeadAssessments: (leadId) => api.get(`/sales/leads/${leadId}/assessments`),
    getOpportunityAssessments: (oppId) => api.get(`/sales/opportunities/${oppId}/assessments`),
    
    // 获取评估详情
    get: (assessmentId) => api.get(`/sales/assessments/${assessmentId}`),
    
    // 评分规则管理
    getScoringRules: () => api.get('/sales/scoring-rules'),
    createScoringRule: (data) => api.post('/sales/scoring-rules', data),
    activateScoringRule: (ruleId) => api.put(`/sales/scoring-rules/${ruleId}/activate`),
    
    // 失败案例库
    getFailureCases: (params) => api.get('/sales/failure-cases', { params }),
    getFailureCase: (id) => api.get(`/sales/failure-cases/${id}`),
    createFailureCase: (data) => api.post('/sales/failure-cases', data),
    updateFailureCase: (id, data) => api.put(`/sales/failure-cases/${id}`, data),
    findSimilarCases: (params) => api.get('/sales/failure-cases/similar', { params }),
    
    // 未决事项
    getOpenItems: (params) => api.get('/sales/open-items', { params }),
    createOpenItemForLead: (leadId, data) => api.post(`/sales/leads/${leadId}/open-items`, data),
    createOpenItemForOpportunity: (oppId, data) => api.post(`/sales/opportunities/${oppId}/open-items`, data),
    updateOpenItem: (itemId, data) => api.put(`/sales/open-items/${itemId}`, data),
    closeOpenItem: (itemId) => api.post(`/sales/open-items/${itemId}/close`),
    
    // 需求详情管理
    getRequirementDetail: (leadId) => api.get(`/sales/leads/${leadId}/requirement-detail`),
    createRequirementDetail: (leadId, data) => api.post(`/sales/leads/${leadId}/requirement-detail`, data),
    updateRequirementDetail: (leadId, data) => api.put(`/sales/leads/${leadId}/requirement-detail`, data),
    
    // 需求冻结管理
    getRequirementFreezes: (sourceType, sourceId) => {
        const path = sourceType === 'lead' 
            ? `/sales/leads/${sourceId}/requirement-freezes`
            : `/sales/opportunities/${sourceId}/requirement-freezes`;
        return api.get(path);
    },
    createRequirementFreeze: (sourceType, sourceId, data) => {
        const path = sourceType === 'lead'
            ? `/sales/leads/${sourceId}/requirement-freezes`
            : `/sales/opportunities/${sourceId}/requirement-freezes`;
        return api.post(path, data);
    },
    
    // AI澄清管理
    getAIClarifications: (params) => api.get('/sales/ai-clarifications', { params }),
    createAIClarificationForLead: (leadId, data) => api.post(`/sales/leads/${leadId}/ai-clarifications`, data),
    createAIClarificationForOpportunity: (oppId, data) => api.post(`/sales/opportunities/${oppId}/ai-clarifications`, data),
    updateAIClarification: (clarificationId, data) => api.put(`/sales/ai-clarifications/${clarificationId}`, data),
    getAIClarification: (clarificationId) => api.get(`/sales/ai-clarifications/${clarificationId}`),
};

// ==================== 绩效管理 API ====================

export const performanceApi = {
    // ========== 员工端 API ==========

    // 月度工作总结
    createMonthlySummary: (data) => api.post('/performance/monthly-summary', data),
    saveMonthlySummaryDraft: (period, data) => api.put('/performance/monthly-summary/draft', data, {
        params: { period }
    }),
    getMonthlySummaryHistory: (params) => api.get('/performance/monthly-summary/history', { params }),

    // 我的绩效
    getMyPerformance: () => api.get('/performance/my-performance'),

    // ========== 经理端 API ==========

    // 待评价任务
    getEvaluationTasks: (params) => api.get('/performance/evaluation-tasks', { params }),
    getEvaluationDetail: (taskId) => api.get(`/performance/evaluation/${taskId}`),
    submitEvaluation: (taskId, data) => api.post(`/performance/evaluation/${taskId}`, data),

    // ========== HR 端 API ==========

    // 权重配置
    getWeightConfig: () => api.get('/performance/weight-config'),
    updateWeightConfig: (data) => api.put('/performance/weight-config', data),
    
    // 融合绩效
    getIntegratedPerformance: (userId, params) => api.get(`/performance/integrated/${userId}`, { params }),
    calculateIntegratedPerformance: (params) => api.post('/performance/calculate-integrated', null, { params }),
};

// Bonus APIs (奖金激励)
export const bonusApi = {
    // 我的奖金
    getMyBonus: () => api.get('/bonus/my'),
    getMyBonusStatistics: (params) => api.get('/bonus/statistics', { params }),
    
    // 奖金计算记录
    getCalculations: (params) => api.get('/bonus/calculations', { params }),
    getCalculation: (id) => api.get(`/bonus/calculations/${id}`),
    
    // 奖金发放记录
    getDistributions: (params) => api.get('/bonus/distributions', { params }),
    getDistribution: (id) => api.get(`/bonus/distributions/${id}`),
    
    // 计算奖金（需要权限）
    calculateSalesBonus: (data) => api.post('/bonus/calculate/sales', data),
    calculateSalesDirectorBonus: (data) => api.post('/bonus/calculate/sales-director', data),
    calculatePresaleBonus: (data) => api.post('/bonus/calculate/presale', data),
    calculatePerformanceBonus: (data) => api.post('/bonus/calculate/performance', data),
    calculateProjectBonus: (data) => api.post('/bonus/calculate/project', data),
    calculateMilestoneBonus: (data) => api.post('/bonus/calculate/milestone', data),
    calculateTeamBonus: (data) => api.post('/bonus/calculate/team', data),
};

// Qualification APIs (任职资格管理)
export const qualificationApi = {
    // 等级管理
    getLevels: (params) => api.get('/qualifications/levels', { params }),
    getLevel: (id) => api.get(`/qualifications/levels/${id}`),
    createLevel: (data) => api.post('/qualifications/levels', data),
    updateLevel: (id, data) => api.put(`/qualifications/levels/${id}`, data),
    deleteLevel: (id) => api.delete(`/qualifications/levels/${id}`),
    
    // 能力模型管理
    getModels: (params) => api.get('/qualifications/models', { params }),
    getModel: (positionType, levelId, params) => api.get(`/qualifications/models/${positionType}/${levelId}`, { params }),
    getModelById: (id) => api.get(`/qualifications/models/${id}`),
    createModel: (data) => api.post('/qualifications/models', data),
    updateModel: (id, data) => api.put(`/qualifications/models/${id}`, data),
    
    // 员工任职资格
    getEmployeeQualification: (employeeId, params) => api.get(`/qualifications/employees/${employeeId}`, { params }),
    getEmployeeQualifications: (params) => api.get('/qualifications/employees', { params }),
    certifyEmployee: (employeeId, data) => api.post(`/qualifications/employees/${employeeId}/certify`, data),
    promoteEmployee: (employeeId, data) => api.post(`/qualifications/employees/${employeeId}/promote`, data),
    
    // 评估记录
    getAssessments: (employeeId, params) => api.get(`/qualifications/assessments/${employeeId}`, { params }),
    createAssessment: (data) => api.post('/qualifications/assessments', data),
    submitAssessment: (assessmentId, data) => api.post(`/qualifications/assessments/${assessmentId}/submit`, data),
};

// R&D Project APIs (研发项目管理)
export const rdProjectApi = {
    // 研发项目分类
    getCategories: (params) => api.get('/rd-project-categories', { params }),
    
    // 研发项目管理
    list: (params) => api.get('/rd-projects', { params }),
    get: (id) => api.get(`/rd-projects/${id}`),
    create: (data) => api.post('/rd-projects', data),
    update: (id, data) => api.put(`/rd-projects/${id}`, data),
    approve: (id, data) => api.put(`/rd-projects/${id}/approve`, data),
    close: (id, data) => api.put(`/rd-projects/${id}/close`, data),
    linkProject: (id, data) => api.put(`/rd-projects/${id}/link-project`, data),
    
    // 研发费用类型
    getCostTypes: (params) => api.get('/rd-cost-types', { params }),
    
    // 研发费用管理
    getCosts: (params) => api.get('/rd-costs', { params }),
    createCost: (data) => api.post('/rd-costs', data),
    updateCost: (id, data) => api.put(`/rd-costs/${id}`, data),
    calculateLaborCost: (data) => api.post('/rd-costs/calc-labor', data),
    
    // 费用汇总
    getCostSummary: (projectId) => api.get(`/rd-projects/${projectId}/cost-summary`),
    getTimesheetSummary: (projectId, params) => api.get(`/rd-projects/${projectId}/timesheet-summary`, { params }),
    
    // 费用分摊规则
    getAllocationRules: (params) => api.get('/rd-cost-allocation-rules', { params }),
    applyAllocation: (ruleId, data) => api.post('/rd-costs/apply-allocation', data, { params: { rule_id: ruleId, ...data } }),
    
    // 研发项目工作日志
    getWorklogs: (projectId, params) => api.get(`/rd-projects/${projectId}/worklogs`, { params }),
    createWorklog: (projectId, data) => api.post(`/rd-projects/${projectId}/worklogs`, data),
    
    // 研发项目文档管理
    getDocuments: (projectId, params) => api.get(`/rd-projects/${projectId}/documents`, { params }),
    createDocument: (projectId, data) => api.post(`/rd-projects/${projectId}/documents`, data),
    uploadDocument: (projectId, formData) => api.post(`/rd-projects/${projectId}/documents/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
    }),
    downloadDocument: (projectId, docId) => api.get(`/rd-projects/${projectId}/documents/${docId}/download`, {
        responseType: 'blob'
    }),
};

// R&D Cost Reports APIs (研发费用报表)
export const rdReportApi = {
    // 研发费用辅助账
    getAuxiliaryLedger: (params) => api.get('/reports/rd-auxiliary-ledger', { params }),
    
    // 研发费用加计扣除明细
    getDeductionDetail: (params) => api.get('/reports/rd-deduction-detail', { params }),
    
    // 高新企业研发费用表
    getHighTechReport: (params) => api.get('/reports/rd-high-tech', { params }),
    
    // 研发投入强度报表
    getIntensityReport: (params) => api.get('/reports/rd-intensity', { params }),
    
    // 研发人员统计
    getPersonnelReport: (params) => api.get('/reports/rd-personnel', { params }),
    
    // 导出研发费用报表
    exportReport: (params) => api.get('/reports/rd-export', { params, responseType: 'blob' }),
};

// Assembly Kit Analysis APIs (装配齐套分析)
export const assemblyKitApi = {
    // 看板数据
    dashboard: (params) => api.get('/assembly/dashboard', { params }),

    // 装配阶段
    getStages: (params) => api.get('/assembly/stages', { params }),
    updateStage: (stageCode, data) => api.put(`/assembly/stages/${stageCode}`, data),

    // 物料分类映射
    getCategoryMappings: (params) => api.get('/assembly/category-mappings', { params }),
    createCategoryMapping: (data) => api.post('/assembly/category-mappings', data),
    updateCategoryMapping: (id, data) => api.put(`/assembly/category-mappings/${id}`, data),
    deleteCategoryMapping: (id) => api.delete(`/assembly/category-mappings/${id}`),

    // BOM装配属性
    getBomAssemblyAttrs: (bomId, params) => api.get(`/assembly/bom/${bomId}/assembly-attrs`, { params }),
    batchSetAssemblyAttrs: (bomId, data) => api.post(`/assembly/bom/${bomId}/assembly-attrs/batch`, data),
    updateAssemblyAttr: (attrId, data) => api.put(`/assembly/bom/assembly-attrs/${attrId}`, data),
    autoAssignAttrs: (bomId, data) => api.post(`/assembly/bom/${bomId}/assembly-attrs/auto`, data),
    applyTemplate: (bomId, data) => api.post(`/assembly/bom/${bomId}/assembly-attrs/template`, data),

    // 齐套分析
    executeAnalysis: (data) => api.post('/assembly/analysis', data),
    getAnalysisDetail: (readinessId) => api.get(`/assembly/analysis/${readinessId}`),
    getProjectReadiness: (projectId, params) => api.get(`/assembly/projects/${projectId}/assembly-readiness`, { params }),
    
    // 智能推荐
    getRecommendations: (bomId) => api.get(`/assembly/bom/${bomId}/assembly-attrs/recommendations`),
    smartRecommend: (bomId, data) => api.post(`/assembly/bom/${bomId}/assembly-attrs/smart-recommend`, data),
    
    // 排产建议
    generateSuggestions: (params) => api.post('/assembly/suggestions/generate', null, { params }),
    
    // 优化建议
    getOptimizationSuggestions: (readinessId) => api.get(`/assembly/analysis/${readinessId}/optimize`),

    // 缺料预警
    getShortageAlerts: (params) => api.get('/assembly/shortage-alerts', { params }),

    // 预警规则
    getAlertRules: (params) => api.get('/assembly/alert-rules', { params }),
    createAlertRule: (data) => api.post('/assembly/alert-rules', data),
    updateAlertRule: (id, data) => api.put(`/assembly/alert-rules/${id}`, data),

    // 排产建议
    getSuggestions: (params) => api.get('/assembly/suggestions', { params }),
    acceptSuggestion: (id, data) => api.post(`/assembly/suggestions/${id}/accept`, data),
    rejectSuggestion: (id, data) => api.post(`/assembly/suggestions/${id}/reject`, data),

    // 装配模板
    getTemplates: (params) => api.get('/assembly/templates', { params }),
    createTemplate: (data) => api.post('/assembly/templates', data),
    updateTemplate: (id, data) => api.put(`/assembly/templates/${id}`, data),
    deleteTemplate: (id) => api.delete(`/assembly/templates/${id}`),
};

// Scheduler APIs
export const schedulerApi = {
    status: () => api.get('/scheduler/status'),
    jobs: () => api.get('/scheduler/jobs'),
    metrics: () => api.get('/scheduler/metrics'),
    metricsPrometheus: () => api.get('/scheduler/metrics/prometheus', { responseType: 'text' }),
    triggerJob: (jobId) => api.post(`/scheduler/jobs/${jobId}/trigger`),
    listServices: () => api.get('/scheduler/services/list'),
};

// Staff Matching APIs - AI驱动人员智能匹配
export const staffMatchingApi = {
    // 标签管理
    getTags: (params) => api.get('/staff-matching/tags', { params }),
    getTagTree: (tagType) => api.get('/staff-matching/tags/tree', { params: { tag_type: tagType } }),
    createTag: (data) => api.post('/staff-matching/tags', data),
    updateTag: (id, data) => api.put(`/staff-matching/tags/${id}`, data),
    deleteTag: (id) => api.delete(`/staff-matching/tags/${id}`),

    // 员工标签评估
    getEvaluations: (params) => api.get('/staff-matching/evaluations', { params }),
    createEvaluation: (data) => api.post('/staff-matching/evaluations', data),
    batchCreateEvaluations: (data) => api.post('/staff-matching/evaluations/batch', data),
    updateEvaluation: (id, data) => api.put(`/staff-matching/evaluations/${id}`, data),
    deleteEvaluation: (id) => api.delete(`/staff-matching/evaluations/${id}`),

    // 员工档案
    getProfiles: (params) => api.get('/staff-matching/profiles', { params }),
    getProfile: (employeeId) => api.get(`/staff-matching/profiles/${employeeId}`),
    refreshProfile: (employeeId) => api.post(`/staff-matching/profiles/${employeeId}/refresh`),

    // 项目绩效
    getPerformance: (params) => api.get('/staff-matching/performance', { params }),
    createPerformance: (data) => api.post('/staff-matching/performance', data),
    getEmployeePerformanceHistory: (employeeId) => api.get(`/staff-matching/performance/employee/${employeeId}`),

    // 人员需求
    getStaffingNeeds: (params) => api.get('/staff-matching/staffing-needs', { params }),
    getStaffingNeed: (id) => api.get(`/staff-matching/staffing-needs/${id}`),
    createStaffingNeed: (data) => api.post('/staff-matching/staffing-needs', data),
    updateStaffingNeed: (id, data) => api.put(`/staff-matching/staffing-needs/${id}`, data),
    cancelStaffingNeed: (id) => api.delete(`/staff-matching/staffing-needs/${id}`),

    // AI匹配
    executeMatching: (staffingNeedId, params) => api.post(`/staff-matching/matching/execute/${staffingNeedId}`, null, { params }),
    getMatchingResults: (staffingNeedId, requestId) => api.get(`/staff-matching/matching/results/${staffingNeedId}`, { params: { request_id: requestId } }),
    acceptCandidate: (data) => api.post('/staff-matching/matching/accept', data),
    rejectCandidate: (data) => api.post('/staff-matching/matching/reject', data),
    getMatchingHistory: (params) => api.get('/staff-matching/matching/history', { params }),

    // 仪表板
    getDashboard: () => api.get('/staff-matching/dashboard'),
};

// Project Role APIs - 项目角色类型与配置
export const projectRoleApi = {
    // 角色类型管理
    types: {
        list: (params) => api.get('/project-roles/types', { params }),
        get: (id) => api.get(`/project-roles/types/${id}`),
        create: (data) => api.post('/project-roles/types', data),
        update: (id, data) => api.put(`/project-roles/types/${id}`, data),
        delete: (id) => api.delete(`/project-roles/types/${id}`),
    },

    // 项目角色配置
    configs: {
        get: (projectId) => api.get(`/project-roles/projects/${projectId}/configs`),
        batchUpdate: (projectId, data) => api.put(`/project-roles/projects/${projectId}/configs`, data),
        init: (projectId) => api.post(`/project-roles/projects/${projectId}/configs/init`),
    },

    // 项目负责人管理
    leads: {
        list: (projectId) => api.get(`/project-roles/projects/${projectId}/leads`),
        get: (projectId, memberId) => api.get(`/project-roles/projects/${projectId}/leads/${memberId}`),
        create: (projectId, data) => api.post(`/project-roles/projects/${projectId}/leads`, data),
        update: (projectId, memberId, data) => api.put(`/project-roles/projects/${projectId}/leads/${memberId}`, data),
        delete: (projectId, memberId) => api.delete(`/project-roles/projects/${projectId}/leads/${memberId}`),
    },

    // 团队成员管理
    team: {
        list: (projectId, leadMemberId) => api.get(`/project-roles/projects/${projectId}/leads/${leadMemberId}/team`),
        add: (projectId, leadMemberId, data) => api.post(`/project-roles/projects/${projectId}/leads/${leadMemberId}/team`, data),
        remove: (projectId, leadMemberId, memberId) => api.delete(`/project-roles/projects/${projectId}/leads/${leadMemberId}/team/${memberId}`),
    },

    // 项目角色概览
    getOverview: (projectId) => api.get(`/project-roles/projects/${projectId}/overview`),
};

// Administrative APIs (行政管理)
export const adminApi = {
    // 行政审批
    approvals: {
        list: (params) => api.get('/admin/approvals', { params }),
        get: (id) => api.get(`/admin/approvals/${id}`),
        approve: (id, data) => api.put(`/admin/approvals/${id}/approve`, data),
        reject: (id, data) => api.put(`/admin/approvals/${id}/reject`, data),
        getStatistics: (params) => api.get('/admin/approvals/statistics', { params }),
    },

    // 费用报销
    expenses: {
        list: (params) => api.get('/admin/expenses', { params }),
        get: (id) => api.get(`/admin/expenses/${id}`),
        create: (data) => api.post('/admin/expenses', data),
        update: (id, data) => api.put(`/admin/expenses/${id}`, data),
        submit: (id) => api.put(`/admin/expenses/${id}/submit`),
        approve: (id, data) => api.put(`/admin/expenses/${id}/approve`, data),
        reject: (id, data) => api.put(`/admin/expenses/${id}/reject`, data),
        getStatistics: (params) => api.get('/admin/expenses/statistics', { params }),
    },

    // 请假管理
    leave: {
        list: (params) => api.get('/admin/leave', { params }),
        get: (id) => api.get(`/admin/leave/${id}`),
        create: (data) => api.post('/admin/leave', data),
        update: (id, data) => api.put(`/admin/leave/${id}`, data),
        approve: (id, data) => api.put(`/admin/leave/${id}/approve`, data),
        reject: (id, data) => api.put(`/admin/leave/${id}/reject`, data),
        cancel: (id) => api.put(`/admin/leave/${id}/cancel`),
        getStatistics: (params) => api.get('/admin/leave/statistics', { params }),
        getBalance: (userId) => api.get(`/admin/leave/balance/${userId}`),
    },

    // 考勤管理
    attendance: {
        list: (params) => api.get('/admin/attendance', { params }),
        get: (id) => api.get(`/admin/attendance/${id}`),
        clockIn: (data) => api.post('/admin/attendance/clock-in', data),
        clockOut: (data) => api.post('/admin/attendance/clock-out', data),
        getMyRecords: (params) => api.get('/admin/attendance/my-records', { params }),
        getStatistics: (params) => api.get('/admin/attendance/statistics', { params }),
        exportReport: (params) => api.get('/admin/attendance/export', { params, responseType: 'blob' }),
    },

    // 办公用品
    supplies: {
        list: (params) => api.get('/admin/supplies', { params }),
        get: (id) => api.get(`/admin/supplies/${id}`),
        request: (data) => api.post('/admin/supplies/request', data),
        approve: (id, data) => api.put(`/admin/supplies/${id}/approve`, data),
        reject: (id, data) => api.put(`/admin/supplies/${id}/reject`, data),
        getInventory: () => api.get('/admin/supplies/inventory'),
    },

    // 车辆管理
    vehicles: {
        list: (params) => api.get('/admin/vehicles', { params }),
        get: (id) => api.get(`/admin/vehicles/${id}`),
        request: (data) => api.post('/admin/vehicles/request', data),
        approve: (id, data) => api.put(`/admin/vehicles/${id}/approve`, data),
        reject: (id, data) => api.put(`/admin/vehicles/${id}/reject`, data),
        getAvailable: (date) => api.get('/admin/vehicles/available', { params: { date } }),
    },

    // 会议室管理
    meetingRooms: {
        list: (params) => api.get('/admin/meeting-rooms', { params }),
        get: (id) => api.get(`/admin/meeting-rooms/${id}`),
        book: (data) => api.post('/admin/meeting-rooms/book', data),
        cancel: (id) => api.put(`/admin/meeting-rooms/${id}/cancel`),
        getAvailable: (date, time) => api.get('/admin/meeting-rooms/available', { params: { date, time } }),
    },

    // 仪表板
    getDashboard: (params) => api.get('/admin/dashboard', { params }),
};

// Management Rhythm APIs - 管理节律
export const managementRhythmApi = {
    // 节律配置
    configs: {
        list: (params) => api.get('/management-rhythm/configs', { params }),
        get: (id) => api.get(`/management-rhythm/configs/${id}`),
        create: (data) => api.post('/management-rhythm/configs', data),
        update: (id, data) => api.put(`/management-rhythm/configs/${id}`, data),
    },

    // 战略会议
    meetings: {
        list: (params) => api.get('/strategic-meetings', { params }),
        get: (id) => api.get(`/strategic-meetings/${id}`),
        create: (data) => api.post('/strategic-meetings', data),
        update: (id, data) => api.put(`/strategic-meetings/${id}`, data),
        updateMinutes: (id, data) => api.put(`/strategic-meetings/${id}/minutes`, data),
    },

    // 会议行动项
    actionItems: {
        list: (meetingId, params) => api.get(`/strategic-meetings/${meetingId}/action-items`, { params }),
        create: (meetingId, data) => api.post(`/strategic-meetings/${meetingId}/action-items`, data),
        update: (meetingId, itemId, data) => api.put(`/strategic-meetings/${meetingId}/action-items/${itemId}`, data),
    },

    // 节律仪表盘
    dashboard: {
        get: () => api.get('/management-rhythm/dashboard'),
    },

    // 会议地图
    meetingMap: {
        get: (params) => api.get('/meeting-map', { params }),
        calendar: (params) => api.get('/meeting-map/calendar', { params }),
        statistics: (params) => api.get('/meeting-map/statistics', { params }),
    },

    // 战略结构模板
    getStrategicStructureTemplate: () => api.get('/management-rhythm/strategic-structure-template'),

    // 会议报告
    reports: {
        list: (params) => api.get('/meeting-reports', { params }),
        get: (id) => api.get(`/meeting-reports/${id}`),
        generate: (data) => api.post('/meeting-reports/generate', data),
        exportDocx: (id) => api.get(`/meeting-reports/${id}/export-docx`, { responseType: 'blob' }),
    },
};

// Culture Wall APIs - 文化墙
export const cultureWallApi = {
    // 文化墙汇总
    summary: {
        get: () => api.get('/culture-wall/summary'),
    },

    // 文化墙内容
    contents: {
        list: (params) => api.get('/culture-wall/contents', { params }),
        get: (id) => api.get(`/culture-wall/contents/${id}`),
        create: (data) => api.post('/culture-wall/contents', data),
        update: (id, data) => api.put(`/culture-wall/contents/${id}`, data),
    },

    // 个人目标
    goals: {
        list: (params) => api.get('/personal-goals', { params }),
        create: (data) => api.post('/personal-goals', data),
        update: (id, data) => api.put(`/personal-goals/${id}`, data),
    },
};

// Financial Reports APIs - 财务报表
export const financialReportApi = {
    // 综合财务数据
    getSummary: (params) => api.get('/finance/summary', { params }),
    // 损益表
    getProfitLoss: (params) => api.get('/finance/profit-loss', { params }),
    // 现金流量表
    getCashFlow: (params) => api.get('/finance/cash-flow', { params }),
    // 预算执行
    getBudgetExecution: (params) => api.get('/finance/budget-execution', { params }),
    // 成本分析
    getCostAnalysis: (params) => api.get('/finance/cost-analysis', { params }),
    // 项目盈利分析
    getProjectProfitability: (params) => api.get('/finance/project-profitability', { params }),
    // 月度趋势
    getMonthlyTrend: (params) => api.get('/finance/monthly-trend', { params }),
    // 导出报表
    exportReport: (params) => api.get('/finance/export', { params, responseType: 'blob' }),
};

// Work Log APIs - 工作日志
export const workLogApi = {
    list: (params) => api.get('/work-logs', { params }),
    get: (id) => api.get(`/work-logs/${id}`),
    create: (data) => api.post('/work-logs', data),
    update: (id, data) => api.put(`/work-logs/${id}`, data),
    delete: (id) => api.delete(`/work-logs/${id}`),
    getMentionOptions: () => api.get('/work-logs/mentions/options'),
    // 配置相关（管理员）
    getConfig: () => api.get('/work-logs/config'),
    listConfigs: () => api.get('/work-logs/config/list'),
    createConfig: (data) => api.post('/work-logs/config', data),
    updateConfig: (id, data) => api.put(`/work-logs/config/${id}`, data),
};

// Report Center APIs - 报表中心
export const reportCenterApi = {
    // 报表配置
    getRoles: () => api.get('/reports/roles'),
    getTypes: () => api.get('/reports/types'),
    getRoleReportMatrix: () => api.get('/reports/role-report-matrix'),
    // 报表生成
    generate: (data) => api.post('/reports/generate', data),
    preview: (reportType, params) => api.get(`/reports/preview/${reportType}`, { params }),
    compareRoles: (data) => api.post('/reports/compare-roles', data),
    // 报表导出
    exportReport: (data) => api.post('/reports/export', data),
    exportDirect: (params) => api.post('/reports/export-direct', null, { params }),
    download: (reportId) => api.get(`/reports/download/${reportId}`, { responseType: 'blob' }),
    // 报表模板
    getTemplates: (params) => api.get('/reports/templates', { params }),
    applyTemplate: (data) => api.post('/reports/templates/apply', data),
    // BI 报表
    getDeliveryRate: (params) => api.get('/reports/delivery-rate', { params }),
    getHealthDistribution: () => api.get('/reports/health-distribution'),
    getUtilization: (params) => api.get('/reports/utilization', { params }),
    getSupplierPerformance: (params) => api.get('/reports/supplier-performance', { params }),
    getExecutiveDashboard: () => api.get('/reports/dashboard/executive'),
    // 研发费用报表
    getRdAuxiliaryLedger: (params) => api.get('/reports/rd-auxiliary-ledger', { params }),
    getRdDeductionDetail: (params) => api.get('/reports/rd-deduction-detail', { params }),
    getRdHighTech: (params) => api.get('/reports/rd-high-tech', { params }),
    getRdIntensity: (params) => api.get('/reports/rd-intensity', { params }),
    getRdPersonnel: (params) => api.get('/reports/rd-personnel', { params }),
    exportRdReport: (params) => api.get('/reports/rd-export', { params, responseType: 'blob' }),
};
