import { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { pmoApi, projectApi } from "../../../services/api";

export function useProjectClosureManagement() {
    const { projectId } = useParams();
    const navigate = useNavigate();

    const [loading, setLoading] = useState(true);
    const [project, setProject] = useState(null);
    const [closure, setClosure] = useState(null);
    const [selectedProjectId, setSelectedProjectId] = useState(
        projectId ? parseInt(projectId) : null
    );

    // Project Selection State
    const [projectSearch, setProjectSearch] = useState("");
    const [projectList, setProjectList] = useState([]);
    const [showProjectSelect, setShowProjectSelect] = useState(!projectId);

    // Dialog States
    const [createDialogOpen, setCreateDialogOpen] = useState(false);
    const [reviewDialog, setReviewDialog] = useState({
        open: false,
        closureId: null
    });
    const [lessonsDialog, setLessonsDialog] = useState({
        open: false,
        closureId: null
    });
    const [detailDialog, setDetailDialog] = useState({
        open: false,
        closure: null
    });

    const fetchProjectData = useCallback(async () => {
        if (!selectedProjectId) return;
        try {
            const res = await projectApi.get(selectedProjectId);
            const data = res.data || res;
            setProject(data);
        } catch (err) {
            console.error("Failed to fetch project:", err);
        }
    }, [selectedProjectId]);

    const fetchClosure = useCallback(async () => {
        if (!selectedProjectId) return;
        try {
            setLoading(true);
            const res = await pmoApi.closures.get(selectedProjectId);
            const data = res.data || res;
            setClosure(data);
        } catch (err) {
            if (err.response?.status === 404) {
                setClosure(null);
            } else {
                console.error("Failed to fetch closure:", err);
            }
        } finally {
            setLoading(false);
        }
    }, [selectedProjectId]);

    const fetchProjectList = useCallback(async () => {
        try {
            const res = await projectApi.list({
                page: 1,
                page_size: 50,
                keyword: projectSearch
            });
            const data = res.data || res;
            setProjectList(data.items || data || []);
        } catch (err) {
            console.error("Failed to fetch projects:", err);
            setProjectList([]);
        }
    }, [projectSearch]);

    useEffect(() => {
        if (selectedProjectId) {
            fetchProjectData();
            fetchClosure();
        }
    }, [selectedProjectId, fetchProjectData, fetchClosure]);

    useEffect(() => {
        if (showProjectSelect) {
            fetchProjectList();
        }
    }, [showProjectSelect, fetchProjectList]);

    const handleSelectProject = (id) => {
        setSelectedProjectId(id);
        setShowProjectSelect(false);
        navigate(`/pmo/closure/${id}`);
    };

    const handleCreate = async (formData) => {
        try {
            await pmoApi.closures.create(selectedProjectId, formData);
            setCreateDialogOpen(false);
            fetchClosure();
        } catch (err) {
            console.error("Failed to create closure:", err);
            alert("创建失败: " + (err.response?.data?.detail || err.message));
        }
    };

    const handleReview = async (closureId, data) => {
        try {
            await pmoApi.closures.review(closureId, data);
            setReviewDialog({ open: false, closureId: null });
            fetchClosure();
        } catch (err) {
            console.error("Failed to review closure:", err);
            alert("评审失败: " + (err.response?.data?.detail || err.message));
        }
    };

    const handleLessons = async (closureId, data) => {
        try {
            await pmoApi.closures.updateLessons(closureId, data);
            setLessonsDialog({ open: false, closureId: null });
            fetchClosure();
        } catch (err) {
            console.error("Failed to update lessons:", err);
            alert("更新失败: " + (err.response?.data?.detail || err.message));
        }
    };

    return {
        // State
        loading,
        project,
        closure,
        selectedProjectId,
        projectSearch, setProjectSearch,
        projectList,
        showProjectSelect, setShowProjectSelect,
        createDialogOpen, setCreateDialogOpen,
        reviewDialog, setReviewDialog,
        lessonsDialog, setLessonsDialog,
        detailDialog, setDetailDialog,
        navigate,

        // Handlers
        handleSelectProject,
        handleCreate,
        handleReview,
        handleLessons,
        refreshClosure: fetchClosure
    };
}
