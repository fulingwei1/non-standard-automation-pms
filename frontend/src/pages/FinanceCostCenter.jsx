import { useMemo } from "react";
import TabbedCenterPage from "../components/layout/TabbedCenterPage";
import CostAccounting from "./CostAccounting";
import CostCollection from "./CostCollection";
import QuoteActualCompare from "./QuoteActualCompare";
import CostVarianceAnalysis from "./CostVarianceAnalysis";
import LaborCostDetail from "./LaborCostDetail";

export default function FinanceCostCenter() {
  const tabs = useMemo(
    () => [
      {
        value: "accounting",
        label: "成本核算",
        permission: "cost:accounting:read",
        render: () => <CostAccounting />,
      },
      {
        value: "collection",
        label: "成本归集",
        permission: "cost:accounting:read",
        render: () => <CostCollection />,
      },
      {
        value: "quotes",
        label: "报价对比",
        permission: "cost:accounting:read",
        render: () => <QuoteActualCompare />,
      },
      {
        value: "variance",
        label: "成本偏差",
        permission: "cost:accounting:read",
        render: () => <CostVarianceAnalysis />,
      },
      {
        value: "labor",
        label: "人工成本",
        permission: "cost:accounting:read",
        render: () => <LaborCostDetail />,
      },
    ],
    [],
  );

  return (
    <TabbedCenterPage
      tabs={tabs}
      showHeader={false}
      defaultTab="accounting"
    />
  );
}
