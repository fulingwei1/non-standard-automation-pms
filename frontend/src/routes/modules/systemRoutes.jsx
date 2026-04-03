import { Route, Navigate } from "react-router-dom";
import { lazyLoad } from "../lazyLoad";

const NotificationCenter = lazyLoad(() => import("../../pages/NotificationCenter"));
const StageTemplateManagement = lazyLoad(() => import("../../pages/StageTemplateManagement"));
const StageTemplateEditor = lazyLoad(() => import("../../pages/StageTemplateEditor"));
const Timesheet = lazyLoad(() => import("../../pages/Timesheet"));
const TimesheetDashboard = lazyLoad(() => import("../../pages/TimesheetDashboard"));
const TimesheetBatchOperations = lazyLoad(() => import("../../pages/TimesheetBatchOperations"));
const Settings = lazyLoad(() => import("../../pages/Settings"));
const UserManagement = lazyLoad(() => import("../../pages/UserManagement"));
const RoleManagement = lazyLoad(() => import("../../pages/RoleManagement"));
const PermissionManagement = lazyLoad(() => import("../../pages/PermissionManagement"));
const SchedulerMonitoringDashboard = lazyLoad(() => import("../../pages/SchedulerMonitoringDashboard"));
const SchedulerConfigManagement = lazyLoad(() => import("../../pages/SchedulerConfigManagement"));
const AuditLogs = lazyLoad(() => import("../../pages/AuditLogs"));
const DataImportExport = lazyLoad(() => import("../../pages/DataImportExport"));
const HourlyRateManagement = lazyLoad(() => import("../../pages/HourlyRateManagement"));
const HRManagement = lazyLoad(() => import("../../pages/HRManagement"));
const PresalesIntegration = lazyLoad(() => import("../../pages/PresalesIntegration"));
const ProjectRoles = lazyLoad(() => import("../../pages/ProjectRoles"));
const CustomerManagement = lazyLoad(() => import("../../pages/CustomerManagement"));
const Customer360 = lazyLoad(() => import("../../pages/Customer360"));
const SupplierManagementData = lazyLoad(() => import("../../pages/SupplierManagementData"));
const DepartmentManagement = lazyLoad(() => import("../../pages/DepartmentManagement"));
const OrganizationManagement = lazyLoad(() => import("../../pages/OrganizationManagement"));
const PositionManagement = lazyLoad(() => import("../../pages/PositionManagement"));
const PermissionDebug = lazyLoad(() => import("../../pages/PermissionDebug"));
const AlertCenter = lazyLoad(() => import("../../pages/AlertCenter"));
const AlertDetail = lazyLoad(() => import("../../pages/AlertDetail"));
const AlertRuleConfig = lazyLoad(() => import("../../pages/alert-rule-config"));
const AlertStatistics = lazyLoad(() => import("../../pages/AlertStatistics"));
const AlertSubscription = lazyLoad(() => import("../../pages/AlertSubscription"));
const AlertSubscriptionSettings = lazyLoad(() => import("../../pages/AlertSubscriptionSettings"));
const Acceptance = lazyLoad(() => import("../../pages/Acceptance"));
const ApprovalCenter = lazyLoad(() => import("../../pages/ApprovalCenter"));
const ApprovalDetailPage = lazyLoad(() => import("../../pages/ApprovalDetailPage"));
const IssueManagement = lazyLoad(() => import("../../pages/IssueManagement"));
const IssueTemplateManagement = lazyLoad(() => import("../../pages/IssueTemplateManagement"));
const IssueStatisticsSnapshot = lazyLoad(() => import("../../pages/IssueStatisticsSnapshot"));
const ExceptionManagement = lazyLoad(() => import("../../pages/ExceptionManagement"));
const ShortageAlert = lazyLoad(() => import("../../pages/ShortageAlert"));
const ECNManagement = lazyLoad(() => import("../../pages/ECNManagement"));
const ECNDetail = lazyLoad(() => import("../../pages/ECNDetail"));
const ECNTypeManagement = lazyLoad(() => import("../../pages/ECNTypeManagement"));
const ECNOverdueAlerts = lazyLoad(() => import("../../pages/ECNOverdueAlerts"));
const ECNStatistics = lazyLoad(() => import("../../pages/ECNStatistics"));
const ECNCenter = lazyLoad(() => import("../../pages/ECNCenter"));
const TechnicalSpecManagement = lazyLoad(() => import("../../pages/TechnicalSpecManagement"));
const TechnicalReviewList = lazyLoad(() => import("../../pages/TechnicalReviewList"));
const TechnicalReviewDetail = lazyLoad(() => import("../../pages/TechnicalReviewDetail"));
const SpecMatchCheck = lazyLoad(() => import("../../pages/SpecMatchCheck"));
const CustomerServiceDashboard = lazyLoad(() => import("../../pages/CustomerServiceDashboard"));
const ServiceTicketManagement = lazyLoad(() => import("../../pages/ServiceTicketManagement"));
const ServiceRecord = lazyLoad(() => import("../../pages/ServiceRecord"));
const CustomerCommunication = lazyLoad(() => import("../../pages/CustomerCommunication"));
const CustomerSatisfaction = lazyLoad(() => import("../../pages/CustomerSatisfaction"));
const ServiceAnalytics = lazyLoad(() => import("../../pages/ServiceAnalytics"));
const ServiceKnowledgeBase = lazyLoad(() => import("../../pages/ServiceKnowledgeBase"));
const ServiceCenter = lazyLoad(() => import("../../pages/ServiceCenter"));
const DeliveryAcceptanceCenter = lazyLoad(() => import("../../pages/DeliveryAcceptanceCenter"));
const RdProjectList = lazyLoad(() => import("../../pages/RdProjectList"));
const RdProjectDetail = lazyLoad(() => import("../../pages/RdProjectDetail"));
const RdProjectWorklogs = lazyLoad(() => import("../../pages/RdProjectWorklogs"));
const RdProjectDocuments = lazyLoad(() => import("../../pages/RdProjectDocuments"));
const RdCostEntry = lazyLoad(() => import("../../pages/RdCostEntry"));
const RdCostSummary = lazyLoad(() => import("../../pages/RdCostSummary"));
const RdCostReports = lazyLoad(() => import("../../pages/RdCostReports"));
const TagManagement = lazyLoad(() => import("../../pages/TagManagement"));
const EmployeeProfileList = lazyLoad(() => import("../../pages/EmployeeProfileList"));
const EmployeeProfileDetail = lazyLoad(() => import("../../pages/EmployeeProfileDetail"));
const ProjectStaffingNeed = lazyLoad(() => import("../../pages/ProjectStaffingNeed"));
const AIStaffMatching = lazyLoad(() => import("../../pages/AIStaffMatching"));
const MobileWorkerTaskList = lazyLoad(() => import("../../pages/mobile/MobileWorkerTaskList"));
const MobileScanStart = lazyLoad(() => import("../../pages/mobile/MobileScanStart"));
const MobileProgressReport = lazyLoad(() => import("../../pages/mobile/MobileProgressReport"));
const MobileCompleteReport = lazyLoad(() => import("../../pages/mobile/MobileCompleteReport"));
const MobileExceptionReport = lazyLoad(() => import("../../pages/mobile/MobileExceptionReport"));
const MobileMaterialRequisition = lazyLoad(() => import("../../pages/mobile/MobileMaterialRequisition"));
const MobileScanShortage = lazyLoad(() => import("../../pages/mobile/MobileScanShortage"));
const MobileShortageReport = lazyLoad(() => import("../../pages/mobile/MobileShortageReport"));
const MobileMyShortageReports = lazyLoad(() => import("../../pages/mobile/MobileMyShortageReports"));
const ReportGeneration = lazyLoad(() => import("../../pages/ReportGeneration"));
const ReportTemplates = lazyLoad(() => import("../../pages/ReportTemplates"));
const ReportArchives = lazyLoad(() => import("../../pages/ReportArchives"));
const TemplateConfigList = lazyLoad(() => import("../../pages/TemplateConfigList"));
const TemplateConfigEditor = lazyLoad(() => import("../../pages/TemplateConfigEditor"));
const TemplateCenter = lazyLoad(() => import("../../pages/TemplateCenter"));
const AccountPermissionCenter = lazyLoad(() => import("../../pages/AccountPermissionCenter"));
const OrganizationCenter = lazyLoad(() => import("../../pages/OrganizationCenter"));

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
      <Route path="/change-management/ecn-center" element={<ECNCenter />} />
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
      <Route path="/service/center" element={<ServiceCenter />} />
      <Route path="/delivery/acceptance-center" element={<DeliveryAcceptanceCenter />} />
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
      <Route path="/rd-cost" element={<Navigate to="/rd-cost-summary" replace />} />

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
      <Route path="/system/template-center" element={<TemplateCenter />} />
      <Route path="/system/account-permission-center" element={<AccountPermissionCenter />} />
      <Route path="/system/organization-center" element={<OrganizationCenter />} />
      <Route path="/stage-templates" element={<StageTemplateManagement />} />
      <Route path="/stage-templates/:templateId/edit" element={<StageTemplateEditor />} />
      <Route path="/report-generation" element={<ReportGeneration />} />
      <Route path="/report-templates" element={<ReportTemplates />} />
      <Route path="/report-archives" element={<ReportArchives />} />
      <Route path="/template-configs" element={<TemplateConfigList />} />
      <Route path="/template-configs/new" element={<TemplateConfigEditor />} />
      <Route
        path="/template-configs/edit/:id"
        element={<TemplateConfigEditor />}
      />
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
      <Route path="/sales/customers/:id/360" element={<Customer360 />} />
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
