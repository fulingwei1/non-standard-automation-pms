import { useMemo } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Calculator, Lightbulb } from "lucide-react";

import { PageHeader } from "../components/layout";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { toast } from "../components/ui/toast";
import CostEstimateForm from "../components/presales/CostEstimateForm";

function parseAmount(value) {
  const amount = Number(value);
  if (!Number.isFinite(amount) || amount < 0) {
    return 0;
  }
  return amount;
}

export default function PresalesCostEstimation() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const bidding = useMemo(
    () => ({
      id: searchParams.get("id") || undefined,
      name: searchParams.get("name") || "售前技术方案",
      amount: parseAmount(searchParams.get("amount")),
    }),
    [searchParams],
  );

  const handleSave = (result) => {
    if (result?.status === "submitted") {
      toast.success("成本估算已提交");
      return;
    }

    toast.success("成本估算草稿已保存");
  };

  const handleCancel = () => {
    navigate("/presales-workbench");
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="成本估算"
        description="按技术方案拆分成本结构，输出建议报价与毛利参考。"
        actions={[
          {
            label: "查看技术方案",
            icon: Lightbulb,
            to: "/presales/technical-solutions",
            variant: "outline",
          },
        ]}
      />

      <Card className="bg-surface-1/50 border border-white/5">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-white">
            <Calculator className="h-5 w-5 text-amber-300" />
            {bidding.name}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="rounded-xl border border-white/5 bg-surface-100/60 px-4 py-3 text-sm text-slate-300">
            {bidding.amount > 0 ? `当前预算参考：¥${bidding.amount}万` : "可直接填写成本项，系统会自动计算建议报价。"}
          </div>

          <CostEstimateForm
            bidding={bidding}
            onSave={handleSave}
            onCancel={handleCancel}
          />

          <div className="flex justify-end">
            <Button variant="ghost" onClick={() => navigate("/presales-workbench")}>
              返回售前工作台
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
