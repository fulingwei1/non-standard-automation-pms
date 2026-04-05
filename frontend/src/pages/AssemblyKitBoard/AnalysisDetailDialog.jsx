/**
 * Analysis Detail Dialog - 齐套分析详情对话框
 */
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "../../components/ui/dialog";
import { Badge } from "../../components/ui/badge";
import { Progress } from "../../components/ui/progress";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../../components/ui/table";
import { cn } from "../../lib/utils";
import { alertLevelConfig, getKitRateColor } from "./constants";

export default function AnalysisDetailDialog({
  open,
  onOpenChange,
  analysisDetail,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>齐套分析详情</DialogTitle>
          <DialogDescription>
            {analysisDetail?.readiness_no} - {analysisDetail?.project_name}
          </DialogDescription>
        </DialogHeader>
        {analysisDetail &&
        <div className="space-y-6">
            {/* Summary */}
            <div className="grid grid-cols-4 gap-4">
              <div className="p-3 bg-slate-50 rounded-lg">
                <div className="text-sm text-slate-500">整体齐套率</div>
                <div
                className={cn(
                  "text-xl font-bold",
                  getKitRateColor(analysisDetail.overall_kit_rate)
                )}>

                  {analysisDetail.overall_kit_rate}%
                </div>
              </div>
              <div className="p-3 bg-slate-50 rounded-lg">
                <div className="text-sm text-slate-500">阻塞齐套率</div>
                <div
                className={cn(
                  "text-xl font-bold",
                  getKitRateColor(analysisDetail.blocking_kit_rate)
                )}>

                  {analysisDetail.blocking_kit_rate}%
                </div>
              </div>
              <div className="p-3 bg-slate-50 rounded-lg">
                <div className="text-sm text-slate-500">开工状态</div>
                <div
                className={cn(
                  "text-xl font-bold",
                  analysisDetail.can_start ?
                  "text-emerald-600" :
                  "text-red-600"
                )}>

                  {analysisDetail.can_start ? "可开工" : "阻塞"}
                </div>
              </div>
              <div className="p-3 bg-slate-50 rounded-lg">
                <div className="text-sm text-slate-500">首个阻塞阶段</div>
                <div className="text-xl font-bold text-slate-700">
                  {analysisDetail.first_blocked_stage || "-"}
                </div>
              </div>
            </div>

            {/* Stage Progress */}
            <div>
              <h4 className="font-medium mb-3">各阶段齐套率</h4>
              <div className="space-y-3">
                {analysisDetail.stage_kit_rates?.map((stage) =>
              <div
                key={stage.stage_code}
                className="flex items-center gap-4">

                    <div className="w-24 text-sm font-medium">
                      {stage.stage_name}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <Progress
                      value={stage.kit_rate}
                      className="h-2 flex-1" />

                        <span
                      className={cn(
                        "text-sm font-medium w-12",
                        getKitRateColor(stage.kit_rate)
                      )}>

                          {stage.kit_rate}%
                        </span>
                      </div>
                      <div className="text-xs text-slate-500">
                        阻塞: {stage.blocking_rate}% |
                        {stage.can_start ?
                    <span className="text-emerald-600 ml-1">
                            可开始
                    </span> :

                    <span className="text-red-600 ml-1">阻塞</span>
                    }
                      </div>
                    </div>
              </div>
              )}
              </div>
            </div>

            {/* Shortage Details */}
            {analysisDetail.shortage_details?.length > 0 &&
          <div>
                <h4 className="font-medium mb-3">
                  缺料明细 ({analysisDetail.shortage_details?.length} 项)
                </h4>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>物料编码</TableHead>
                      <TableHead>物料名称</TableHead>
                      <TableHead>装配阶段</TableHead>
                      <TableHead>需求</TableHead>
                      <TableHead>可用</TableHead>
                      <TableHead>缺料</TableHead>
                      <TableHead>阻塞性</TableHead>
                      <TableHead>预警</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {(analysisDetail.shortage_details || []).map((detail) =>
                <TableRow key={detail.id}>
                        <TableCell className="font-mono text-sm">
                          {detail.material_code}
                        </TableCell>
                        <TableCell>{detail.material_name}</TableCell>
                        <TableCell>
                          {detail.stage_name || detail.assembly_stage}
                        </TableCell>
                        <TableCell>{detail.required_qty}</TableCell>
                        <TableCell>{detail.available_qty}</TableCell>
                        <TableCell className="text-red-600 font-medium">
                          {detail.shortage_qty}
                        </TableCell>
                        <TableCell>
                          {detail.is_blocking ?
                    <Badge className="bg-red-500">阻塞</Badge> :

                    <Badge variant="outline">可后补</Badge>
                    }
                        </TableCell>
                        <TableCell>
                          <Badge
                      className={
                      alertLevelConfig[detail.alert_level]?.color ||
                      "bg-slate-500"
                      }>

                            {detail.alert_level}
                          </Badge>
                        </TableCell>
                </TableRow>
                )}
                  </TableBody>
                </Table>
          </div>
          }
        </div>
        }
      </DialogContent>
    </Dialog>
  );
}
