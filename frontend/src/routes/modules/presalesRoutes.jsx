import { Route, Navigate } from "react-router-dom";
import { lazyLoad } from "../lazyLoad";

const PresalesWorkstation = lazyLoad(() => import("../../pages/PresalesWorkstation"));
const PresalesWorkbench = lazyLoad(() => import("../../pages/PresalesWorkbench"));
const SalesPresaleWorkbench = lazyLoad(() => import("../../pages/SalesPresaleWorkbench"));
const PresaleAnalytics = lazyLoad(() => import("../../pages/PresaleAnalytics"));
const PresalesManagerWorkstation = lazyLoad(() => import("../../pages/PresalesManagerWorkstation"));
const PresalesReviewCenter = lazyLoad(() => import("../../pages/PresalesReviewCenter"));
const SolutionDetail = lazyLoad(() => import("../../pages/SolutionDetail"));
const KnowledgeBase = lazyLoad(() => import("../../pages/KnowledgeBase"));

export function PresalesRoutes() {
  return (
    <>
      <Route path="/presales/workbench" element={<PresalesWorkbench />} />
      <Route path="/presales/workbench/sales" element={<SalesPresaleWorkbench />} />
      <Route path="/presales/workbench/execution" element={<PresalesWorkstation />} />
      <Route path="/presales/workbench/manager" element={<PresalesManagerWorkstation />} />
      <Route path="/presales-workbench" element={<Navigate to="/presales/workbench" replace />} />
      <Route path="/presales-dashboard" element={<PresalesWorkstation />} />
      <Route
        path="/presales-manager-dashboard"
        element={<PresalesManagerWorkstation />}
      />
      <Route path="/presales/technical-solutions" element={<PresalesReviewCenter />} />
      <Route path="/presales/cost-estimation" element={<Navigate to="/presales/technical-solutions?tab=cost" replace />} />
      <Route path="/presales-tasks" element={<Navigate to="/presales/technical-solutions?tab=reviews" replace />} />
      <Route path="/presales/assessments" element={<Navigate to="/presales/technical-solutions?tab=reviews" replace />} />
      <Route path="/presales/presale-analytics" element={<PresaleAnalytics />} />
      <Route path="/presale-analytics" element={<Navigate to="/presales/presale-analytics" replace />} />
      <Route path="/presales/solutions" element={<Navigate to="/presales/technical-solutions?tab=solutions" replace />} />
      <Route path="/solutions" element={<Navigate to="/presales/technical-solutions?tab=solutions" replace />} />
      <Route path="/solutions/:id" element={<SolutionDetail />} />
      <Route path="/requirement-survey" element={<Navigate to="/presales/technical-solutions?tab=surveys" replace />} />
      <Route path="/bidding" element={<Navigate to="/presales/technical-solutions?tab=bids" replace />} />
      <Route path="/presales/bids" element={<Navigate to="/presales/technical-solutions?tab=bids" replace />} />
      <Route path="/knowledge-base" element={<KnowledgeBase />} />
      <Route path="/presales/templates" element={<Navigate to="/presales/technical-solutions?tab=knowledge" replace />} />
      <Route path="/presales/technical-parameters" element={<Navigate to="/presales/technical-solutions?tab=parameters" replace />} />
      <Route path="/presales/ticket-board" element={<Navigate to="/presales/technical-solutions?tab=reviews" replace />} />
      <Route path="/presale-templates" element={<Navigate to="/presales/technical-solutions?tab=knowledge" replace />} />
    </>
  );
}
