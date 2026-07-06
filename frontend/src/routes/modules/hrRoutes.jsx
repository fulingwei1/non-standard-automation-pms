import { Route } from "react-router-dom";
import { lazyLoad } from "../lazyLoad";
import { ModuleProtectedRoute } from "../../lib/permission";

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

const PERFORMANCE_PERMISSIONS = ["performance:manage", "evaluation:config:manage"];
const STAFF_MATCHING_PERMISSIONS = [
  "staff:tag:manage",
  "staff:profile:read",
  "staff:need:read",
  "staff:match:read",
];

const protect = (element, permission, moduleName) => (
  <ModuleProtectedRoute permission={permission} moduleName={moduleName}>
    {element}
  </ModuleProtectedRoute>
);

const protectAny = (element, permissions, moduleName) => (
  <ModuleProtectedRoute permissions={permissions} moduleName={moduleName}>
    {element}
  </ModuleProtectedRoute>
);

export function HRRoutes() {
  return (
    <>
      <Route
        path="/hr/performance-center"
        element={protectAny(<PerformanceCenter />, PERFORMANCE_PERMISSIONS, "绩效中心")}
      />
      <Route
        path="/hr/talent-matching-center"
        element={protectAny(<TalentMatchingCenter />, STAFF_MATCHING_PERMISSIONS, "人才匹配中心")}
      />
      <Route path="/performance" element={protectAny(<PerformanceManagement />, PERFORMANCE_PERMISSIONS, "绩效管理")} />
      <Route path="/performance/ranking" element={protectAny(<PerformanceRanking />, PERFORMANCE_PERMISSIONS, "绩效排名")} />
      <Route path="/performance-contract" element={protectAny(<PerformanceContract />, PERFORMANCE_PERMISSIONS, "绩效合约")} />
      <Route
        path="/performance/indicators"
        element={protectAny(<PerformanceIndicators />, PERFORMANCE_PERMISSIONS, "绩效指标")}
      />
      <Route path="/performance/results" element={protectAny(<PerformanceResults />, PERFORMANCE_PERMISSIONS, "绩效结果")} />
      <Route
        path="/performance/results/:employeeId"
        element={protectAny(<PerformanceResults />, PERFORMANCE_PERMISSIONS, "绩效结果")}
      />
      <Route path="/personal/monthly-summary" element={<MonthlySummary />} />
      <Route path="/personal/my-performance" element={<MyPerformance />} />
      <Route path="/personal/my-bonus" element={<MyBonus />} />
      <Route path="/evaluation-tasks" element={protect(<EvaluationTaskList />, "evaluation:task:read", "绩效评价")} />
      <Route path="/evaluation/:taskId" element={protect(<EvaluationScoring />, "evaluation:task:read", "绩效评价")} />
      <Route
        path="/evaluation-weight-config"
        element={protectAny(<EvaluationWeightConfig />, PERFORMANCE_PERMISSIONS, "评价权重配置")}
      />
      <Route path="/qualifications" element={protect(<QualificationManagement />, "qualification:read", "资质管理")} />
      <Route
        path="/qualifications/levels/new"
        element={protect(<QualificationLevelForm />, "qualification:read", "资质等级")}
      />
      <Route
        path="/qualifications/levels/:id"
        element={protect(<QualificationLevelForm />, "qualification:read", "资质等级")}
      />
      <Route
        path="/qualifications/levels/:id/edit"
        element={protect(<QualificationLevelForm />, "qualification:read", "资质等级")}
      />
      <Route
        path="/qualifications/models/new"
        element={protect(<CompetencyModelForm />, "qualification:read", "能力模型")}
      />
      <Route
        path="/qualifications/models/:id"
        element={protect(<CompetencyModelForm />, "qualification:read", "能力模型")}
      />
      <Route
        path="/qualifications/models/:id/edit"
        element={protect(<CompetencyModelForm />, "qualification:read", "能力模型")}
      />
      <Route
        path="/qualifications/employees/certify"
        element={protect(<EmployeeQualificationForm />, "qualification:read", "员工资质")}
      />
      <Route
        path="/qualifications/employees/:employeeId"
        element={protect(<EmployeeQualificationForm />, "qualification:read", "员工资质")}
      />
      <Route
        path="/qualifications/employees/:employeeId/view"
        element={protect(<EmployeeQualificationForm />, "qualification:read", "员工资质")}
      />
      <Route
        path="/qualifications/employees/:employeeId/promote"
        element={protect(<EmployeeQualificationForm />, "qualification:read", "员工资质")}
      />
      <Route
        path="/qualifications/assessments"
        element={protect(<QualificationAssessmentList />, "qualification:read", "资质评估")}
      />
      <Route path="/attendance-management" element={protect(<AttendanceManagement />, "hr:read", "考勤管理")} />
      <Route path="/hr/attendance" element={protect(<AttendanceManagement />, "hr:read", "考勤管理")} />
      <Route
        path="/engineer-performance"
        element={protect(<EngineerPerformanceDashboard />, "performance:engineer:read", "工程师绩效")}
      />
      <Route
        path="/engineer-performance/ranking"
        element={protect(<EngineerPerformanceRanking />, "performance:engineer:read", "工程师绩效排名")}
      />
      <Route
        path="/engineer-performance/engineer/:userId"
        element={protect(<EngineerPerformanceDetail />, "performance:engineer:read", "工程师绩效详情")}
      />
      <Route
        path="/engineer-performance/collaboration"
        element={protect(<EngineerCollaboration />, "engineer:collaboration:read", "工程师协作")}
      />
      <Route
        path="/engineer-performance/knowledge"
        element={protect(<EngineerKnowledge />, "performance:engineer:read", "工程师知识")}
      />
    </>
  );
}
