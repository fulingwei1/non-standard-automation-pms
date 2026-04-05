import { useState, useEffect, useMemo, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { bomApi, projectApi, machineApi } from '../../../services/api';

/**
 * BOM管理数据 Hook
 * Encapsulates all state, data-fetching, and action handlers for BOMManagement.
 */
export function useBOMManagement() {
    const [searchParams] = useSearchParams();
    const machineId = searchParams.get('machine_id');
    const projectId = searchParams.get('project_id');

    // List state
    const [loading, setLoading] = useState(true);
    const [boms, setBoms] = useState([]);
    const [projects, setProjects] = useState([]);
    const [machines, setMachines] = useState([]);

    // Detail state
    const [selectedBom, setSelectedBom] = useState(null);
    const [bomItems, setBomItems] = useState([]);
    const [versions, setVersions] = useState([]);

    // Filters
    const [searchKeyword, setSearchKeyword] = useState('');
    const [filterProject, setFilterProject] = useState(projectId || '');
    const [filterMachine, setFilterMachine] = useState(machineId || '');
    const [filterStatus, setFilterStatus] = useState('');

    // Dialog visibility
    const [showBomDetail, setShowBomDetail] = useState(false);
    const [showCreateDialog, setShowCreateDialog] = useState(false);
    const [showImportDialog, setShowImportDialog] = useState(false);
    const [showReleaseDialog, setShowReleaseDialog] = useState(false);

    // Form state
    const [newBom, setNewBom] = useState({
        bom_name: '',
        machine_id: machineId ? parseInt(machineId) : null,
        version: '1.0',
        remark: '',
    });
    const [importFile, setImportFile] = useState(null);
    const [releaseNote, setReleaseNote] = useState('');

    // ── Data fetchers ──────────────────────────────────────────────────────────

    const fetchProjects = useCallback(async () => {
        try {
            const res = await projectApi.list({ page_size: 1000 });
            setProjects(res.data?.items || res.data || []);
        } catch (error) {
            console.error('Failed to fetch projects:', error);
        }
    }, []);

    const fetchMachines = useCallback(async (projId) => {
        try {
            const res = await machineApi.list(projId);
            setMachines(res.data?.items || res.data || []);
        } catch (error) {
            console.error('Failed to fetch machines:', error);
        }
    }, []);

    const fetchBOMs = useCallback(async () => {
        try {
            setLoading(true);
            const params = {};
            if (filterProject) params.project_id = filterProject;
            if (filterMachine) params.machine_id = filterMachine;
            if (filterStatus) params.status = filterStatus;
            if (searchKeyword) params.search = searchKeyword;
            const res = await bomApi.list(params);
            setBoms(res.data?.items || res.data || []);
        } catch (error) {
            console.error('Failed to fetch BOMs:', error);
        } finally {
            setLoading(false);
        }
    }, [filterProject, filterMachine, filterStatus, searchKeyword]);

    const fetchBOMDetail = useCallback(async (bomId) => {
        try {
            const [bomRes, itemsRes, versionsRes] = await Promise.all([
                bomApi.get(bomId),
                bomApi.getItems(bomId),
                bomApi.getVersions(bomId),
            ]);
            setSelectedBom(bomRes.data || bomRes);
            setBomItems(itemsRes.data || itemsRes || []);
            setVersions(versionsRes.data || versionsRes || []);
            setShowBomDetail(true);
        } catch (error) {
            console.error('Failed to fetch BOM detail:', error);
        }
    }, []);

    // ── Effects ────────────────────────────────────────────────────────────────

    useEffect(() => {
        fetchProjects();
        if (filterProject) fetchMachines(filterProject);
    }, []); // eslint-disable-line react-hooks/exhaustive-deps

    useEffect(() => {
        fetchBOMs();
    }, [fetchBOMs]);

    // ── Action handlers ────────────────────────────────────────────────────────

    const handleCreateBOM = useCallback(async () => {
        if (!newBom.machine_id || !newBom.bom_name) {
            alert('请填写BOM名称并选择机台');
            return;
        }
        try {
            await bomApi.create(newBom.machine_id, newBom);
            setShowCreateDialog(false);
            setNewBom({ bom_name: '', machine_id: null, version: '1.0', remark: '' });
            fetchBOMs();
        } catch (error) {
            console.error('Failed to create BOM:', error);
            alert('创建BOM失败: ' + (error.response?.data?.detail || error.message));
        }
    }, [newBom, fetchBOMs]);

    const handleReleaseBOM = useCallback(async () => {
        if (!selectedBom) return;
        try {
            await bomApi.release(selectedBom.id, releaseNote);
            setShowReleaseDialog(false);
            setReleaseNote('');
            fetchBOMDetail(selectedBom.id);
            fetchBOMs();
        } catch (error) {
            console.error('Failed to release BOM:', error);
            alert('发布BOM失败: ' + (error.response?.data?.detail || error.message));
        }
    }, [selectedBom, releaseNote, fetchBOMDetail, fetchBOMs]);

    const handleImport = useCallback(async () => {
        if (!importFile || !selectedBom) return;
        try {
            await bomApi.import(selectedBom.id, importFile);
            setShowImportDialog(false);
            setImportFile(null);
            fetchBOMDetail(selectedBom.id);
            alert('导入成功');
        } catch (error) {
            console.error('Failed to import BOM:', error);
            alert('导入失败: ' + (error.response?.data?.detail || error.message));
        }
    }, [importFile, selectedBom, fetchBOMDetail]);

    const handleExport = useCallback(async (bomId) => {
        try {
            const res = await bomApi.export(bomId);
            const url = window.URL.createObjectURL(new Blob([res.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `BOM_${bomId}.xlsx`);
            document.body.appendChild(link);
            link.click();
            link.remove();
        } catch (error) {
            console.error('Failed to export BOM:', error);
            alert('导出失败: ' + (error.response?.data?.detail || error.message));
        }
    }, []);

    const handleFilterProjectChange = useCallback((val) => {
        setFilterProject(val);
        setFilterMachine('');
        if (val) fetchMachines(val);
    }, [fetchMachines]);

    const handleCreateDialogProjectChange = useCallback((val) => {
        fetchMachines(val);
        setNewBom((prev) => ({ ...prev, machine_id: null }));
    }, [fetchMachines]);

    // ── Derived state ──────────────────────────────────────────────────────────

    const filteredBoms = useMemo(() => {
        return (boms || []).filter((bom) => {
            if (searchKeyword) {
                const keyword = searchKeyword.toLowerCase();
                return (
                    bom.bom_no?.toLowerCase().includes(keyword) ||
                    bom.bom_name?.toLowerCase().includes(keyword) ||
                    bom.project_name?.toLowerCase().includes(keyword) ||
                    bom.machine_name?.toLowerCase().includes(keyword)
                );
            }
            return true;
        });
    }, [boms, searchKeyword]);

    return {
        // list
        loading,
        filteredBoms,
        projects,
        machines,
        // detail
        selectedBom,
        setSelectedBom,
        bomItems,
        versions,
        // filters
        searchKeyword,
        setSearchKeyword,
        filterProject,
        filterMachine,
        setFilterMachine,
        filterStatus,
        setFilterStatus,
        handleFilterProjectChange,
        // dialogs
        showBomDetail,
        setShowBomDetail,
        showCreateDialog,
        setShowCreateDialog,
        showImportDialog,
        setShowImportDialog,
        showReleaseDialog,
        setShowReleaseDialog,
        // form
        newBom,
        setNewBom,
        importFile,
        setImportFile,
        releaseNote,
        setReleaseNote,
        // actions
        fetchBOMDetail,
        fetchBOMs,
        handleCreateBOM,
        handleReleaseBOM,
        handleImport,
        handleExport,
        handleCreateDialogProjectChange,
    };
}
