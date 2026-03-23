import { lazy } from "react";
import { Route } from "react-router-dom";
import { QualityProtectedRoute } from "../../components/common/ProtectedRoute";

// ---- 懒加载页面组件（质量模块） ----
const QualityWorkstation = lazy(() => import("../../pages/quality/QualityWorkstation"));
const InspectionList = lazy(() => import("../../pages/quality/InspectionList"));
const InspectionNew = lazy(() => import("../../pages/quality/InspectionNew"));
const InspectionDetail = lazy(() => import("../../pages/quality/InspectionDetail"));
const QualityIssues = lazy(() => import("../../pages/quality/QualityIssues"));
const IssueDetail = lazy(() => import("../../pages/quality/IssueDetail"));
const AcceptanceList = lazy(() => import("../../pages/quality/AcceptanceList"));
const AcceptanceDetail = lazy(() => import("../../pages/quality/AcceptanceDetail"));
const QualityReports = lazy(() => import("../../pages/quality/QualityReports"));
const ReportTemplates = lazy(() => import("../../pages/ReportTemplates"));
const ReportGeneration = lazy(() => import("../../pages/ReportGeneration"));
const ReportArchives = lazy(() => import("../../pages/ReportArchives"));
const NCManagement = lazy(() => import("../../pages/quality/NCManagement"));

export function QualityRoutes() {
  return (
    <>
      {/* 质量工作台首页 */}
      <Route
        path="/workstation/quality"
        element={
          <QualityProtectedRoute>
            <QualityWorkstation />
          </QualityProtectedRoute>
        }
      />

      {/* 检验任务 */}
      <Route
        path="/quality/inspections"
        element={
          <QualityProtectedRoute>
            <InspectionList />
          </QualityProtectedRoute>
        }
      />
      <Route
        path="/quality/inspections/new"
        element={
          <QualityProtectedRoute>
            <InspectionNew />
          </QualityProtectedRoute>
        }
      />
      <Route
        path="/quality/inspections/:id"
        element={
          <QualityProtectedRoute>
            <InspectionDetail />
          </QualityProtectedRoute>
        }
      />

      {/* 质量问题 */}
      <Route
        path="/quality/issues"
        element={
          <QualityProtectedRoute>
            <QualityIssues />
          </QualityProtectedRoute>
        }
      />
      <Route
        path="/quality/issues/:id"
        element={
          <QualityProtectedRoute>
            <IssueDetail />
          </QualityProtectedRoute>
        }
      />

      {/* 验收管理 */}
      <Route
        path="/quality/acceptance"
        element={
          <QualityProtectedRoute>
            <AcceptanceList />
          </QualityProtectedRoute>
        }
      />
      <Route
        path="/quality/acceptance/:id"
        element={
          <QualityProtectedRoute>
            <AcceptanceDetail />
          </QualityProtectedRoute>
        }
      />

      {/* 质量报表 */}
      <Route
        path="/quality/reports"
        element={
          <QualityProtectedRoute>
            <QualityReports />
          </QualityProtectedRoute>
        }
      />
      <Route
        path="/quality/reports/templates"
        element={
          <QualityProtectedRoute>
            <ReportTemplates />
          </QualityProtectedRoute>
        }
      />
      <Route
        path="/quality/reports/generate"
        element={
          <QualityProtectedRoute>
            <ReportGeneration />
          </QualityProtectedRoute>
        }
      />
      <Route
        path="/quality/reports/archives"
        element={
          <QualityProtectedRoute>
            <ReportArchives />
          </QualityProtectedRoute>
        }
      />

      {/* 不合格品管理 */}
      <Route
        path="/quality/nc"
        element={
          <QualityProtectedRoute>
            <NCManagement />
          </QualityProtectedRoute>
        }
      />
    </>
  );
}
