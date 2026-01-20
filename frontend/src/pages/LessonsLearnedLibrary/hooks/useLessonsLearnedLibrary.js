import { useState, useEffect, useCallback } from 'react';
import { projectReviewApi } from '../../../services/api';

export function useLessonsLearnedLibrary() {
    const [loading, setLoading] = useState(true);
    const [lessons, setLessons] = useState([]);
    const [total, setTotal] = useState(0);
    const [page, setPage] = useState(1);
    const [pageSize] = useState(20);

    // Filters
    const [keyword, setKeyword] = useState("");
    const [lessonType, setLessonType] = useState(null);
    const [category, setCategory] = useState(null);
    const [status, setStatus] = useState(null);
    const [priority, setPriority] = useState(null);
    const [projectId, setProjectId] = useState(null);

    // Stats
    const [statistics, setStatistics] = useState(null);
    const [categories, setCategories] = useState([]);
    const [activeTab, setActiveTab] = useState("list");

    const fetchLessons = useCallback(async () => {
        try {
            setLoading(true);
            const params = { page, page_size: pageSize };
            if (keyword) params.keyword = keyword;
            if (lessonType) params.lesson_type = lessonType;
            if (category) params.category = category;
            if (status) params.status = status;
            if (priority) params.priority = priority;
            if (projectId) params.project_id = projectId;

            const res = await projectReviewApi.searchLessonsLearned(params);
            const data = res.data || res;
            setLessons(data.items || data || []);
            setTotal(data.total || data.length || 0);
        } catch (err) {
            console.error("Failed to fetch lessons:", err);
            setLessons([]);
            setTotal(0);
        } finally {
            setLoading(false);
        }
    }, [page, pageSize, keyword, lessonType, category, status, priority, projectId]);

    const fetchStatistics = useCallback(async () => {
        try {
            const params = projectId ? { project_id: projectId } : {};
            const res = await projectReviewApi.getLessonsStatistics(params);
            const data = res.data || res;
            setStatistics(data);
        } catch (err) {
            console.error("Failed to fetch statistics:", err);
        }
    }, [projectId]);

    const fetchCategories = useCallback(async () => {
        try {
            const res = await projectReviewApi.getLessonCategories();
            const data = res.data || res;
            setCategories(data.categories || []);
        } catch (err) {
            console.error("Failed to fetch categories:", err);
        }
    }, []);

    useEffect(() => {
        fetchLessons();
        fetchStatistics();
        fetchCategories();
    }, [fetchLessons, fetchStatistics, fetchCategories]);

    return {
        loading,
        lessons,
        total,
        page, setPage,
        pageSize,
        keyword, setKeyword,
        lessonType, setLessonType,
        category, setCategory,
        status, setStatus,
        priority, setPriority,
        projectId, setProjectId,
        statistics,
        categories,
        activeTab, setActiveTab
    };
}
