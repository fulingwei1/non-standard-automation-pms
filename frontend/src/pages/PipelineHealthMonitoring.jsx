/**
 * Pipeline Health Monitoring Page - 全链条健康度监控
 * Features: 线索、商机、报价、合同、回款各环节健康度监控
 */

import { useState, useEffect } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  XCircle } from
"lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Input,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger } from
"../components/ui";
import { healthApi } from "../services/api";

export default function PipelineHealthMonitoring() {
  const [_loading, setLoading] = useState(false);
  const [warnings, setWarnings] = useState([]);
  const [selectedEntity, setSelectedEntity] = useState({
    type: "lead",
    id: null
  });

  const loadWarnings = async () => {
    setLoading(true);
    try {
      const response = await healthApi.getHealthWarnings();
      if (response.data?.data?.warnings) {
        setWarnings(response.data.data.warnings);
      }
    } catch (error) {
      console.error("加载健康度预警失败:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadWarnings();
  }, []);

  const getHealthBadge = (status) => {
    const configs = {
      H1: { label: "正常", variant: "success", color: "text-green-600" },
      H2: { label: "有风险", variant: "warning", color: "text-amber-600" },
      H3: { label: "阻塞", variant: "destructive", color: "text-red-600" },
      H4: { label: "已完结", variant: "secondary", color: "text-slate-600" }
    };
    const config = configs[status] || configs.H1;
    return <Badge variant={config.variant}>{config.label}</Badge>;
  };

  const getHealthIcon = (status) => {
    if (status === "H1") {return <CheckCircle2 className="h-5 w-5 text-green-600" />;}
    if (status === "H2") {return <AlertTriangle className="h-5 w-5 text-amber-600" />;}
    if (status === "H3") {return <XCircle className="h-5 w-5 text-red-600" />;}
    return <CheckCircle2 className="h-5 w-5 text-slate-600" />;
  };

  const calculateHealth = async (type, id) => {
    if (!id) {return;}
    setLoading(true);
    try {
      let response;
      switch (type) {
        case "lead":
          response = await healthApi.getLeadHealth(id);
          break;
        case "opportunity":
          response = await healthApi.getOpportunityHealth(id);
          break;
        case "quote":
          response = await healthApi.getQuoteHealth(id);
          break;
        case "contract":
          response = await healthApi.getContractHealth(id);
          break;
        case "payment":
          response = await healthApi.getPaymentHealth(id);
          break;
        default:
          return;
      }
      if (response.data?.data) {
        alert(
          `健康度: ${response.data.data.health_status} (${response.data.data.health_score}分)\n风险因素: ${response.data.data.risk_factors?.join(", ") || "无"}`
        );
      }
    } catch (error) {
      console.error("计算健康度失败:", error);
      alert("计算健康度失败: " + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader title="全链条健康度监控" />

      {/* 健康度预警 */}
      {warnings.length > 0 &&
      <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-amber-500" />
              健康度预警
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {warnings.slice(0, 10).map((warning, idx) =>
            <div
              key={idx}
              className="flex items-center justify-between p-3 bg-amber-50 rounded-lg">

                  <div>
                    <div className="font-medium">{warning.entity_name}</div>
                    <div className="text-sm text-slate-500">
                      {warning.entity_type} · {warning.risk_factors?.join(", ")}
                    </div>
                  </div>
                  {getHealthBadge(warning.health_status)}
            </div>
            )}
            </div>
          </CardContent>
      </Card>
      }

      {/* 健康度计算工具 */}
      <Card>
        <CardHeader>
          <CardTitle>健康度计算工具</CardTitle>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="lead">
            <TabsList>
              <TabsTrigger value="lead">线索</TabsTrigger>
              <TabsTrigger value="opportunity">商机</TabsTrigger>
              <TabsTrigger value="quote">报价</TabsTrigger>
              <TabsTrigger value="contract">合同</TabsTrigger>
              <TabsTrigger value="payment">回款</TabsTrigger>
            </TabsList>
            <TabsContent value="lead" className="mt-4">
              <div className="space-y-4">
                <div>
                  <label className="text-sm text-slate-500 mb-1 block">
                    线索ID
                  </label>
                  <Input
                    type="number"
                    placeholder="请输入线索ID"
                    value={selectedEntity.type === "lead" ? selectedEntity.id || "" : ""}
                    onChange={(e) =>
                    setSelectedEntity({
                      type: "lead",
                      id: e.target.value ? parseInt(e.target.value) : null
                    })
                    } />

                </div>
                <Button
                  onClick={() => calculateHealth("lead", selectedEntity.id)}
                  disabled={!selectedEntity.id || selectedEntity.type !== "lead"}>

                  计算健康度
                </Button>
              </div>
            </TabsContent>
            <TabsContent value="opportunity" className="mt-4">
              <div className="space-y-4">
                <div>
                  <label className="text-sm text-slate-500 mb-1 block">
                    商机ID
                  </label>
                  <Input
                    type="number"
                    placeholder="请输入商机ID"
                    value={selectedEntity.type === "opportunity" ? selectedEntity.id || "" : ""}
                    onChange={(e) =>
                    setSelectedEntity({
                      type: "opportunity",
                      id: e.target.value ? parseInt(e.target.value) : null
                    })
                    } />

                </div>
                <Button
                  onClick={() =>
                  calculateHealth("opportunity", selectedEntity.id)
                  }
                  disabled={!selectedEntity.id || selectedEntity.type !== "opportunity"}>

                  计算健康度
                </Button>
              </div>
            </TabsContent>
            <TabsContent value="quote" className="mt-4">
              <div className="space-y-4">
                <div>
                  <label className="text-sm text-slate-500 mb-1 block">
                    报价ID
                  </label>
                  <Input
                    type="number"
                    placeholder="请输入报价ID"
                    value={selectedEntity.type === "quote" ? selectedEntity.id || "" : ""}
                    onChange={(e) =>
                    setSelectedEntity({
                      type: "quote",
                      id: e.target.value ? parseInt(e.target.value) : null
                    })
                    } />

                </div>
                <Button
                  onClick={() => calculateHealth("quote", selectedEntity.id)}
                  disabled={!selectedEntity.id || selectedEntity.type !== "quote"}>

                  计算健康度
                </Button>
              </div>
            </TabsContent>
            <TabsContent value="contract" className="mt-4">
              <div className="space-y-4">
                <div>
                  <label className="text-sm text-slate-500 mb-1 block">
                    合同ID
                  </label>
                  <Input
                    type="number"
                    placeholder="请输入合同ID"
                    value={selectedEntity.type === "contract" ? selectedEntity.id || "" : ""}
                    onChange={(e) =>
                    setSelectedEntity({
                      type: "contract",
                      id: e.target.value ? parseInt(e.target.value) : null
                    })
                    } />

                </div>
                <Button
                  onClick={() =>
                  calculateHealth("contract", selectedEntity.id)
                  }
                  disabled={!selectedEntity.id || selectedEntity.type !== "contract"}>

                  计算健康度
                </Button>
              </div>
            </TabsContent>
            <TabsContent value="payment" className="mt-4">
              <div className="space-y-4">
                <div>
                  <label className="text-sm text-slate-500 mb-1 block">
                    发票ID
                  </label>
                  <Input
                    type="number"
                    placeholder="请输入发票ID"
                    value={selectedEntity.type === "payment" ? selectedEntity.id || "" : ""}
                    onChange={(e) =>
                    setSelectedEntity({
                      type: "payment",
                      id: e.target.value ? parseInt(e.target.value) : null
                    })
                    } />

                </div>
                <Button
                  onClick={() => calculateHealth("payment", selectedEntity.id)}
                  disabled={!selectedEntity.id || selectedEntity.type !== "payment"}>

                  计算健康度
                </Button>
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      {/* 健康度说明 */}
      <Card>
        <CardHeader>
          <CardTitle>健康度等级说明</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              {getHealthIcon("H1")}
              <div>
                <div className="font-medium">H1 - 正常</div>
                <div className="text-sm text-slate-500">
                  流程正常推进，无风险因素
                </div>
              </div>
            </div>
            <div className="flex items-center gap-3">
              {getHealthIcon("H2")}
              <div>
                <div className="font-medium">H2 - 有风险</div>
                <div className="text-sm text-slate-500">
                  存在风险因素，需要关注
                </div>
              </div>
            </div>
            <div className="flex items-center gap-3">
              {getHealthIcon("H3")}
              <div>
                <div className="font-medium">H3 - 阻塞</div>
                <div className="text-sm text-slate-500">
                  流程受阻，需要立即处理
                </div>
              </div>
            </div>
            <div className="flex items-center gap-3">
              {getHealthIcon("H4")}
              <div>
                <div className="font-medium">H4 - 已完结</div>
                <div className="text-sm text-slate-500">
                  流程已完成或已关闭
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>);

}