import { lazyLoad } from "../lazyLoad";

const PerformanceManagement = lazyLoad(() => import("../../pages/PerformanceManagement"));
const PerformanceRanking = lazyLoad(() => import("../../pages/PerformanceRanking"));
const PerformanceIndicators = lazyLoad(() => import("../../pages/PerformanceIndicators"));
const PerformanceResults = lazyLoad(() => import("../../pages/PerformanceResults"));
const MonthlySummary = lazyLoad(() => import("../../pages/MonthlySummary"));
const MyPerformance = lazyLoad(() => import("../../pages/MyPerformance"));
const MyBonus = lazyLoad(() => import("../../pages/MyBonus"));
const EvaluationTaskList = lazyLoad(() => import("../../pages/EvaluationTaskList"));
const EvaluationScoring = lazyLoad(() => import("../../pages/EvaluationScoring"));
const EvaluationWeightConfig = lazyLoad(() => import("../../pages/EvaluationWeightConfig"));
const QualificationManagement = lazyLoad(() => import("../../pages/QualificationManagement"));
const QualificationLevelForm = lazyLoad(() => import("../../pages/QualificationLevelForm"));
const CompetencyModelForm = lazyLoad(() => import("../../pages/CompetencyModelForm"));
const EmployeeQualificationForm = lazyLoad(() => import("../../pages/EmployeeQualificationForm"));
const QualificationAssessmentList = lazyLoad(() => import("../../pages/QualificationAssessmentList"));
const AttendanceManagement = lazyLoad(() => import("../../pages/AttendanceManagement"));
const EngineerPerformanceDashboard = lazyLoad(() => import("../../pages/EngineerPerformanceDashboard"));
const EngineerPerformanceRanking = lazyLoad(() => import("../../pages/EngineerPerformanceRanking"));
const EngineerPerformanceDetail = lazyLoad(() => import("../../pages/EngineerPerformanceDetail"));
const PerformanceContract = lazyLoad(() => import("../../pages/PerformanceContract"));
const EngineerCollaboration = lazyLoad(() => import("../../pages/EngineerCollaboration"));
const EngineerKnowledge = lazyLoad(() => import("../../pages/EngineerKnowledge"));
const PerformanceCenter = lazyLoad(() => import("../../pages/PerformanceCenter"));
const TalentMatchingCenter = lazyLoad(() => import("../../pages/TalentMatchingCenter"));

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
