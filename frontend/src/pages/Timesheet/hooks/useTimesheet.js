import { useState, useEffect, useCallback } from "react";
import { timesheetApi, projectApi } from "../../../services/api";
import { getWeekDates, formatFullDate } from "../utils/dateUtils";

export function useTimesheet() {
    const [weekOffset, setWeekOffset] = useState(0);
    const [entries, setEntries] = useState([]);
    const [showAddDialog, setShowAddDialog] = useState(false);
    const [loading, setLoading] = useState(false);
    const [saving, setSaving] = useState(false);
    const [projects, setProjects] = useState([]);
    const [weekData, setWeekData] = useState(null);

    const weekDates = getWeekDates(weekOffset);
    const isCurrentWeek = weekOffset === 0;
    const weekStart = formatFullDate(weekDates[0]);

    // Load week timesheet data
    const loadWeekTimesheet = useCallback(async () => {
        setLoading(true);
        try {
            const response = await timesheetApi.getWeek({ week_start: weekStart });
            const data = response.data?.data || response.data;
            const timesheets = data.timesheets || [];

            // Group by project and task
            const grouped = {};
            timesheets.forEach((ts) => {
                const key = `${ts.project_id || "none"}_${ts.task_id || "none"}`;

                if (!grouped[key]) {
                    grouped[key] = {
                        id: `entry_${ts.id}`,
                        project_id: ts.project_id,
                        project_code: ts.project_id ? `PJ${String(ts.project_id).padStart(9, "0")}` : "",
                        project_name: ts.project_name || "未分配项目",
                        task_id: ts.task_id,
                        task_name: ts.task_name,
                        hours: {},
                        status: ts.status || "DRAFT",
                        timesheet_ids: [],
                        timesheet_map: {},
                    };
                }

                const dateStr = typeof ts.work_date === "string" ? ts.work_date.split("T")[0] : ts.work_date;
                grouped[key].hours[dateStr] = parseFloat(ts.work_hours || 0);
                grouped[key].timesheet_map[dateStr] = ts.id;

                if (!grouped[key].timesheet_ids.includes(ts.id)) {
                    grouped[key].timesheet_ids.push(ts.id);
                }

                // Status priority: APPROVED > PENDING > DRAFT > REJECTED
                const statusPriority = { APPROVED: 3, PENDING: 2, SUBMITTED: 2, DRAFT: 1, REJECTED: 0 };
                const currentPriority = statusPriority[grouped[key].status] || 0;
                const newPriority = statusPriority[ts.status] || 0;
                if (newPriority > currentPriority) {
                    grouped[key].status = ts.status;
                }
            });

            setEntries(Object.values(grouped));
            setWeekData(data);
        } catch (error) {
            console.error("加载周工时数据失败:", error);
            setEntries([]);
        } finally {
            setLoading(false);
        }
    }, [weekStart]);

    // Load projects
    const loadProjects = useCallback(async () => {
        try {
            const response = await projectApi.list({ page_size: 100, is_active: true });
            const items = response.data?.items || response.data?.data?.items || [];
            setProjects(items);
        } catch (error) {
            console.error("加载项目列表失败:", error);
            setProjects([]);
        }
    }, []);

    useEffect(() => {
        loadProjects();
    }, [loadProjects]);

    useEffect(() => {
        loadWeekTimesheet();
    }, [loadWeekTimesheet]);

    // Calculate totals
    const dailyTotals = weekDates.reduce((acc, date) => {
        const dateStr = formatFullDate(date);
        acc[dateStr] = entries.reduce((sum, entry) => {
            const hours = entry.hours?.[dateStr] || 0;
            return sum + (typeof hours === "number" ? hours : parseFloat(hours) || 0);
        }, 0);
        return acc;
    }, {});

    const weeklyTotal = Object.values(dailyTotals).reduce((a, b) => a + b, 0);

    // Handle add entry
    const handleAddEntry = async (newEntry) => {
        if (!newEntry.project_id) return;

        setSaving(true);
        try {
            const timesheetsToCreate = [];

            weekDates.forEach((date) => {
                const dateStr = formatFullDate(date);
                const hours = newEntry.hours?.[dateStr];
                if (hours && parseFloat(hours) > 0) {
                    timesheetsToCreate.push({
                        project_id: newEntry.project_id,
                        task_id: newEntry.task_id || null,
                        work_date: dateStr,
                        work_hours: parseFloat(hours),
                        work_type: "NORMAL",
                        description: newEntry.task_name || "",
                    });
                }
            });

            if (timesheetsToCreate.length > 0) {
                const response = await timesheetApi.batchCreate({ timesheets: timesheetsToCreate });

                if (response.data?.code === 200 || response.data?.success !== false || response.status === 201) {
                    await loadWeekTimesheet();
                    setShowAddDialog(false);
                } else {
                    throw new Error(response.data?.message || response.data?.detail || "创建失败");
                }
            }
        } catch (error) {
            console.error("创建工时记录失败:", error);
            alert("创建工时记录失败，请稍后重试");
        } finally {
            setSaving(false);
        }
    };

    // Handle hours change
    const handleHoursChange = async (entryId, dateStr, value) => {
        const entry = entries.find((e) => e.id === entryId);
        if (!entry) return;

        const hours = parseFloat(value) || 0;

        // Optimistic update
        setEntries(
            entries.map((e) =>
                e.id === entryId ? { ...e, hours: { ...e.hours, [dateStr]: hours } } : e
            )
        );

        // Debounce save
        if (handleHoursChange.timeout) {
            clearTimeout(handleHoursChange.timeout);
        }

        handleHoursChange.timeout = setTimeout(async () => {
            try {
                const existingTimesheetId = entry.timesheet_map?.[dateStr];
                let existingTimesheet = null;

                if (weekData?.timesheets) {
                    existingTimesheet = weekData.timesheets.find((ts) => {
                        const tsDate = typeof ts.work_date === "string" ? ts.work_date.split("T")[0] : ts.work_date;
                        return (
                            ts.id === existingTimesheetId ||
                            (ts.project_id === entry.project_id && ts.task_id === entry.task_id && tsDate === dateStr)
                        );
                    });
                }

                if (hours > 0) {
                    if (existingTimesheet) {
                        await timesheetApi.update(existingTimesheet.id, { work_hours: hours });
                    } else {
                        await timesheetApi.create({
                            project_id: entry.project_id,
                            task_id: entry.task_id || null,
                            work_date: dateStr,
                            work_hours: hours,
                            work_type: "NORMAL",
                            description: entry.task_name || "",
                        });
                    }
                } else if (existingTimesheet) {
                    await timesheetApi.delete(existingTimesheet.id);
                }

                await loadWeekTimesheet();
            } catch (error) {
                console.error("更新工时记录失败:", error);
                await loadWeekTimesheet();
                alert("更新工时记录失败，请稍后重试");
            }
        }, 500);
    };

    // Handle delete entry
    const handleDeleteEntry = async (entryId) => {
        const entry = entries.find((e) => e.id === entryId);
        if (!entry || !confirm("确定要删除这条工时记录吗？")) return;

        try {
            if (entry.timesheet_ids && entry.timesheet_ids.length > 0) {
                for (const tsId of entry.timesheet_ids) {
                    await timesheetApi.delete(tsId);
                }
            }
            await loadWeekTimesheet();
        } catch (error) {
            console.error("删除工时记录失败:", error);
            alert("删除工时记录失败，请稍后重试");
        }
    };

    // Handle submit
    const handleSubmit = async () => {
        const timesheetIds = [];
        entries.forEach((entry) => {
            if (entry.status === "DRAFT" && entry.timesheet_ids) {
                timesheetIds.push(...entry.timesheet_ids);
            }
        });

        if (timesheetIds.length === 0) {
            alert("没有可提交的记录（只有草稿状态的记录可以提交）");
            return;
        }

        if (!confirm(`确定要提交 ${timesheetIds.length} 条工时记录进行审批吗？`)) {
            return;
        }

        setSaving(true);
        try {
            const response = await timesheetApi.submit({ timesheet_ids: timesheetIds });

            if (response.data?.code === 200 || response.data?.message) {
                alert(response.data.message || `成功提交 ${timesheetIds.length} 条工时记录`);
                await loadWeekTimesheet();
            } else {
                throw new Error(response.data?.message || "提交失败");
            }
        } catch (error) {
            console.error("提交工时记录失败:", error);
            alert(error.response?.data?.detail || error.message || "提交工时记录失败，请稍后重试");
        } finally {
            setSaving(false);
        }
    };

    // Handle save draft
    const handleSaveDraft = () => {
        alert("工时记录已自动保存为草稿");
    };

    // Handle copy last week
    const handleCopyLastWeek = async () => {
        if (weekOffset === 0) {
            alert("当前是本周，无法复制上周数据");
            return;
        }

        if (!confirm("确定要复制上周的工时记录到本周吗？")) {
            return;
        }

        setSaving(true);
        try {
            const lastWeekStart = getWeekDates(weekOffset - 1)[0];
            const lastWeekStartStr = formatFullDate(lastWeekStart);

            const lastWeekResponse = await timesheetApi.getWeek({ week_start: lastWeekStartStr });
            const lastWeekData = lastWeekResponse.data?.data || lastWeekResponse.data;
            const lastWeekTimesheets = lastWeekData.timesheets || [];

            if (lastWeekTimesheets.length === 0) {
                alert("上周没有工时记录可复制");
                return;
            }

            const timesheetsToCreate = [];
            const currentWeekStart = weekDates[0];

            lastWeekTimesheets.forEach((ts) => {
                const lastWeekDate = new Date(ts.work_date);
                const dayOfWeek = lastWeekDate.getDay() === 0 ? 7 : lastWeekDate.getDay();
                const currentWeekDate = new Date(currentWeekStart);
                currentWeekDate.setDate(currentWeekStart.getDate() + dayOfWeek - 1);

                const dateStr = formatFullDate(currentWeekDate);
                const existing = entries.find(
                    (e) => e.project_id === ts.project_id && e.task_id === ts.task_id && e.hours?.[dateStr]
                );

                if (!existing && parseFloat(ts.work_hours || 0) > 0) {
                    timesheetsToCreate.push({
                        project_id: ts.project_id,
                        rd_project_id: ts.rd_project_id,
                        task_id: ts.task_id,
                        work_date: dateStr,
                        work_hours: parseFloat(ts.work_hours || 0),
                        work_type: ts.work_type || "NORMAL",
                        description: ts.description || "",
                    });
                }
            });

            if (timesheetsToCreate.length > 0) {
                await timesheetApi.batchCreate({ timesheets: timesheetsToCreate });
                alert(`成功复制 ${timesheetsToCreate.length} 条工时记录`);
                await loadWeekTimesheet();
            } else {
                alert("本周已有对应日期的工时记录，无需复制");
            }
        } catch (error) {
            console.error("复制上周工时记录失败:", error);
            alert("复制上周工时记录失败，请稍后重试");
        } finally {
            setSaving(false);
        }
    };

    return {
        // State
        weekOffset,
        setWeekOffset,
        entries,
        showAddDialog,
        setShowAddDialog,
        loading,
        saving,
        projects,
        weekDates,
        isCurrentWeek,
        weeklyTotal,
        dailyTotals,

        // Handlers
        handleAddEntry,
        handleHoursChange,
        handleDeleteEntry,
        handleSubmit,
        handleSaveDraft,
        handleCopyLastWeek,
    };
}
