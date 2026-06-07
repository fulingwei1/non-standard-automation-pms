import { Route, Navigate } from "react-router-dom";
import { lazyLoad } from "../lazyLoad";
import { PresalesCenterRedirect } from "./presalesRedirects";

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
      <Route path="/presales/cost-estimation" element={<PresalesCenterRedirect tab="cost" />} />
      <Route path="/presales-tasks" element={<PresalesCenterRedirect tab="reviews" />} />
      <Route path="/presales/assessments" element={<PresalesCenterRedirect tab="reviews" />} />
      <Route path="/presales/presale-analytics" element={<PresaleAnalytics />} />
      <Route path="/presale-analytics" element={<Navigate to="/presales/presale-analytics" replace />} />
      <Route path="/presales/solutions" element={<PresalesCenterRedirect tab="solutions" />} />
      <Route path="/solutions" element={<PresalesCenterRedirect tab="solutions" />} />
      <Route path="/solutions/:id" element={<SolutionDetail />} />
      <Route path="/requirement-survey" element={<PresalesCenterRedirect tab="surveys" />} />
      <Route path="/bidding" element={<PresalesCenterRedirect tab="bids" />} />
      <Route path="/presales/bids" element={<PresalesCenterRedirect tab="bids" />} />
      <Route path="/knowledge-base" element={<KnowledgeBase />} />
      <Route path="/presales/templates" element={<PresalesCenterRedirect tab="knowledge" />} />
      <Route path="/presales/technical-parameters" element={<PresalesCenterRedirect tab="parameters" />} />
      <Route path="/presales/ticket-board" element={<PresalesCenterRedirect tab="reviews" />} />
      <Route path="/presale-templates" element={<PresalesCenterRedirect tab="knowledge" />} />
    </>
  );
}
