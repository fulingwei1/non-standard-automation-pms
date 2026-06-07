import { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { technicalReviewApi, projectApi, userApi } from "../../../services/api";
import { formatDate } from "../../../lib/utils";
import { DEFAULT_FORM_DATA } from "../constants";
import { getProjectContextFilters } from "../../../lib/projectContext";
import { buildTechnicalReviewListPath } from "../navigation";

/**
 * Manages all create/edit form state for TechnicalReviewDetail.
 * Handles data fetching, form fields, and save operations.
 */
export function useTechnicalReviewForm(reviewId) {
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const projectContextFilters = getProjectContextFilters(searchParams);
    const contextProjectId = projectContextFilters.project_id || "";
    const isNew = !reviewId || reviewId === "new";

    const [loading, setLoading] = useState(!isNew);
    const [saving, setSaving] = useState(false);
    const [review, setReview] = useState(null);
    const [activeTab, setActiveTab] = useState("basic");

    const [formData, setFormData] = useState(() => ({
        ...DEFAULT_FORM_DATA,
        project_id: contextProjectId || DEFAULT_FORM_DATA.project_id,
    }));

    const [projects, setProjects] = useState([]);
    const [users, setUsers] = useState([]);
    const [participants, setParticipants] = useState([]);
    const [materials, setMaterials] = useState([]);
    const [checklistRecords, setChecklistRecords] = useState([]);
    const [issues, setIssues] = useState([]);

    // Dialog open-state flags (kept here so sub-components can trigger them)
    const [participantDialog, setParticipantDialog] = useState({ open: false });
    const [materialDialog, setMaterialDialog] = useState({ open: false });
    const [checklistDialog, setChecklistDialog] = useState({ open: false });
    const [issueDialog, setIssueDialog] = useState({ open: false });

    useEffect(() => {
        if (isNew) {
            setLoading(false);
            if (contextProjectId) {
                setFormData((prev) => ({ ...prev, project_id: contextProjectId }));
            }
        } else {
            fetchReview();
        }
        fetchProjects();
        fetchUsers();
    }, [reviewId, contextProjectId]); // eslint-disable-line react-hooks/exhaustive-deps

    const fetchProjects = async () => {
        try {
            const response = await projectApi.list({ page: 1, page_size: 100 });
            const data = response.data || response;
            setProjects(data.items || []);
        } catch (error) {
            console.error("Failed to fetch projects:", error);
        }
    };

    const fetchUsers = async () => {
        try {
            const response = await userApi.list({ page: 1, page_size: 100 });
            const data = response.data || response;
            setUsers(data.items || []);
        } catch (error) {
            console.error("Failed to fetch users:", error);
        }
    };

    const fetchReview = async () => {
        try {
            setLoading(true);
            const response = await technicalReviewApi.get(reviewId);
            const data = response.data || response;
            setReview(data);
            setFormData({
                review_type: data.review_type,
                review_name: data.review_name,
                project_id: data.project_id,
                equipment_id: data.equipment_id || "",
                scheduled_date: formatDate(data.scheduled_date, "YYYY-MM-DDTHH:mm"),
                location: data.location || "",
                meeting_type: data.meeting_type,
                host_id: data.host_id,
                presenter_id: data.presenter_id,
                recorder_id: data.recorder_id,
            });
            setParticipants(data.participants || []);
            setMaterials(data.materials || []);
            setChecklistRecords(data.checklist_records || []);
            setIssues(data.issues || []);
        } catch (error) {
            console.error("Failed to fetch review:", error);
            alert("加载失败：" + (error.response?.data?.detail || error.message));
        } finally {
            setLoading(false);
        }
    };

    const handleSave = async () => {
        try {
            setSaving(true);
            if (isNew) {
                await technicalReviewApi.create(formData);
                navigate(buildTechnicalReviewListPath(searchParams));
            } else {
                await technicalReviewApi.update(reviewId, formData);
                await fetchReview();
            }
        } catch (error) {
            console.error("Failed to save:", error);
            alert("保存失败：" + (error.response?.data?.detail || error.message));
        } finally {
            setSaving(false);
        }
    };

    const updateField = (field, value) =>
        setFormData((prev) => ({ ...prev, [field]: value }));

    return {
        isNew,
        loading,
        saving,
        review,
        activeTab,
        setActiveTab,
        formData,
        updateField,
        projects,
        users,
        participants,
        materials,
        checklistRecords,
        issues,
        participantDialog,
        setParticipantDialog,
        materialDialog,
        setMaterialDialog,
        checklistDialog,
        setChecklistDialog,
        issueDialog,
        setIssueDialog,
        handleSave,
        fetchReview,
    };
}
