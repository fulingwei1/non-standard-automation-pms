import { useMemo } from "react";
import TabbedCenterPage from "../components/layout/TabbedCenterPage";
import PurchaseOrders from "./PurchaseOrders";
import PurchaseRequestList from "./PurchaseRequestList";
import ArrivalManagement from "./ArrivalManagement";

export default function ProcurementExecutionCenter() {
  const tabs = useMemo(
    () => [
      {
        value: "orders",
        label: "采购订单",
        permission: "purchase:read",
        render: () => <PurchaseOrders />,
      },
      {
        value: "requests",
        label: "采购申请",
        permission: "purchase:request:read",
        render: () => <PurchaseRequestList />,
      },
      {
        value: "receipts",
        label: "收货管理",
        permission: "purchase:receipt:read",
        render: () => <ArrivalManagement />,
      },
    ],
    [],
  );

  return (
    <TabbedCenterPage
      tabs={tabs}
      showHeader={false}
      defaultTab="orders"
    />
  );
}
