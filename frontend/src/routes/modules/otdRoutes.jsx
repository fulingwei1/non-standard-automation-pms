import { Route } from "react-router-dom";
import { lazyLoad } from "../lazyLoad";

const OTDDashboard = lazyLoad(() => import("../../pages/OTDDashboard"));
const OTDProjectDetail = lazyLoad(() => import("../../pages/OTDProjectDetail"));
const MarginDashboard = lazyLoad(() => import("../../pages/MarginDashboard"));
const OTDThresholdConfig = lazyLoad(() => import("../../pages/OTDThresholdConfig"));
const OTDProjectCompare = lazyLoad(() => import("../../pages/OTDProjectCompare"));
const PmMonthlyCheck = lazyLoad(() => import("../../pages/PmMonthlyCheck"));
const BomCostCheck = lazyLoad(() => import("../../pages/BomCostCheck"));
const OtdMetrics = lazyLoad(() => import("../../pages/OtdMetrics"));

export function OTDRoutes() {
  return (
    <>
      <Route path="/otd/dashboard" element={<OTDDashboard />} />
      <Route path="/otd/scan/:projectId" element={<OTDProjectDetail />} />
      <Route path="/otd/margin-dashboard" element={<MarginDashboard />} />
      <Route path="/otd/thresholds" element={<OTDThresholdConfig />} />
      <Route path="/otd/compare" element={<OTDProjectCompare />} />
      <Route path="/otd/metrics" element={<OtdMetrics />} />
      <Route path="/otd/pm-check" element={<PmMonthlyCheck />} />
      <Route path="/otd/bom-check" element={<BomCostCheck />} />
      <Route path="/otd/bom-check/:projectId" element={<BomCostCheck />} />
    </>
  );
}
