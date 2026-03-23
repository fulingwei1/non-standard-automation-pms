import { lazy } from "react";
import { Route, Navigate } from "react-router-dom";

// ---- 懒加载页面组件（系统管理模块） ----

// 告警中心
const AlertCenter = lazy(() => import("../../pages/AlertCenter"));
const AlertDetail = lazy(() => import("../../pages/AlertDetail"));
const AlertRuleConfig = lazy(() => import("../../pages/alert-rule-config"));
const AlertStatistics = lazy(() => import("../../pages/AlertStatistics"));
const AlertSubscription = lazy(() => import("../../pages/AlertSubscription"));
const AlertSubscriptionSettings = lazy(() => import("../../pages/AlertSubscriptionSettings"));

// ECN 变更管理
const ECNCenter = lazy(() => import("../../pages/ECNCenter"));
const ECNDetail = lazy(() => import("../../pages/ECNDetail"));
const ECNManagement = lazy(() => import("../../pages/ECNManagement"));
const ECNOverdueAlerts = lazy(() => import("../../pages/ECNOverdueAlerts"));
const ECNStatistics = lazy(() => import("../../pages/ECNStatistics"));
const ECNTypeManagement = lazy(() => import("../../pages/ECNTypeManagement"));
const ExceptionManagement = lazy(() => import("../../pages/ExceptionManagement"));
const ShortageAlert = lazy(() => import("../../pages/ShortageAlert"));

// 质量与验收
const Acceptance = lazy(() => import("../../pages/Acceptance"));
const ApprovalCenter = lazy(() => import("../../pages/ApprovalCenter"));
const ApprovalDetailPage = lazy(() => import("../../pages/ApprovalDetailPage"));
const IssueManagement = lazy(() => import("../../pages/IssueManagement"));
const IssueTemplateManagement = lazy(() => import("../../pages/IssueTemplateManagement"));
const IssueStatisticsSnapshot = lazy(() => import("../../pages/IssueStatisticsSnapshot"));

// 技术规格管理
const TechnicalSpecManagement = lazy(() => import("../../pages/TechnicalSpecManagement"));
const TechnicalReviewList = lazy(() => import("../../pages/TechnicalReviewList"));
const TechnicalReviewDetail = lazy(() => import("../../pages/TechnicalReviewDetail"));
const SpecMatchCheck = lazy(() => import("../../pages/SpecMatchCheck"));

// 客户服务
const CustomerServiceCenter = lazy(() => import("../../pages/CustomerServiceCenter"));
const CustomerServiceDashboard = lazy(() => import("../../pages/CustomerServiceDashboard"));
const ServiceTicketManagement = lazy(() => import("../../pages/ServiceTicketManagement"));
const ServiceRecord = lazy(() => import("../../pages/ServiceRecord"));
const CustomerCommunication = lazy(() => import("../../pages/CustomerCommunication"));
const CustomerSatisfaction = lazy(() => import("../../pages/CustomerSatisfaction"));
const ServiceAnalytics = lazy(() => import("../../pages/ServiceAnalytics"));
const ServiceKnowledgeBase = lazy(() => import("../../pages/ServiceKnowledgeBase"));

// 研发项目管理
const RdProjectList = lazy(() => import("../../pages/RdProjectList"));
const RdProjectDetail = lazy(() => import("../../pages/RdProjectDetail"));
const RdProjectWorklogs = lazy(() => import("../../pages/RdProjectWorklogs"));
const RdProjectDocuments = lazy(() => import("../../pages/RdProjectDocuments"));
const RdCostEntry = lazy(() => import("../../pages/RdCostEntry"));
const RdCostSummary = lazy(() => import("../../pages/RdCostSummary"));
const RdCostReports = lazy(() => import("../../pages/RdCostReports"));

// AI 人员匹配
const TagManagement = lazy(() => import("../../pages/TagManagement"));
const EmployeeProfileList = lazy(() => import("../../pages/EmployeeProfileList"));
const EmployeeProfileDetail = lazy(() => import("../../pages/EmployeeProfileDetail"));
const ProjectStaffingNeed = lazy(() => import("../../pages/ProjectStaffingNeed"));
const AIStaffMatching = lazy(() => import("../../pages/AIStaffMatching"));

