import axios from 'axios';

const api = axios.create({
    baseURL: '/api/v1',
    headers: {
        'Content-Type': 'application/json',
    },
});

// Request interceptor for adding auth token
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('token');
        if (token) {
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
            localStorage.removeItem('token');
            // Redirect to login or handle session expiry
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
    create: (data) => api.post('/milestones/', data),
    update: (id, data) => api.put(`/milestones/${id}`, data),
};

export const memberApi = {
    list: (projectId) => api.get('/members/', { params: { project_id: projectId } }),
    add: (data) => api.post('/members/', data),
    remove: (id) => api.delete(`/members/${id}`),
};

export const costApi = {
    list: (projectId) => api.get('/costs/', { params: { project_id: projectId } }),
    create: (data) => api.post('/costs/', data),
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
};

export const customerApi = {
    list: () => api.get('/customers/'),
    get: (id) => api.get(`/customers/${id}`),
    create: (data) => api.post('/customers/', data),
    update: (id, data) => api.put(`/customers/${id}`, data),
};

export const orgApi = {
    departments: () => api.get('/org/departments'),
    employees: () => api.get('/org/employees'),
};
