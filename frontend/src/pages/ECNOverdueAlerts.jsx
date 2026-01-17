/**
 * ECN Overdue Alerts Page - ECN超时提醒页面
 * Features: 超时提醒列表、按类型分组、批量处理、跳转到ECN详情
 */
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  AlertTriangle,
  Clock,
  FileText,
  CheckCircle2,
  ExternalLink,
  RefreshCw,
  Filter } from
"lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription } from
"../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue } from
"../components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow } from
"../components/ui/table";
import { Checkbox } from "../components/ui/checkbox";
import { ecnApi } from "../services/api";
import { formatDate as _formatDate } from "../lib/utils";

const alertTypeConfigs = {
  EVALUATION_OVERDUE: {
    label: "评估超时",
    color: "bg-amber-500",
    icon: FileText
  },
  APPROVAL_OVERDUE: {
    label: "审批超时",
    color: "bg-red-500",
    icon: CheckCircle2
  },
  TASK_OVERDUE: {
    label: "任务超时",
    color: "bg-orange-500",
    icon: Clock
  }
};

export default function ECNOverdueAlerts() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [alerts, setAlerts] = useState([]);
  const [filteredAlerts, setFilteredAlerts] = useState([]);
  const [filterType, setFilterType] = useState("all");
  const [selectedAlerts, setSelectedAlerts] = useState(new Set());
  const [lastRefresh, setLastRefresh] = useState(new Date());

  useEffect(() => {
    fetchAlerts();
  }, []);

  useEffect(() => {
    filterAlerts();
  }, [alerts, filterType]);

  const fetchAlerts = async () => {
    try {
      setLoading(true);
      const res = await ecnApi.getOverdueAlerts();
      const alertsList = res.data || res || [];
      setAlerts(alertsList);
      setLastRefresh(new Date());
    } catch (error) {
      console.error("Failed to fetch overdue alerts:", error);
      alert(
        "获取超时提醒失败: " + (error.response?.data?.detail || error.message)
      );
    } finally {
      setLoading(false);
    }
  };

  const filterAlerts = () => {
    if (filterType === "all") {
      setFilteredAlerts(alerts);
    } else {
      setFilteredAlerts(alerts.filter((alert) => alert.type === filterType));
    }
  };

  const handleSelectAlert = (alertId) => {
    const newSelected = new Set(selectedAlerts);
    if (newSelected.has(alertId)) {
      newSelected.delete(alertId);
    } else {
      newSelected.add(alertId);
    }
    setSelectedAlerts(newSelected);
  };

  const _handleSelectAll = () => {
    if (selectedAlerts.size === filteredAlerts.length) {
      setSelectedAlerts(new Set());
    } else {
      setSelectedAlerts(
        new Set(
          filteredAlerts.map(
            (a) =>
            `${a.type}-${a.ecn_id}-${a.task_id || a.approval_level || a.dept || ""}`
          )
        )
      );
    }
  };

  const handleViewECN = (ecnId) => {
    navigate(`/ecns?ecnId=${ecnId}`);
  };

  const handleBatchProcess = async () => {
    if (selectedAlerts.size === 0) {
      alert("请先选择要处理的提醒");
      return;
    }

    if (
    !confirm(
      `确认发送提醒通知给相关人员？将处理 ${selectedAlerts.size} 个超时提醒。`
    ))
    {
      return;
    }

    try {
      // 根据选中的 alertId 找到对应的提醒数据
      const selectedAlertList = filteredAlerts.filter((alert) => {
        let alertId = "";
        if (alert.type === "EVALUATION_OVERDUE") {
          alertId = `${alert.type}-${alert.ecn_id}-${alert.dept || ""}`;
        } else if (alert.type === "APPROVAL_OVERDUE") {
          alertId = `${alert.type}-${alert.ecn_id}-${alert.approval_level || ""}`;
        } else if (alert.type === "TASK_OVERDUE") {
          alertId = `${alert.type}-${alert.ecn_id}-${alert.task_id || ""}`;
        }
        return selectedAlerts.has(alertId);
      });

      const res = await ecnApi.batchProcessOverdueAlerts(selectedAlertList);

      if (res.data) {
        const { success_count, fail_count } = res.data;
        if (fail_count === 0) {
          // 使用toast替代alert，如果toast可用
          if (window.toast) {
            window.toast.success(
              `批量处理成功！已发送提醒通知给 ${success_count} 个提醒的相关人员。`
            );
          } else {
            alert(
              `批量处理成功！已发送提醒通知给 ${success_count} 个提醒的相关人员。`
            );
          }
        } else {
          if (window.toast) {
            window.toast.warning(
              `批量处理完成：成功 ${success_count} 个，失败 ${fail_count} 个。`
            );
          } else {
            alert(
              `批量处理完成：成功 ${success_count} 个，失败 ${fail_count} 个。`
            );
          }
        }
      } else {
        if (window.toast) {
          window.toast.success("批量处理完成");
        } else {
          alert("批量处理完成");
        }
      }

      setSelectedAlerts(new Set());
      fetchAlerts();
    } catch (error) {
      console.error("批量处理失败:", error);
      const errorMsg =
      error.response?.data?.detail || error.message || "批量处理失败";
      if (window.toast) {
        window.toast.error("批量处理失败: " + errorMsg);
      } else {
        alert("批量处理失败: " + errorMsg);
      }
    }
  };

  const groupAlertsByType = (alerts) => {
    const groups = {
      EVALUATION_OVERDUE: [],
      APPROVAL_OVERDUE: [],
      TASK_OVERDUE: []
    };
    alerts.forEach((alert) => {
      if (groups[alert.type]) {
        groups[alert.type].push(alert);
      }
    });
    return groups;
  };

  const groupedAlerts = groupAlertsByType(filteredAlerts);
  const totalCount = filteredAlerts.length;
  const evaluationCount = groupedAlerts.EVALUATION_OVERDUE.length;
  const approvalCount = groupedAlerts.APPROVAL_OVERDUE.length;
  const taskCount = groupedAlerts.TASK_OVERDUE.length;

  return (
    <div className="space-y-6 p-6">
      <PageHeader
        title="ECN超时提醒"
        description="查看和处理ECN评估、审批、执行任务超时提醒" />


      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-400">总超时提醒</div>
                <div className="text-2xl font-bold">{totalCount}</div>
              </div>
              <AlertTriangle className="w-8 h-8 text-amber-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-400">评估超时</div>
                <div className="text-2xl font-bold">{evaluationCount}</div>
              </div>
              <FileText className="w-8 h-8 text-amber-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-400">审批超时</div>
                <div className="text-2xl font-bold">{approvalCount}</div>
              </div>
              <CheckCircle2 className="w-8 h-8 text-red-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-400">任务超时</div>
                <div className="text-2xl font-bold">{taskCount}</div>
              </div>
              <Clock className="w-8 h-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 操作栏 */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Select value={filterType} onValueChange={setFilterType}>
                <SelectTrigger className="w-40">
                  <SelectValue placeholder="筛选类型" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部类型</SelectItem>
                  <SelectItem value="EVALUATION_OVERDUE">评估超时</SelectItem>
                  <SelectItem value="APPROVAL_OVERDUE">审批超时</SelectItem>
                  <SelectItem value="TASK_OVERDUE">任务超时</SelectItem>
                </SelectContent>
              </Select>
              <div className="text-sm text-slate-400">
                最后更新: {lastRefresh.toLocaleTimeString()}
              </div>
            </div>
            <div className="flex items-center gap-2">
              {selectedAlerts.size > 0 &&
              <Button variant="outline" onClick={handleBatchProcess}>
                  批量处理 ({selectedAlerts.size})
                </Button>
              }
              <Button onClick={fetchAlerts} variant="outline">
                <RefreshCw className="w-4 h-4 mr-2" />
                刷新
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 超时提醒列表 */}
      {loading ?
      <Card>
          <CardContent className="pt-6">
            <div className="text-center py-8 text-slate-400">加载中...</div>
          </CardContent>
        </Card> :
      filteredAlerts.length === 0 ?
      <Card>
          <CardContent className="pt-6">
            <div className="text-center py-8 text-slate-400">
              {filterType === "all" ?
            "暂无超时提醒" :
            `暂无${alertTypeConfigs[filterType]?.label || ""}提醒`}
            </div>
          </CardContent>
        </Card> :

      <div className="space-y-4">
          {/* 评估超时 */}
          {groupedAlerts.EVALUATION_OVERDUE.length > 0 &&
        <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="w-5 h-5 text-amber-500" />
                  评估超时 ({groupedAlerts.EVALUATION_OVERDUE.length})
                </CardTitle>
                <CardDescription>评估任务超过3天未完成</CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-12">
                        <Checkbox
                      checked={
                      selectedAlerts.size ===
                      groupedAlerts.EVALUATION_OVERDUE.length &&
                      groupedAlerts.EVALUATION_OVERDUE.length > 0 &&
                      groupedAlerts.EVALUATION_OVERDUE.every((a) =>
                      selectedAlerts.has(
                        `${a.type}-${a.ecn_id}-${a.dept || ""}`
                      )
                      )
                      }
                      onCheckedChange={(checked) => {
                        if (checked) {
                          const newSelected = new Set(selectedAlerts);
                          groupedAlerts.EVALUATION_OVERDUE.forEach((a) => {
                            newSelected.add(
                              `${a.type}-${a.ecn_id}-${a.dept || ""}`
                            );
                          });
                          setSelectedAlerts(newSelected);
                        } else {
                          const newSelected = new Set(selectedAlerts);
                          groupedAlerts.EVALUATION_OVERDUE.forEach((a) => {
                            newSelected.delete(
                              `${a.type}-${a.ecn_id}-${a.dept || ""}`
                            );
                          });
                          setSelectedAlerts(newSelected);
                        }
                      }} />

                      </TableHead>
                      <TableHead>ECN编号</TableHead>
                      <TableHead>ECN标题</TableHead>
                      <TableHead>评估部门</TableHead>
                      <TableHead>超时天数</TableHead>
                      <TableHead>操作</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {groupedAlerts.EVALUATION_OVERDUE.map((alert, index) => {
                  const alertId = `${alert.type}-${alert.ecn_id}-${alert.dept || ""}`;
                  return (
                    <TableRow key={index}>
                          <TableCell>
                            <Checkbox
                          checked={selectedAlerts.has(alertId)}
                          onCheckedChange={(checked) => {
                            if (checked) {
                              handleSelectAlert(alertId);
                            } else {
                              handleSelectAlert(alertId);
                            }
                          }} />

                          </TableCell>
                          <TableCell className="font-mono text-sm">
                            {alert.ecn_no}
                          </TableCell>
                          <TableCell>{alert.ecn_title}</TableCell>
                          <TableCell>
                            <Badge className="bg-amber-500">{alert.dept}</Badge>
                          </TableCell>
                          <TableCell>
                            <Badge className="bg-red-500">
                              {alert.overdue_days} 天
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleViewECN(alert.ecn_id)}>

                              <ExternalLink className="w-4 h-4 mr-2" />
                              查看ECN
                            </Button>
                          </TableCell>
                        </TableRow>);

                })}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
        }

          {/* 审批超时 */}
          {groupedAlerts.APPROVAL_OVERDUE.length > 0 &&
        <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <CheckCircle2 className="w-5 h-5 text-red-500" />
                  审批超时 ({groupedAlerts.APPROVAL_OVERDUE.length})
                </CardTitle>
                <CardDescription>审批任务超过截止日期未完成</CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-12">
                        <Checkbox
                      checked={
                      selectedAlerts.size ===
                      groupedAlerts.APPROVAL_OVERDUE.length &&
                      groupedAlerts.APPROVAL_OVERDUE.length > 0 &&
                      groupedAlerts.APPROVAL_OVERDUE.every((a) =>
                      selectedAlerts.has(
                        `${a.type}-${a.ecn_id}-${a.approval_level || ""}`
                      )
                      )
                      }
                      onCheckedChange={(checked) => {
                        if (checked) {
                          const newSelected = new Set(selectedAlerts);
                          groupedAlerts.APPROVAL_OVERDUE.forEach((a) => {
                            newSelected.add(
                              `${a.type}-${a.ecn_id}-${a.approval_level || ""}`
                            );
                          });
                          setSelectedAlerts(newSelected);
                        } else {
                          const newSelected = new Set(selectedAlerts);
                          groupedAlerts.APPROVAL_OVERDUE.forEach((a) => {
                            newSelected.delete(
                              `${a.type}-${a.ecn_id}-${a.approval_level || ""}`
                            );
                          });
                          setSelectedAlerts(newSelected);
                        }
                      }} />

                      </TableHead>
                      <TableHead>ECN编号</TableHead>
                      <TableHead>ECN标题</TableHead>
                      <TableHead>审批层级</TableHead>
                      <TableHead>审批角色</TableHead>
                      <TableHead>超时天数</TableHead>
                      <TableHead>操作</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {groupedAlerts.APPROVAL_OVERDUE.map((alert, index) => {
                  const alertId = `${alert.type}-${alert.ecn_id}-${alert.approval_level || ""}`;
                  return (
                    <TableRow key={index}>
                          <TableCell>
                            <Checkbox
                          checked={selectedAlerts.has(alertId)}
                          onCheckedChange={(checked) => {
                            if (checked) {
                              handleSelectAlert(alertId);
                            } else {
                              handleSelectAlert(alertId);
                            }
                          }} />

                          </TableCell>
                          <TableCell className="font-mono text-sm">
                            {alert.ecn_no}
                          </TableCell>
                          <TableCell>{alert.ecn_title}</TableCell>
                          <TableCell>第{alert.approval_level}级</TableCell>
                          <TableCell>
                            <Badge className="bg-blue-500">
                              {alert.approval_role}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <Badge className="bg-red-500">
                              {alert.overdue_days} 天
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleViewECN(alert.ecn_id)}>

                              <ExternalLink className="w-4 h-4 mr-2" />
                              查看ECN
                            </Button>
                          </TableCell>
                        </TableRow>);

                })}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
        }

          {/* 任务超时 */}
          {groupedAlerts.TASK_OVERDUE.length > 0 &&
        <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Clock className="w-5 h-5 text-orange-500" />
                  任务超时 ({groupedAlerts.TASK_OVERDUE.length})
                </CardTitle>
                <CardDescription>
                  执行任务超过计划完成日期未完成
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-12">
                        <Checkbox
                      checked={
                      selectedAlerts.size ===
                      groupedAlerts.TASK_OVERDUE.length &&
                      groupedAlerts.TASK_OVERDUE.length > 0 &&
                      groupedAlerts.TASK_OVERDUE.every((a) =>
                      selectedAlerts.has(
                        `${a.type}-${a.ecn_id}-${a.task_id || ""}`
                      )
                      )
                      }
                      onCheckedChange={(checked) => {
                        if (checked) {
                          const newSelected = new Set(selectedAlerts);
                          groupedAlerts.TASK_OVERDUE.forEach((a) => {
                            newSelected.add(
                              `${a.type}-${a.ecn_id}-${a.task_id || ""}`
                            );
                          });
                          setSelectedAlerts(newSelected);
                        } else {
                          const newSelected = new Set(selectedAlerts);
                          groupedAlerts.TASK_OVERDUE.forEach((a) => {
                            newSelected.delete(
                              `${a.type}-${a.ecn_id}-${a.task_id || ""}`
                            );
                          });
                          setSelectedAlerts(newSelected);
                        }
                      }} />

                      </TableHead>
                      <TableHead>ECN编号</TableHead>
                      <TableHead>ECN标题</TableHead>
                      <TableHead>任务名称</TableHead>
                      <TableHead>超时天数</TableHead>
                      <TableHead>操作</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {groupedAlerts.TASK_OVERDUE.map((alert, index) => {
                  const alertId = `${alert.type}-${alert.ecn_id}-${alert.task_id || ""}`;
                  return (
                    <TableRow key={index}>
                          <TableCell>
                            <Checkbox
                          checked={selectedAlerts.has(alertId)}
                          onCheckedChange={(checked) => {
                            if (checked) {
                              handleSelectAlert(alertId);
                            } else {
                              handleSelectAlert(alertId);
                            }
                          }} />

                          </TableCell>
                          <TableCell className="font-mono text-sm">
                            {alert.ecn_no}
                          </TableCell>
                          <TableCell>{alert.ecn_title}</TableCell>
                          <TableCell>{alert.task_name}</TableCell>
                          <TableCell>
                            <Badge className="bg-red-500">
                              {alert.overdue_days} 天
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleViewECN(alert.ecn_id)}>

                              <ExternalLink className="w-4 h-4 mr-2" />
                              查看ECN
                            </Button>
                          </TableCell>
                        </TableRow>);

                })}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
        }
        </div>
      }
    </div>);

}