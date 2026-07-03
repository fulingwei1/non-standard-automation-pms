/**
 * AdditionalInfoCard - 其他信息卡片
 */
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Input } from "../../components/ui/input";

export default function AdditionalInfoCard({ formData, setFormData, versionData, setVersionData }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>其他信息</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="text-sm font-medium mb-2 block">交期(天)</label>
            <Input
              type="number"
              value={versionData.lead_time_days ?? ""}
              onChange={(e) =>
                setVersionData({
                  ...versionData,
                  lead_time_days: parseInt(e.target.value) || 60,
                })
              }
            />
          </div>
          <div>
            <label className="text-sm font-medium mb-2 block">付款条件</label>
            <Input
              value={formData.payment_terms || ""}
              onChange={(e) =>
                setFormData({ ...formData, payment_terms: e.target.value })
              }
              placeholder="付款条件"
            />
          </div>
          <div>
            <label className="text-sm font-medium mb-2 block">交付条件</label>
            <Input
              value={formData.delivery_terms || ""}
              onChange={(e) =>
                setFormData({ ...formData, delivery_terms: e.target.value })
              }
              placeholder="交付条件"
            />
          </div>
          <div>
            <label className="text-sm font-medium mb-2 block">风险条款</label>
            <Input
              value={versionData.risk_terms || ""}
              onChange={(e) =>
                setVersionData({ ...versionData, risk_terms: e.target.value })
              }
              placeholder="风险条款"
            />
          </div>
          <div className="md:col-span-2">
            <label className="text-sm font-medium mb-2 block">备注</label>
            <textarea
              className="w-full min-h-[80px] p-3 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 bg-transparent"
              value={formData.note || ""}
              onChange={(e) =>
                setFormData({ ...formData, note: e.target.value })
              }
              placeholder="备注..."
            />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
