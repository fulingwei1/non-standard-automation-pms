import { useState, useEffect } from "react";
import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Search,
  RefreshCw,
} from "lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import api from "../services/api";

export default function SpecMatchCheck() {
  const [matchRecords, setMatchRecords] = useState([]);
  const [loading, setLoading] = useState(false);
  const [projectId, setProjectId] = useState("");
  const [matchType, setMatchType] = useState("");
  const [matchStatus, setMatchStatus] = useState("");
  const [checking, setChecking] = useState(false);

  useEffect(() => {
    loadMatchRecords();
  }, [projectId, matchType, matchStatus]);

  const loadMatchRecords = async () => {
    setLoading(true);
    try {
      const params = { page: 1, page_size: 100 };
      if (projectId) {params.project_id = parseInt(projectId);}
      if (matchType) {params.match_type = matchType;}
      if (matchStatus) {params.match_status = matchStatus;}

      const response = await api.get("/technical-spec/match/records", {
        params,
      });
      setMatchRecords(response.data.items || []);
    } catch (error) {
      console.error("加载匹配记录失败:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleCheck = async () => {
    if (!projectId) {
      alert("请先选择项目");
      return;
    }

    setChecking(true);
    try {
      await api.post("/technical-spec/match/check", {
        project_id: parseInt(projectId),
        match_type: matchType || undefined,
        match_target_id: undefined,
      });
      alert("匹配检查完成");
      loadMatchRecords();
    } catch (error) {
      console.error("执行匹配检查失败:", error);
      alert("检查失败: " + (error.response?.data?.detail || error.message));
    } finally {
      setChecking(false);
    }
  };

  const getStatusBadge = (status) => {
    const configs = {
      MATCHED: { label: "匹配", className: "bg-green-100 text-green-800" },
      MISMATCHED: { label: "不匹配", className: "bg-red-100 text-red-800" },
      UNKNOWN: { label: "未知", className: "bg-gray-100 text-gray-800" },
    };
    const config = configs[status] || {
      label: status,
      className: "bg-gray-100 text-gray-800",
    };
    return <Badge className={config.className}>{config.label}</Badge>;
  };

  const getMatchTypeLabel = (type) => {
    const labels = {
      BOM: "BOM",
      PURCHASE_ORDER: "采购订单",
    };
    return labels[type] || type;
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="规格匹配检查"
        description="查看技术规格要求与采购订单/BOM的匹配结果"
      />

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>匹配记录</CardTitle>
            <div className="flex items-center gap-2">
              <Input
                type="number"
                placeholder="项目ID"
                value={projectId}
                onChange={(e) => setProjectId(e.target.value)}
                className="w-32"
              />
              <Select value={matchType} onValueChange={setMatchType}>
                <SelectTrigger className="w-40">
                  <SelectValue placeholder="匹配类型" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部</SelectItem>
                  <SelectItem value="BOM">BOM</SelectItem>
                  <SelectItem value="PURCHASE_ORDER">采购订单</SelectItem>
                </SelectContent>
              </Select>
              <Select value={matchStatus} onValueChange={setMatchStatus}>
                <SelectTrigger className="w-40">
                  <SelectValue placeholder="匹配状态" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部</SelectItem>
                  <SelectItem value="MATCHED">匹配</SelectItem>
                  <SelectItem value="MISMATCHED">不匹配</SelectItem>
                  <SelectItem value="UNKNOWN">未知</SelectItem>
                </SelectContent>
              </Select>
              <Button onClick={handleCheck} disabled={checking || !projectId}>
                <RefreshCw
                  className={`w-4 h-4 mr-2 ${checking ? "animate-spin" : ""}`}
                />
                执行检查
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8">加载中...</div>
          ) : matchRecords.length === 0 ? (
            <div className="text-center py-8 text-gray-500">暂无匹配记录</div>
          ) : (
            <div className="space-y-4">
              {matchRecords.map((record) => (
                <div
                  key={record.id}
                  className="border rounded-lg p-4 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <h3 className="font-semibold">
                          {record.spec_requirement?.material_name || "未知物料"}
                        </h3>
                        {getStatusBadge(record.match_status)}
                        <Badge variant="outline">
                          {getMatchTypeLabel(record.match_type)}
                        </Badge>
                        {record.match_score !== null && (
                          <Badge variant="outline">
                            匹配度: {parseFloat(record.match_score).toFixed(1)}%
                          </Badge>
                        )}
                      </div>
                      {record.spec_requirement && (
                        <div className="text-sm text-gray-600 space-y-1">
                          <p>
                            <span className="font-medium">要求规格:</span>{" "}
                            {record.spec_requirement.specification}
                          </p>
                          {record.differences &&
                            Object.keys(record.differences).length > 0 && (
                              <div className="mt-2 p-2 bg-red-50 rounded border border-red-200">
                                <p className="font-medium text-red-800 mb-1">
                                  差异详情:
                                </p>
                                <pre className="text-xs text-red-700">
                                  {JSON.stringify(record.differences, null, 2)}
                                </pre>
                              </div>
                            )}
                        </div>
                      )}
                    </div>
                    {record.alert_id && (
                      <AlertTriangle className="w-5 h-5 text-orange-500" />
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
