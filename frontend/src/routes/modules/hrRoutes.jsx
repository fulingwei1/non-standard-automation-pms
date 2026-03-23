import { lazy } from "react";
import { Route } from "react-router-dom";

// ---- 懒加载页面组件（人力资源模块） ----
const PerformanceCenter = lazy(() => import("../../pages/PerformanceCenter"));
const TalentMatchingCenter = lazy(() => import("../../pages/TalentMatchingCenter"));
const PerformanceManagement = lazy(() => import("../../pages/PerformanceManagement"));
const PerformanceRanking = lazy(() => import("../../pages/PerformanceRanking"));
const PerformanceContract = lazy(() => import("../../pages/PerformanceContract"));
const PerformanceIndicators = lazy(() => import("../../pages/PerformanceIndicators"));
const PerformanceResults = lazy(() => import("../../pages/PerformanceResults"));
const MonthlySummary = lazy(() => import("../../pages/MonthlySummary"));
const MyPerformance = lazy(() => import("../../pages/MyPerformance"));
const MyBonus = lazy(() => import("../../pages/MyBonus"));
const EvaluationTaskList = lazy(() => import("../../pages/EvaluationTaskList"));
const EvaluationScoring = lazy(() => import("../../pages/EvaluationScoring"));
const EvaluationWeightConfig = lazy(() => import("../../pages/EvaluationWeightConfig"));
const QualificationManagement = lazy(() => import("../../pages/QualificationManagement"));
const QualificationLevelForm = lazy(() => import("../../pages/QualificationLevelForm"));
const CompetencyModelForm = lazy(() => import("../../pages/CompetencyModelForm"));
const EmployeeQualificationForm = lazy(() => import("../../pages/EmployeeQualificationForm"));
const QualificationAssessmentList = lazy(() => import("../../pages/QualificationAssessmentList"));
const AttendanceManagement = lazy(() => import("../../pages/AttendanceManagement"));
const EngineerPerformanceDashboard = lazy(() => import("../../pages/EngineerPerformanceDashboard"));
const EngineerPerformanceRanking = lazy(() => import("../../pages/EngineerPerformanceRanking"));
const EngineerPerformanceDetail = lazy(() => import("../../pages/EngineerPerformanceDetail"));
const EngineerCollaboration = lazy(() => import("../../pages/EngineerCollaboration"));
const EngineerKnowledge = lazy(() => import("../../pages/EngineerKnowledge"));

export function HRRoutes() {
  return (
    <>
      <Route path="/hr/performance-center" element={<PerformanceCenter />} />
      <Route path="/hr/talent-matching-center" element={<TalentMatchingCenter />} />
      <Route path="/performance" element={<PerformanceManagement />} />
      <Route path="/performance/ranking" element={<PerformanceRanking />} />
      <Route path="/performance-contract" element={<PerformanceContract />} />
      <Route
        path="/performance/indicators"
        element={<PerformanceIndicators />}
      />
      <Route path="/performance/results" element={<PerformanceResults />} />
      <Route
        path="/performance/results/:employeeId"
        element={<PerformanceResults />}
      />
      <Route path="/personal/monthly-summary" element={<MonthlySummary />} />
      <Route path="/personal/my-performance" element={<MyPerformance />} />
      <Route path="/personal/my-bonus" element={<MyBonus />} />
      <Route path="/evaluation-tasks" element={<EvaluationTaskList />} />
      <Route path="/evaluation/:taskId" element={<EvaluationScoring />} />
      <Route
        path="/evaluation-weight-config"
        element={<EvaluationWeightConfig />}
      />
      <Route path="/qualifications" element={<QualificationManagement />} />
      <Route
        path="/qualifications/levels/new"
        element={<QualificationLevelForm />}
      />
      <Route
        path="/qualifications/levels/:id"
        element={<QualificationLevelForm />}
      />
      <Route
        path="/qualifications/levels/:id/edit"
        element={<QualificationLevelForm />}
      />
      <Route
        path="/qualifications/models/new"
        element={<CompetencyModelForm />}
      />
      <Route
        path="/qualifications/models/:id"
        element={<CompetencyModelForm />}
      />
      <Route
        path="/qualifications/models/:id/edit"
        element={<CompetencyModelForm />}
      />
      <Route
        path="/qualifications/employees/certify"
        element={<EmployeeQualificationForm />}
      />
      <Route
        path="/qualifications/employees/:employeeId"
        element={<EmployeeQualificationForm />}
      />
      <Route
        path="/qualifications/employees/:employeeId/view"
        element={<EmployeeQualificationForm />}
      />
      <Route
        path="/qualifications/employees/:employeeId/promote"
        element={<EmployeeQualificationForm />}
      />
      <Route
        path="/qualifications/assessments"
        element={<QualificationAssessmentList />}
      />
      <Route path="/attendance-management" element={<AttendanceManagement />} />
      <Route path="/hr/attendance" element={<AttendanceManagement />} />
      <Route
        path="/engineer-performance"
        element={<EngineerPerformanceDashboard />}
      />
      <Route
        path="/engineer-performance/ranking"
        element={<EngineerPerformanceRanking />}
      />
      <Route
        path="/engineer-performance/engineer/:userId"
        element={<EngineerPerformanceDetail />}
      />
      <Route
        path="/engineer-performance/collaboration"
        element={<EngineerCollaboration />}
      />
      <Route
        path="/engineer-performance/knowledge"
        element={<EngineerKnowledge />}
      />
    </>
  );
}
