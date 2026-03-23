import { useMemo } from "react";

export default function ProcurementAnalysisCenter() {
  const tabs = useMemo(
    () => [
      {
        value: "shortage",
        label: "齐套缺料",
        permission: "material:analysis:read",
        render: () => <MaterialAnalysis />,
      },
      {
        value: "pricing",
        label: "价格趋势",
        permission: "purchase:read",
        render: () => <SupplierPriceTrend />,
      },
      {
        value: "analytics",
        label: "采购分析",
        permission: "purchase:analysis:read",
        render: () => <ProcurementAnalysis />,
      },
    ],
    [],
  );

  return (
    <TabbedCenterPage
      tabs={tabs}
      showHeader={false}
      defaultTab="shortage"
    />
  );
}
