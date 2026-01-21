import { Route } from "react-router-dom";

import PerformanceManagement from "../../pages/PerformanceManagement";
import PerformanceRanking from "../../pages/PerformanceRanking";
import PerformanceIndicators from "../../pages/PerformanceIndicators";
import PerformanceResults from "../../pages/PerformanceResults";
import MonthlySummary from "../../pages/MonthlySummary";
import MyPerformance from "../../pages/MyPerformance";
import MyBonus from "../../pages/MyBonus";
import EvaluationTaskList from "../../pages/EvaluationTaskList";
import EvaluationScoring from "../../pages/EvaluationScoring";
import EvaluationWeightConfig from "../../pages/EvaluationWeightConfig";
import QualificationManagement from "../../pages/QualificationManagement";
import QualificationLevelForm from "../../pages/QualificationLevelForm";
import CompetencyModelForm from "../../pages/CompetencyModelForm";
import EmployeeQualificationForm from "../../pages/EmployeeQualificationForm";
import QualificationAssessmentList from "../../pages/QualificationAssessmentList";
import EngineerPerformanceDashboard from "../../pages/EngineerPerformanceDashboard";
import EngineerPerformanceRanking from "../../pages/EngineerPerformanceRanking";
import EngineerPerformanceDetail from "../../pages/EngineerPerformanceDetail";
import EngineerCollaboration from "../../pages/EngineerCollaboration";
import EngineerKnowledge from "../../pages/EngineerKnowledge";

export function HRRoutes() {
  return (
    <>
      <Route path="/performance" element={<PerformanceManagement />} />
      <Route path="/performance/ranking" element={<PerformanceRanking />} />
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
