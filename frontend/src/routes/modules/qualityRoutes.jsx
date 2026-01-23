import { Route } from "react-router-dom";
import { QualityProtectedRoute } from "../../components/common/ProtectedRoute";

import QualityWorkstation from "../../pages/quality/QualityWorkstation";
import InspectionList from "../../pages/quality/InspectionList";
import InspectionDetail from "../../pages/quality/InspectionDetail";
import InspectionNew from "../../pages/quality/InspectionNew";
import QualityIssues from "../../pages/quality/QualityIssues";
import IssueDetail from "../../pages/quality/IssueDetail";
import AcceptanceList from "../../pages/quality/AcceptanceList";
import AcceptanceDetail from "../../pages/quality/AcceptanceDetail";
import QualityReports from "../../pages/quality/QualityReports";
import NCManagement from "../../pages/quality/NCManagement";

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
