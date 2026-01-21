import { Route, Navigate } from "react-router-dom";
import { AppProtectedRoute } from "../../components/common/AppProtectedRoute";

import Dashboard from "../../pages/Dashboard";
import UnifiedDashboard from "../../pages/UnifiedDashboard";
import ChairmanWorkstation from "../../pages/ChairmanWorkstation";
import GeneralManagerWorkstation from "../../pages/gm-workstation";
import AdminDashboard from "../../pages/AdminDashboard";
import OperationDashboard from "../../pages/OperationDashboard";
import StrategyAnalysis from "../../pages/StrategyAnalysis";
import KeyDecisions from "../../pages/KeyDecisions";
import ManagementRhythmDashboard from "../../pages/ManagementRhythmDashboard";
import MeetingMap from "../../pages/MeetingMap";
import StrategicMeetingManagement from "../../pages/StrategicMeetingManagement";
import StrategicMeetingDetail from "../../pages/StrategicMeetingDetail";
import MeetingReports from "../../pages/MeetingReports";
import CultureWall from "../../pages/CultureWall";
import Shipments from "../../pages/Shipments";
import DeliveryManagement from "../../pages/DeliveryManagement";
import Documents from "../../pages/Documents";

export function DashboardRoutes() {
  return (
    <>
      <Route
        path="/"
        element={
          <AppProtectedRoute>
            <Dashboard />
          </AppProtectedRoute>
        }
      />
      {/* 统一工作台 - 新的统一入口 */}
      <Route
        path="/dashboard"
        element={
          <AppProtectedRoute>
            <UnifiedDashboard />
          </AppProtectedRoute>
        }
      />
      {/* 旧工作台路由重定向到统一工作台 */}
      <Route path="/workstation" element={<Navigate to="/dashboard" replace />} />
      <Route path="/sales-dashboard" element={<Navigate to="/dashboard" replace />} />
      <Route path="/engineer-workstation" element={<Navigate to="/dashboard" replace />} />
      <Route path="/production-dashboard" element={<Navigate to="/dashboard" replace />} />
      <Route path="/procurement-dashboard" element={<Navigate to="/dashboard" replace />} />
      <Route path="/manufacturing-director-dashboard" element={<Navigate to="/dashboard" replace />} />
      <Route path="/production-manager-dashboard" element={<Navigate to="/dashboard" replace />} />
      <Route path="/worker-workstation" element={<Navigate to="/dashboard" replace />} />
      <Route path="/customer-service-dashboard" element={<Navigate to="/dashboard" replace />} />
      <Route path="/finance-manager-dashboard" element={<Navigate to="/dashboard" replace />} />
      <Route path="/hr-manager-dashboard" element={<Navigate to="/dashboard" replace />} />
      <Route path="/presales-dashboard" element={<Navigate to="/dashboard" replace />} />
      <Route path="/business-support" element={<Navigate to="/dashboard" replace />} />
      <Route path="/procurement-manager-dashboard" element={<Navigate to="/dashboard" replace />} />
      <Route
        path="/chairman-dashboard"
        element={
          <AppProtectedRoute>
            <ChairmanWorkstation />
          </AppProtectedRoute>
        }
      />
      <Route
        path="/gm-dashboard"
        element={
          <AppProtectedRoute>
            <GeneralManagerWorkstation />
          </AppProtectedRoute>
        }
      />
      <Route path="/admin-dashboard" element={<AdminDashboard />} />
      <Route path="/operation" element={<OperationDashboard />} />
      <Route path="/strategy-analysis" element={<StrategyAnalysis />} />
      <Route path="/key-decisions" element={<KeyDecisions />} />
      <Route
        path="/management-rhythm-dashboard"
        element={<ManagementRhythmDashboard />}
      />
      <Route path="/meeting-map" element={<MeetingMap />} />
      <Route
        path="/strategic-meetings"
        element={<StrategicMeetingManagement />}
      />
      <Route
        path="/strategic-meetings/:id"
        element={<StrategicMeetingDetail />}
      />
      <Route path="/meeting-reports" element={<MeetingReports />} />
      <Route path="/meeting-reports/:id" element={<MeetingReports />} />
      <Route path="/culture-wall" element={<CultureWall />} />
      <Route path="/shipments" element={<Shipments />} />
      <Route path="/pmc/delivery-plan" element={<DeliveryManagement />} />
      <Route path="/pmc/delivery-orders" element={<DeliveryManagement />} />
      <Route path="/pmc/delivery-orders/:id" element={<DeliveryManagement />} />
      <Route
        path="/pmc/delivery-orders/:id/edit"
        element={<DeliveryManagement />}
      />
      <Route path="/pmc/delivery-orders/new" element={<DeliveryManagement />} />
      <Route path="/documents" element={<Documents />} />
    </>
  );
}
