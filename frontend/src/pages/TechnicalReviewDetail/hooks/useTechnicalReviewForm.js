import { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { technicalReviewApi, projectApi, userApi } from "../../../services/api";
import { DEFAULT_FORM_DATA } from "../constants";
import { getProjectContextFilters } from "../../../lib/projectContext";
import { buildTechnicalReviewListPath } from "../navigation";

function toDateTimeLocalValue(value) {
    if (!value) {
        return "";
    }
    if (typeof value === "string") {
        if (/^\d{4}-\d{2}-\d{2}$/.test(value)) {
            return `${value}T00:00`;
        }
        const normalized = value.replace(" ", "T");
        if (/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}/.test(normalized)) {
            return normalized.slice(0, 16);
        }
    }
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
        return "";
    }
    const pad = (part) => String(part).padStart(2, "0");
    return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

function toRequiredNumber(value) {
    if (value === "" || value === null || value === undefined) {
        return value;
    }
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : value;
}

function toOptionalNumber(value) {
    if (value === "" || value === null || value === undefined) {
        return null;
    }
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : value;
}

function buildReviewPayload(formData) {
    return {
        ...formData,
        project_id: toRequiredNumber(formData.project_id),
        equipment_id: toOptionalNumber(formData.equipment_id),
        host_id: toRequiredNumber(formData.host_id),
        presenter_id: toRequiredNumber(formData.presenter_id),
        recorder_id: toRequiredNumber(formData.recorder_id),
    };
}

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
    }, [reviewId, contextProjectId]);

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
            const response = await userApi.options({ page: 1, page_size: 100, is_active: true });
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
                scheduled_date: toDateTimeLocalValue(data.scheduled_date),
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
            const payload = buildReviewPayload(formData);
            if (isNew) {
                await technicalReviewApi.create(payload);
                navigate(buildTechnicalReviewListPath(searchParams));
            } else {
                await technicalReviewApi.update(reviewId, payload);
                await fetchReview();
            }
        } catch (error) {
            console.error("Failed to save:", error);
            alert("保存失败：" + (error.response?.data?.detail || error.message));
        } finally {
            setSaving(false);
        }
    };

    const handleCreateIssue = async (issueData) => {
        try {
            await technicalReviewApi.createIssue(reviewId, issueData);
            setIssueDialog({ open: false });
            await fetchReview();
        } catch (error) {
            console.error("Failed to create review issue:", error);
            alert("创建问题失败：" + (error.response?.data?.detail || error.message));
        }
    };

    const handleAddParticipant = async (participantData) => {
        try {
            await technicalReviewApi.addParticipant(reviewId, participantData);
            setParticipantDialog({ open: false });
            await fetchReview();
        } catch (error) {
            console.error("Failed to add review participant:", error);
            alert("添加参与人失败：" + (error.response?.data?.detail || error.message));
        }
    };

    const handleAddMaterial = async (materialData) => {
        try {
            await technicalReviewApi.addMaterial(reviewId, materialData);
            setMaterialDialog({ open: false });
            await fetchReview();
        } catch (error) {
            console.error("Failed to add review material:", error);
            alert("添加材料失败：" + (error.response?.data?.detail || error.message));
        }
    };

    const handleCreateChecklistRecord = async (recordData) => {
        try {
            await technicalReviewApi.createChecklistRecord(reviewId, recordData);
            setChecklistDialog({ open: false });
            await fetchReview();
        } catch (error) {
            console.error("Failed to create checklist record:", error);
            alert("添加检查项失败：" + (error.response?.data?.detail || error.message));
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
        handleAddParticipant,
        handleAddMaterial,
        handleCreateChecklistRecord,
        handleCreateIssue,
        fetchReview,
    };
}
