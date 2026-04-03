import { Route } from "react-router-dom";
import { QualityProtectedRoute } from "../../components/common/ProtectedRoute";
import { lazyLoad } from "../lazyLoad";

const QualityWorkstation = lazyLoad(() => import("../../pages/quality/QualityWorkstation"));
const InspectionList = lazyLoad(() => import("../../pages/quality/InspectionList"));
const InspectionDetail = lazyLoad(() => import("../../pages/quality/InspectionDetail"));
const InspectionNew = lazyLoad(() => import("../../pages/quality/InspectionNew"));
const QualityIssues = lazyLoad(() => import("../../pages/quality/QualityIssues"));
const IssueDetail = lazyLoad(() => import("../../pages/quality/IssueDetail"));
const AcceptanceList = lazyLoad(() => import("../../pages/quality/AcceptanceList"));
const AcceptanceDetail = lazyLoad(() => import("../../pages/quality/AcceptanceDetail"));
const QualityReports = lazyLoad(() => import("../../pages/quality/QualityReports"));
const NCManagement = lazyLoad(() => import("../../pages/quality/NCManagement"));
const ReportTemplates = lazyLoad(() => import("../../pages/ReportTemplates"));
const ReportGeneration = lazyLoad(() => import("../../pages/ReportGeneration"));
const ReportArchives = lazyLoad(() => import("../../pages/ReportArchives"));

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