// 个人中心
const NotificationCenter = lazy(() => import("../../pages/NotificationCenter"));
const Timesheet = lazy(() => import("../../pages/Timesheet"));
const TimesheetDashboard = lazy(() => import("../../pages/TimesheetDashboard"));
const TimesheetBatchOperations = lazy(() => import("../../pages/TimesheetBatchOperations"));
const Settings = lazy(() => import("../../pages/Settings"));

// 系统管理
const TemplateCenter = lazy(() => import("../../pages/TemplateCenter"));
const AccountPermissionCenter = lazy(() => import("../../pages/AccountPermissionCenter"));
const OrganizationCenter = lazy(() => import("../../pages/OrganizationCenter"));
const StageTemplateManagement = lazy(() => import("../../pages/StageTemplateManagement"));
const StageTemplateEditor = lazy(() => import("../../pages/StageTemplateEditor"));
const ReportGeneration = lazy(() => import("../../pages/ReportGeneration"));
const ReportTemplates = lazy(() => import("../../pages/ReportTemplates"));
const ReportArchives = lazy(() => import("../../pages/ReportArchives"));
const TemplateConfigList = lazy(() => import("../../pages/TemplateConfigList"));
const TemplateConfigEditor = lazy(() => import("../../pages/TemplateConfigEditor"));
const UserManagement = lazy(() => import("../../pages/UserManagement"));
const RoleManagement = lazy(() => import("../../pages/RoleManagement"));
const PermissionManagement = lazy(() => import("../../pages/PermissionManagement"));
const SchedulerMonitoringDashboard = lazy(() => import("../../pages/SchedulerMonitoringDashboard"));
const SchedulerConfigManagement = lazy(() => import("../../pages/SchedulerConfigManagement"));
const AuditLogs = lazy(() => import("../../pages/AuditLogs"));
const DataImportExport = lazy(() => import("../../pages/DataImportExport"));
const HourlyRateManagement = lazy(() => import("../../pages/HourlyRateManagement"));
const HRManagement = lazy(() => import("../../pages/HRManagement"));
const PresalesIntegration = lazy(() => import("../../pages/PresalesIntegration"));
const ProjectRoles = lazy(() => import("../../pages/ProjectRoles"));

// 主数据管理
const CustomerManagement = lazy(() => import("../../pages/CustomerManagement"));
const Customer360 = lazy(() => import("../../pages/SalesAI/Customer360"));
const SupplierManagementData = lazy(() => import("../../pages/SupplierManagementData"));
const DepartmentManagement = lazy(() => import("../../pages/DepartmentManagement"));
const OrganizationManagement = lazy(() => import("../../pages/OrganizationManagement"));
const PositionManagement = lazy(() => import("../../pages/PositionManagement"));

// 移动端页面
const MobileWorkerTaskList = lazy(() => import("../../pages/mobile/MobileWorkerTaskList"));
const MobileScanStart = lazy(() => import("../../pages/mobile/MobileScanStart"));
const MobileProgressReport = lazy(() => import("../../pages/mobile/MobileProgressReport"));
const MobileCompleteReport = lazy(() => import("../../pages/mobile/MobileCompleteReport"));
const MobileExceptionReport = lazy(() => import("../../pages/mobile/MobileExceptionReport"));
const MobileMaterialRequisition = lazy(() => import("../../pages/mobile/MobileMaterialRequisition"));
const MobileScanShortage = lazy(() => import("../../pages/mobile/MobileScanShortage"));
const MobileShortageReport = lazy(() => import("../../pages/mobile/MobileShortageReport"));
const MobileMyShortageReports = lazy(() => import("../../pages/mobile/MobileMyShortageReports"));

// 调试
const PermissionDebug = lazy(() => import("../../pages/PermissionDebug"));

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
      <Route path="/customer-service/center" element={<CustomerServiceCenter />} />
      <Route
        path="/service/center"
        element={<Navigate to="/customer-service/center?tab=tickets" replace />}
      />
      <Route
        path="/delivery/acceptance-center"
        element={<Navigate to="/customer-service/center?tab=acceptance" replace />}
      />
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
