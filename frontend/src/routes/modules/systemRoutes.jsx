import { Route, Navigate } from "react-router-dom";

import NotificationCenter from "../../pages/NotificationCenter";
import StageTemplateManagement from "../../pages/StageTemplateManagement";
import StageTemplateEditor from "../../pages/StageTemplateEditor";
import Timesheet from "../../pages/Timesheet";
import TimesheetDashboard from "../../pages/TimesheetDashboard";
import TimesheetBatchOperations from "../../pages/TimesheetBatchOperations";
import Settings from "../../pages/Settings";
import UserManagement from "../../pages/UserManagement";
import RoleManagement from "../../pages/RoleManagement";
import PermissionManagement from "../../pages/PermissionManagement";
import SchedulerMonitoringDashboard from "../../pages/SchedulerMonitoringDashboard";
import SchedulerConfigManagement from "../../pages/SchedulerConfigManagement";
import AuditLogs from "../../pages/AuditLogs";
import DataImportExport from "../../pages/DataImportExport";
import HourlyRateManagement from "../../pages/HourlyRateManagement";
import HRManagement from "../../pages/HRManagement";
import PresalesIntegration from "../../pages/PresalesIntegration";
import ProjectRoles from "../../pages/ProjectRoles";
import CustomerManagement from "../../pages/CustomerManagement";
import Customer360 from "../../pages/Customer360";
import SupplierManagementData from "../../pages/SupplierManagementData";
import DepartmentManagement from "../../pages/DepartmentManagement";
import OrganizationManagement from "../../pages/OrganizationManagement";
import PositionManagement from "../../pages/PositionManagement";
import PermissionDebug from "../../pages/PermissionDebug";
import AlertCenter from "../../pages/AlertCenter";
import AlertDetail from "../../pages/AlertDetail";
import AlertRuleConfig from "../../pages/alert-rule-config";
import AlertStatistics from "../../pages/AlertStatistics";
import AlertSubscription from "../../pages/AlertSubscription";
import AlertSubscriptionSettings from "../../pages/AlertSubscriptionSettings";
import Acceptance from "../../pages/Acceptance";
import ApprovalCenter from "../../pages/ApprovalCenter";
import ApprovalDetailPage from "../../pages/ApprovalDetailPage";
import IssueManagement from "../../pages/IssueManagement";
import IssueTemplateManagement from "../../pages/IssueTemplateManagement";
import IssueStatisticsSnapshot from "../../pages/IssueStatisticsSnapshot";
import ExceptionManagement from "../../pages/ExceptionManagement";
import ShortageAlert from "../../pages/ShortageAlert";
import ECNManagement from "../../pages/ECNManagement";
import ECNDetail from "../../pages/ECNDetail";
import ECNTypeManagement from "../../pages/ECNTypeManagement";
import ECNOverdueAlerts from "../../pages/ECNOverdueAlerts";
import ECNStatistics from "../../pages/ECNStatistics";
import TechnicalSpecManagement from "../../pages/TechnicalSpecManagement";
import TechnicalReviewList from "../../pages/TechnicalReviewList";
import TechnicalReviewDetail from "../../pages/TechnicalReviewDetail";
import SpecMatchCheck from "../../pages/SpecMatchCheck";
import CustomerServiceDashboard from "../../pages/CustomerServiceDashboard";
import ServiceTicketManagement from "../../pages/ServiceTicketManagement";
import ServiceRecord from "../../pages/ServiceRecord";
import CustomerCommunication from "../../pages/CustomerCommunication";
import CustomerSatisfaction from "../../pages/CustomerSatisfaction";
import ServiceAnalytics from "../../pages/ServiceAnalytics";
import ServiceKnowledgeBase from "../../pages/ServiceKnowledgeBase";
import RdProjectList from "../../pages/RdProjectList";
import RdProjectDetail from "../../pages/RdProjectDetail";
import RdProjectWorklogs from "../../pages/RdProjectWorklogs";
import RdProjectDocuments from "../../pages/RdProjectDocuments";
import RdCostEntry from "../../pages/RdCostEntry";
import RdCostSummary from "../../pages/RdCostSummary";
import RdCostReports from "../../pages/RdCostReports";
import TagManagement from "../../pages/TagManagement";
import EmployeeProfileList from "../../pages/EmployeeProfileList";
import EmployeeProfileDetail from "../../pages/EmployeeProfileDetail";
import ProjectStaffingNeed from "../../pages/ProjectStaffingNeed";
import AIStaffMatching from "../../pages/AIStaffMatching";
import MobileWorkerTaskList from "../../pages/mobile/MobileWorkerTaskList";
import MobileScanStart from "../../pages/mobile/MobileScanStart";
import MobileProgressReport from "../../pages/mobile/MobileProgressReport";
import MobileCompleteReport from "../../pages/mobile/MobileCompleteReport";
import MobileExceptionReport from "../../pages/mobile/MobileExceptionReport";
import MobileMaterialRequisition from "../../pages/mobile/MobileMaterialRequisition";
import MobileScanShortage from "../../pages/mobile/MobileScanShortage";
import MobileShortageReport from "../../pages/mobile/MobileShortageReport";
import MobileMyShortageReports from "../../pages/mobile/MobileMyShortageReports";

