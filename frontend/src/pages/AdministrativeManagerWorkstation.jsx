/**
 * Administrative Manager Workstation - Main dashboard for administrative manager
 * Features: Office supplies management, Meeting management, Vehicle management,
 * Fixed assets management, Employee attendance, Administrative approvals
 * Core Functions: Administrative affairs, Asset management, Employee services, Approval workflow
 */

import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import {
  ClipboardCheck,
  BarChart3
} from "lucide-react";
import { PageHeader } from "../components/layout";
import { Button } from "../components/ui";
import { staggerContainer, fadeIn } from "../lib/animations";
import {
  employeeApi,
  departmentApi,
  pmoApi,
  ecnApi,
  purchaseApi
} from "../services/api";
import { formatDate } from "../lib/utils";

import {
  StatCardsGrid,
  BudgetProgress,
  OfficeSuppliesStatus,
  TodaysMeetings,
  PendingApprovals,
  VehicleStatus,
  AttendanceStatistics,
  ApprovalDetailDialog,
  MeetingDetailDialog,
  formatCurrency
} from "../components/administrative-manager-workstation";

export default function AdministrativeManagerWorkstation() {
  const [_loading, setLoading] = useState(true);
  const [_error, setError] = useState(null);
  const [stats, setStats] = useState({
    totalEmployees: 0,
    attendanceRate: 0,
    pendingApprovals: 0,
    urgentApprovals: 0,
    monthlyAdminBudget: 0,
    monthlyAdminSpent: 0,
    budgetUtilization: 0,
    officeSuppliesTotal: 0,
    officeSuppliesLowStock: 0,
    meetingsThisWeek: 0,
    meetingsToday: 0,
    totalVehicles: 0,
    vehiclesInUse: 0,
    fixedAssetsTotal: 0,
    fixedAssetsValue: 0,
    officeSuppliesMonthlyCost: 0,
    monthlyFuelCost: 0
  });
  const [pendingApprovals, setPendingApprovals] = useState([]);
  const [meetings, setMeetings] = useState([]);
  const [officeSupplies, _setOfficeSupplies] = useState([]);
  const [vehicles, _setVehicles] = useState([]);
  const [attendanceStats, _setAttendanceStats] = useState([]);
  const [selectedMeeting, setSelectedMeeting] = useState(null);
  const [showMeetingDetail, setShowMeetingDetail] = useState(false);
  const [selectedApproval, setSelectedApproval] = useState(null);
  const [showApprovalDetail, setShowApprovalDetail] = useState(false);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);

      try {
        const empRes = await employeeApi.getStatistics({});
        const empStats = empRes.data || empRes;
        if (empStats) {
          setStats((prev) => ({
            ...prev,
            totalEmployees: empStats.total || prev.totalEmployees
          }));
        }
      } catch (err) {
        console.error("Failed to load employee statistics:", err);
      }

      try {
        const deptRes = await departmentApi.getStatistics({});
        const _deptStats = deptRes.data || deptRes;
      } catch (err) {
        console.error("Failed to load department statistics:", err);
      }

      try {
        const today = new Date().toISOString().split("T")[0];
        const meetingsRes = await pmoApi.meetings.list({
          date_from: today,
          page_size: 50
        });
        const meetingsData = meetingsRes.data || meetingsRes;
        const meetingsList = meetingsData.items || meetingsData || [];

        const transformedMeetings = meetingsList.map((meeting) => ({
          id: meeting.id,
          title: meeting.meeting_title || meeting.title || "",
          organizer: meeting.organizer_name || "未知",
          department: meeting.department || "未知部门",
          room: meeting.meeting_room || "未指定",
          date: meeting.meeting_date ? meeting.meeting_date.split("T")[0] : "",
          time:
          meeting.start_time && meeting.end_time ?
          `${meeting.start_time}-${meeting.end_time}` :
          "",
          attendees: meeting.attendees?.length || 0,
          status:
          meeting.status === "SCHEDULED" ?
          "scheduled" :
          meeting.status === "ONGOING" ?
          "ongoing" :
          meeting.status === "COMPLETED" ?
          "completed" :
          "scheduled"
        }));

        setMeetings(transformedMeetings);

        const todayMeetings = transformedMeetings.filter(
          (m) => m.date === today
        );
        const thisWeekMeetings = transformedMeetings.filter((m) => {
          const meetingDate = new Date(m.date);
          const weekStart = new Date();
          weekStart.setDate(weekStart.getDate() - weekStart.getDay());
          return meetingDate >= weekStart;
        });

        setStats((prev) => ({
          ...prev,
          meetingsToday: todayMeetings.length,
          meetingsThisWeek: thisWeekMeetings.length
        }));
      } catch (err) {
        console.error("Failed to load meetings:", err);
      }

      try {
        const allApprovals = [];

        try {
          const ecnRes = await ecnApi.list({
            status: "SUBMITTED",
            page_size: 20
          });
          const ecnData = ecnRes.data || ecnRes;
          const ecns = ecnData.items || ecnData || [];
          ecns.forEach((ecn) => {
            allApprovals.push({
              id: `ecn-${ecn.id}`,
              type: "ecn",
              title: `设计变更申请 - ${ecn.ecn_no || "ECN"}`,
              applicant: ecn.created_by_name || "未知",
              department: ecn.department || "未知部门",
              amount: 0,
              submitTime: formatDate(ecn.created_at) || "",
              priority:
              ecn.priority === "URGENT" ?
              "urgent" :
              ecn.priority === "HIGH" ?
              "high" :
              "medium",
              status: "pending"
            });
          });
        } catch (err) {
          console.error("Failed to load ECN approvals:", err);
        }

        try {
          const prRes = await purchaseApi.requests.list({
            status: "SUBMITTED",
            page_size: 20
          });
          const prData = prRes.data || prRes;
          const prs = prData.items || prData || [];
          prs.forEach((pr) => {
            allApprovals.push({
              id: `pr-${pr.id}`,
              type: "office_supplies",
              title: `采购申请 - ${pr.request_no || pr.id}`,
              applicant: pr.created_by_name || "未知",
              department: pr.department || "未知部门",
              amount: parseFloat(pr.total_amount || 0),
              submitTime: formatDate(pr.created_at) || "",
              priority: pr.urgent ? "high" : "medium",
              status: "pending"
            });
          });
        } catch (err) {
          console.error("Failed to load purchase request approvals:", err);
        }

        setPendingApprovals(allApprovals.slice(0, 5));
        setStats((prev) => ({
          ...prev,
          pendingApprovals: allApprovals.length,
          urgentApprovals: allApprovals.filter(
            (a) => a.priority === "urgent" || a.priority === "high"
          ).length
        }));
      } catch (err) {
        console.error("Failed to load approvals:", err);
      }
    } catch (err) {
      console.error("Failed to load dashboard data:", err);
      setError(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6">

      <PageHeader
        title="行政经理工作台"
        description={`月度行政预算: ${formatCurrency(stats.monthlyAdminBudget)} | 已使用: ${formatCurrency(stats.monthlyAdminSpent)} (${stats.budgetUtilization}%)`}
        actions={
        <motion.div variants={fadeIn} className="flex gap-2">
            <Button variant="outline" className="flex items-center gap-2">
              <BarChart3 className="w-4 h-4" />
              行政报表
            </Button>
            <Button
            className="flex items-center gap-2"
            onClick={() => window.location.href = "/approval-center"}>

              <ClipboardCheck className="w-4 h-4" />
              审批中心
            </Button>
        </motion.div>
        } />

      <StatCardsGrid stats={stats} />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <BudgetProgress stats={stats} />

          <OfficeSuppliesStatus officeSupplies={officeSupplies} />

          <TodaysMeetings
            meetings={meetings}
            setSelectedMeeting={setSelectedMeeting}
            setShowMeetingDetail={setShowMeetingDetail}
          />
        </div>

        <div className="space-y-6">
          <PendingApprovals
            pendingApprovals={pendingApprovals}
            setSelectedApproval={setSelectedApproval}
            setShowApprovalDetail={setShowApprovalDetail}
          />

          <VehicleStatus vehicles={vehicles} />

          <AttendanceStatistics attendanceStats={attendanceStats} />
        </div>
      </div>

      <ApprovalDetailDialog
        open={showApprovalDetail}
        onOpenChange={setShowApprovalDetail}
        selectedApproval={selectedApproval}
      />

      <MeetingDetailDialog
        open={showMeetingDetail}
        onOpenChange={setShowMeetingDetail}
        selectedMeeting={selectedMeeting}
      />
    </motion.div>);

}
