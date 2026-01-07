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
            // 如果是演示账号的 token，不删除 token，也不重定向
            // 演示账号的 API 调用失败是预期的，因为后端不支持演示账号
            if (token && token.startsWith('demo_token_')) {
                // 对于演示账号，静默处理 401 错误，让页面组件使用 mock 数据
                console.log('演示账号 API 调用失败，将使用 mock 数据');
            } else {
                // 真实账号的 401 错误，删除 token 并可能需要重定向
                localStorage.removeItem('token');
                // Redirect to login or handle session expiry
            }
        }
        return Promise.reject(error);
    }
);

export default api;

export const projectApi = {
    list: (params) => api.get('/projects/', { params }),
    get: (id) => api.get(`/projects/${id}`),
    create: (data) => api.post('/projects/', data),
    update: (id, data) => api.put(`/projects/${id}`, data),
    getMachines: (id) => api.get(`/projects/${id}/machines`),
};

export const machineApi = {
    list: (params) => api.get('/machines/', { params }),
    get: (id) => api.get(`/machines/${id}`),
    create: (data) => api.post('/machines/', data),
    update: (id, data) => api.put(`/machines/${id}`, data),
    delete: (id) => api.delete(`/machines/${id}`),
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
    login: (formData) => api.post('/auth/login', formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    }),
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
    assignRoles: (id, roleIds) => api.put(`/users/${id}/roles`, roleIds),
};

export const roleApi = {
    list: (params) => api.get('/roles/', { params }),
    get: (id) => api.get(`/roles/${id}`),
    create: (data) => api.post('/roles/', data),
    update: (id, data) => api.put(`/roles/${id}`, data),
    assignPermissions: (id, permissionIds) => api.put(`/roles/${id}/permissions`, permissionIds),
    permissions: () => api.get('/roles/permissions'),
};

export const customerApi = {
    list: (params) => api.get('/customers/', { params }),
    get: (id) => api.get(`/customers/${id}`),
    create: (data) => api.post('/customers/', data),
    update: (id, data) => api.put(`/customers/${id}`, data),
    delete: (id) => api.delete(`/customers/${id}`),
    getProjects: (id, params) => api.get(`/customers/${id}/projects`, { params }),
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
};

export const contractApi = {
    list: (params) => api.get('/sales/contracts', { params }),
    get: (id) => api.get(`/sales/contracts/${id}`),
    create: (data) => api.post('/sales/contracts', data),
    update: (id, data) => api.put(`/sales/contracts/${id}`, data),
    sign: (id, data) => api.post(`/sales/contracts/${id}/sign`, data),
    createProject: (id, data) => api.post(`/sales/contracts/${id}/project`, data),
    getDeliverables: (id) => api.get(`/sales/contracts/${id}/deliverables`),
};

export const invoiceApi = {
    list: (params) => api.get('/sales/invoices', { params }),
    get: (id) => api.get(`/sales/invoices/${id}`),
    create: (data) => api.post('/sales/invoices', data),
    update: (id, data) => api.put(`/sales/invoices/${id}`, data),
    issue: (id, data) => api.post(`/sales/invoices/${id}/issue`, data),
    receivePayment: (id, data) => api.post(`/sales/invoices/${id}/receive-payment`, null, { params: data }),
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
        toggle: (id, enabled) => api.put(`/alert-rules/${id}/toggle`, null, { params: { enabled } }),
    },
    
    // Alert Rule Templates
    templates: (params) => api.get('/alert-rule-templates', { params }),
    
    // Alert Statistics
    statistics: (params) => api.get('/alerts/statistics', { params }),
    dashboard: () => api.get('/alerts/statistics/dashboard'),
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
        close: (id, data) => api.put(`/service-tickets/${id}/close`, data),
        getStatistics: () => api.get('/service-tickets/statistics'),
    },
    records: {
        list: (params) => api.get('/service-records', { params }),
        get: (id) => api.get(`/service-records/${id}`),
        create: (data) => api.post('/service-records', data),
        update: (id, data) => api.put(`/service-records/${id}`, data),
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
    },
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
    getCauseAnalysis: (params) => api.get('/issues/statistics/cause-analysis', { params }),
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
};

// Material Management APIs
export const materialApi = {
    list: (params) => api.get('/materials/', { params }),
    get: (id) => api.get(`/materials/${id}`),
    create: (data) => api.post('/materials/', data),
    update: (id, data) => api.put(`/materials/${id}`, data),
    categories: {
        list: (params) => api.get('/materials/categories/', { params }),
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
    submit: (id) => api.put(`/ecns/${id}/submit`),
    evaluate: (id, data) => api.post(`/ecns/${id}/evaluate`, data),
    approve: (id, data) => api.post(`/ecns/${id}/approve`, data),
    reject: (id, data) => api.put(`/ecns/${id}/reject`, data),
    execute: (id, data) => api.put(`/ecns/${id}/execute`, data),
    getTasks: (id) => api.get(`/ecns/${id}/tasks`),
    createTask: (id, data) => api.post(`/ecns/${id}/tasks`, data),
    getAffectedMaterials: (id) => api.get(`/ecns/${id}/affected-materials`),
    getAffectedOrders: (id) => api.get(`/ecns/${id}/affected-orders`),
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
        workload: (params) => api.get('/presale/statistics/workload', { params }),
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
    generatePR: (bomId, data) => api.post(`/bom/${bomId}/generate-pr`, data),
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
};