export function SystemRoutes() {
  return (
    <>
      {/* Alerts */}
      <Route path="/alerts" element={<AlertCenter />} />
      <Route path="/alerts/:id" element={<AlertDetail />} />
      <Route path="/alert-rules" element={<AlertRuleConfig />} />
      <Route path="/alert-statistics" element={<AlertStatistics />} />
      <Route path="/alert-subscription" element={<AlertSubscription />} />
      <Route
        path="/alerts/subscriptions"
        element={<AlertSubscriptionSettings />}
      />
      <Route
        path="/settings/alert-subscriptions"
        element={<AlertSubscriptionSettings />}
      />

      {/* ECN Management */}
      <Route path="/change-management/ecn" element={<ECNManagement />} />
      <Route path="/change-management/ecn/:id" element={<ECNDetail />} />
      <Route path="/change-management/ecn-types" element={<ECNTypeManagement />} />
      <Route path="/change-management/ecn/overdue-alerts" element={<ECNOverdueAlerts />} />
      <Route path="/change-management/ecn/statistics" element={<ECNStatistics />} />
      <Route path="/ecn" element={<ECNManagement />} />
      <Route path="/ecn/:id" element={<ECNDetail />} />
      <Route path="/ecn-types" element={<ECNTypeManagement />} />
      <Route path="/ecn/overdue-alerts" element={<ECNOverdueAlerts />} />
      <Route path="/ecn/statistics" element={<ECNStatistics />} />
      <Route path="/exceptions" element={<ExceptionManagement />} />
      <Route path="/shortage-alerts" element={<ShortageAlert />} />

      {/* Quality & Acceptance */}
      <Route path="/acceptance" element={<Acceptance />} />
      <Route path="/approvals" element={<ApprovalCenter />} />
      <Route path="/approvals/:id" element={<ApprovalDetailPage />} />
      <Route path="/issues" element={<IssueManagement />} />
      <Route path="/issue-templates" element={<IssueTemplateManagement />} />
      <Route
        path="/issue-statistics-snapshot"
        element={<IssueStatisticsSnapshot />}
      />

      {/* Technical Spec Management */}
      <Route path="/technical-spec" element={<TechnicalSpecManagement />} />
      <Route path="/technical-reviews" element={<TechnicalReviewList />} />
      <Route
        path="/technical-reviews/new"
        element={<TechnicalReviewDetail />}
      />
      <Route
        path="/technical-reviews/:reviewId"
        element={<TechnicalReviewDetail />}
      />
      <Route
        path="/technical-reviews/:reviewId/edit"
        element={<TechnicalReviewDetail />}
      />
      <Route path="/spec-match-check" element={<SpecMatchCheck />} />

      {/* Customer Service */}
      <Route
        path="/customer-service-dashboard"
        element={<CustomerServiceDashboard />}
      />
      <Route path="/service-tickets" element={<ServiceTicketManagement />} />
      <Route path="/service-records" element={<ServiceRecord />} />
      <Route
        path="/customer-communications"
        element={<CustomerCommunication />}
      />
      <Route path="/customer-satisfaction" element={<CustomerSatisfaction />} />
      <Route path="/service-analytics" element={<ServiceAnalytics />} />
      <Route
        path="/service-knowledge-base"
        element={<ServiceKnowledgeBase />}
      />

      {/* R&D Project Management */}
      <Route path="/rd-projects" element={<RdProjectList />} />
      <Route path="/rd-projects/:id" element={<RdProjectDetail />} />
      <Route path="/rd-projects/:id/worklogs" element={<RdProjectWorklogs />} />
      <Route
        path="/rd-projects/:id/documents"
        element={<RdProjectDocuments />}
      />
      <Route path="/rd-projects/:id/cost-entry" element={<RdCostEntry />} />
      <Route path="/rd-projects/:id/cost-summary" element={<RdCostSummary />} />
      <Route path="/rd-projects/:id/reports" element={<RdCostReports />} />
      <Route path="/rd-cost-entry" element={<RdCostEntry />} />
      <Route path="/rd-cost-summary" element={<RdCostSummary />} />
      <Route path="/rd-cost-reports" element={<RdCostReports />} />

      {/* AI Staff Matching */}
      <Route path="/staff-matching/tags" element={<TagManagement />} />
      <Route
        path="/staff-matching/profiles"
        element={<EmployeeProfileList />}
      />
      <Route
        path="/staff-matching/profiles/:id"
        element={<EmployeeProfileDetail />}
      />
      <Route
        path="/staff-matching/staffing-needs"
        element={<ProjectStaffingNeed />}
      />
      <Route path="/staff-matching/matching" element={<AIStaffMatching />} />

      {/* Personal Center */}
      <Route path="/work-center" element={<Navigate to="/dashboard" replace />} />
      <Route path="/notifications" element={<NotificationCenter />} />
      <Route path="/timesheet" element={<Timesheet />} />
      <Route path="/timesheet/dashboard" element={<TimesheetDashboard />} />
      <Route path="/timesheet/batch" element={<TimesheetBatchOperations />} />
      <Route path="/settings" element={<Settings />} />

      {/* System Management */}
      <Route path="/stage-templates" element={<StageTemplateManagement />} />
      <Route path="/stage-templates/:templateId/edit" element={<StageTemplateEditor />} />
      <Route path="/user-management" element={<UserManagement />} />
      <Route path="/role-management" element={<RoleManagement />} />
      <Route path="/permission-management" element={<PermissionManagement />} />
      <Route
        path="/scheduler-monitoring"
        element={<SchedulerMonitoringDashboard />}
      />
      <Route path="/scheduler-config" element={<SchedulerConfigManagement />} />
      <Route path="/audit-logs" element={<AuditLogs />} />
      <Route path="/data-import-export" element={<DataImportExport />} />
      <Route path="/hourly-rates" element={<HourlyRateManagement />} />
      <Route path="/hr-management" element={<HRManagement />} />
      <Route path="/presales-integration" element={<PresalesIntegration />} />
      <Route path="/projects/:id/roles" element={<ProjectRoles />} />

      {/* Master Data Management */}
      <Route path="/customer-management" element={<CustomerManagement />} />
      <Route path="/customers/:id/360" element={<Customer360 />} />
      <Route
        path="/supplier-management-data"
        element={<SupplierManagementData />}
      />
      <Route path="/department-management" element={<DepartmentManagement />} />
      <Route path="/organization-management" element={<OrganizationManagement />} />
      <Route path="/position-management" element={<PositionManagement />} />

      {/* Mobile Pages */}
      <Route path="/mobile/tasks" element={<MobileWorkerTaskList />} />
      <Route path="/mobile/scan-start" element={<MobileScanStart />} />
      <Route
        path="/mobile/progress-report"
        element={<MobileProgressReport />}
      />
      <Route
        path="/mobile/complete-report"
        element={<MobileCompleteReport />}
      />
      <Route
        path="/mobile/exception-report"
        element={<MobileExceptionReport />}
      />
      <Route
        path="/mobile/material-requisition"
        element={<MobileMaterialRequisition />}
      />
      <Route path="/mobile/scan-shortage" element={<MobileScanShortage />} />
      <Route
        path="/mobile/shortage-report"
        element={<MobileShortageReport />}
      />
      <Route
        path="/mobile/my-shortage-reports"
        element={<MobileMyShortageReports />}
      />

      {/* Debug Routes */}
      <Route path="/debug/permissions" element={<PermissionDebug />} />

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </>
  );
}
