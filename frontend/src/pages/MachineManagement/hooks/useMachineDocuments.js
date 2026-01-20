import { useState, useCallback } from 'react';
import { machineApi } from '../../../services/api';

/**
 * 机台文档管理 Hook
 * 负责文档的加载、上传、下载
 */
export function useMachineDocuments() {
    const [documents, setDocuments] = useState(null);
    const [loading, setLoading] = useState(false);

    // 加载文档列表
    const fetchDocuments = useCallback(async (machineId) => {
        if (!machineId) return;
        try {
            setLoading(true);
            const res = await machineApi.getDocuments(machineId, {
                group_by_type: true,
            });
            const data = res.data?.data || res.data || {};
            setDocuments(data);
        } catch (error) {
            console.error('Failed to fetch machine documents:', error);
            setDocuments(null);
        } finally {
            setLoading(false);
        }
    }, []);

    // 上传文档
    const uploadDocument = useCallback(async (machineId, file, formData) => {
        if (!file || !machineId) {
            return { success: false, error: '请选择文件和机台' };
        }

        try {
            const data = new FormData();
            data.append('file', file);
            data.append('doc_type', formData.doc_type);
            data.append('doc_name', formData.doc_name || file.name);
            data.append('doc_no', formData.doc_no || '');
            data.append('version', formData.version || '1.0');
            if (formData.description) {
                data.append('description', formData.description);
            }
            if (formData.machine_stage) {
                data.append('machine_stage', formData.machine_stage);
            }

            await machineApi.uploadDocument(machineId, data);
            await fetchDocuments(machineId);
            return { success: true };
        } catch (error) {
            console.error('Failed to upload document:', error);
            const errorMessage = error.response?.data?.detail || error.message || '上传失败';
            const isPermissionError = error.response?.status === 403;
            return {
                success: false,
                error: errorMessage,
                isPermissionError
            };
        }
    }, [fetchDocuments]);

    // 下载文档
    const downloadDocument = useCallback(async (machineId, doc) => {
        try {
            const response = await machineApi.downloadDocument(machineId, doc.id);
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', doc.file_name);
            document.body.appendChild(link);
            link.click();
            link.remove();
            window.URL.revokeObjectURL(url);
            return { success: true };
        } catch (error) {
            console.error('Failed to download document:', error);
            const errorMessage = error.response?.data?.detail || error.message || '下载失败';
            const isPermissionError = error.response?.status === 403;
            return {
                success: false,
                error: errorMessage,
                isPermissionError
            };
        }
    }, []);

    return {
        documents,
        loading,
        fetchDocuments,
        uploadDocument,
        downloadDocument,
    };
}
