/**
 * BasicInfoCard - 基本信息卡片
 */
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Input } from "../../components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../../components/ui/select";

export default function BasicInfoCard({ formData, setFormData, opportunities, isEdit }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>基本信息</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="text-sm font-medium mb-2 block">商机 *</label>
            <Select
              value={formData.opportunity_id?.toString() || ""}
              onValueChange={(val) =>
                setFormData({
                  ...formData,
                  opportunity_id: val ? parseInt(val) : null,
                })
              }
              disabled={isEdit}
            >
              <SelectTrigger>
                <SelectValue placeholder="选择商机" />
              </SelectTrigger>
              <SelectContent>
                {(opportunities || []).map((opp) => (
                  <SelectItem key={opp.id} value={opp.id.toString()}>
                    {opp.opp_code} - {opp.opp_name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <label className="text-sm font-medium mb-2 block">报价编码</label>
            <Input
              value={formData.quote_code || ""}
              onChange={(e) =>
                setFormData({ ...formData, quote_code: e.target.value })
              }
              placeholder="自动生成"
              disabled={isEdit}
            />
          </div>
          <div>
            <label className="text-sm font-medium mb-2 block">报价名称</label>
            <Input
              value={formData.quote_name || ""}
              onChange={(e) =>
                setFormData({ ...formData, quote_name: e.target.value })
              }
              placeholder="报价名称"
            />
          </div>
          <div>
            <label className="text-sm font-medium mb-2 block">
              有效期(天)
            </label>
            <Input
              type="number"
              value={formData.valid_days ?? ""}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  valid_days: parseInt(e.target.value) || 30,
                })
              }
            />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
