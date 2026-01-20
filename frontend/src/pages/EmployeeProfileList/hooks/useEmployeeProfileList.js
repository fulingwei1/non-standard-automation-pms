import { useState, useEffect, useCallback, useRef } from "react";
import { staffMatchingApi, organizationApi } from "../../../services/api";

const defaultProfiles = [];

export function useEmployeeProfileList() {
    const [loading, setLoading] = useState(false);
    const [profiles, setProfiles] = useState(defaultProfiles);
    const [searchKeyword, setSearchKeyword] = useState("");
    const [filterDepartment, setFilterDepartment] = useState("all");
    const [activeStatusTab, setActiveStatusTab] = useState("active");

    // 上传相关状态
    const [showUploadModal, setShowUploadModal] = useState(false);
    const [uploading, setUploading] = useState(false);
    const [uploadResult, setUploadResult] = useState(null);
    const fileInputRef = useRef(null);

    const loadProfiles = useCallback(async () => {
        setLoading(true);
        try {
            // 根据选中的标签构建查询参数
            const params = { limit: 200 };

            if (activeStatusTab === "active") {
                params.employment_status = "active";
            } else if (activeStatusTab === "resigned") {
                params.employment_status = "resigned";
            } else if (activeStatusTab === "regular") {
                params.employment_status = "active";
                params.employment_type = "regular";
            } else if (activeStatusTab === "probation") {
                params.employment_status = "active";
                params.employment_type = "probation";
            } else if (activeStatusTab === "intern") {
                params.employment_status = "active";
                params.employment_type = "intern";
            }

            console.log("[员工档案] 发起API请求, 参数:", params);
            const response = await staffMatchingApi.getProfiles(params);

            const data = response.data || response;
            if (Array.isArray(data)) {
                setProfiles(data);
            } else if (data?.items) {
                setProfiles(data.items);
            } else {
                console.warn("[员工档案] 数据格式不正确:", data);
            }
        } catch (error) {
            console.error("[员工档案] 加载失败:", error);
        } finally {
            setLoading(false);
        }
    }, [activeStatusTab]);

    useEffect(() => {
        loadProfiles();
    }, [loadProfiles]);

    // 过滤
    const filteredProfiles = profiles.filter((p) => {
        const matchKeyword =
            !searchKeyword ||
            p.employee_name?.includes(searchKeyword) ||
            p.employee_code?.includes(searchKeyword);
        const matchDept =
            filterDepartment === "all" || p.department === filterDepartment;
        return matchKeyword && matchDept;
    });

    // 获取部门列表
    const departments = [
        ...new Set(profiles.map((p) => p.department).filter(Boolean)),
    ];

    // 统计
    const stats = {
        total: profiles.length,
        available: profiles.filter((p) => (p.current_workload_pct || 0) < 80).length,
        busy: profiles.filter((p) => (p.current_workload_pct || 0) >= 80).length,
    };

    // 处理文件上传
    const handleFileUpload = async (event) => {
        const file = event.target.files?.[0];
        if (!file) { return; }

        // 验证文件类型
        if (!file.name.endsWith(".xlsx") && !file.name.endsWith(".xls")) {
            setUploadResult({
                success: false,
                message: "请上传 Excel 文件（.xlsx 或 .xls 格式）",
            });
            return;
        }

        setUploading(true);
        setUploadResult(null);

        try {
            const formData = new FormData();
            formData.append("file", file);

            const response = await organizationApi.importEmployees(formData);
            setUploadResult(response.data || response);

            // 导入成功后刷新列表
            if (response.data?.success || response.success) {
                setTimeout(() => {
                    loadProfiles();
                }, 1000);
            }
        } catch (error) {
            console.error("上传失败:", error);
            setUploadResult({
                success: false,
                message:
                    error.response?.data?.detail || error.message || "上传失败，请重试",
            });
        } finally {
            setUploading(false);
            // 清空文件输入，允许重复选择同一文件
            if (fileInputRef.current) {
                fileInputRef.current.value = "";
            }
        }
    };

    return {
        loading,
        profiles, filteredProfiles,
        searchKeyword, setSearchKeyword,
        filterDepartment, setFilterDepartment,
        activeStatusTab, setActiveStatusTab,
        departments,
        stats,
        showUploadModal, setShowUploadModal,
        uploading,
        uploadResult, setUploadResult,
        fileInputRef,
        handleFileUpload,
        loadProfiles
    };
}
