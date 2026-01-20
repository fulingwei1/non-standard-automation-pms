import { motion } from "framer-motion";
import { RefreshCw } from "lucide-react";
import { PageHeader } from "../../components/layout";
import { staggerContainer } from "../../lib/animations";
import { useTimesheet } from "./hooks";
import {
    AddEntryDialog,
    WeekSummaryCards,
    WeekNavigation,
    TimesheetTable,
} from "./components";

export default function Timesheet() {
    const {
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
        handleAddEntry,
        handleHoursChange,
        handleDeleteEntry,
        handleSubmit,
        handleSaveDraft,
        handleCopyLastWeek,
    } = useTimesheet();

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
            <div className="container mx-auto px-4 py-6">
                <motion.div
                    variants={staggerContainer}
                    initial="hidden"
                    animate="visible"
                    className="space-y-6"
                >
                    <PageHeader
                        title="工时填报"
                        description="记录您的工作时间，便于项目成本核算与绩效统计"
                    />

                    {loading && (
                        <div className="flex items-center justify-center py-8">
                            <RefreshCw className="w-6 h-6 animate-spin text-blue-500 mr-2" />
                            <span className="text-slate-400">加载中...</span>
                        </div>
                    )}

                    {/* Week Summary */}
                    <WeekSummaryCards weeklyTotal={weeklyTotal} entries={entries} />

                    {/* Week Navigation */}
                    <WeekNavigation
                        weekDates={weekDates}
                        weekOffset={weekOffset}
                        setWeekOffset={setWeekOffset}
                        isCurrentWeek={isCurrentWeek}
                        loading={loading}
                        saving={saving}
                        entries={entries}
                        onAddRecord={() => setShowAddDialog(true)}
                        onCopyLastWeek={handleCopyLastWeek}
                        onSaveDraft={handleSaveDraft}
                        onSubmit={handleSubmit}
                    />

                    {/* Timesheet Table */}
                    <TimesheetTable
                        weekDates={weekDates}
                        entries={entries}
                        loading={loading}
                        dailyTotals={dailyTotals}
                        weeklyTotal={weeklyTotal}
                        onHoursChange={handleHoursChange}
                        onDeleteEntry={handleDeleteEntry}
                    />

                    {/* Add Entry Dialog */}
                    <AddEntryDialog
                        open={showAddDialog}
                        onOpenChange={setShowAddDialog}
                        onAdd={handleAddEntry}
                        weekDates={weekDates}
                        projects={projects}
                        loading={loading}
                    />
                </motion.div>
            </div>
        </div>
    );
}
