import { useNavigate } from "react-router-dom";
import {
  Card,
  CardContent,
  Button,
} from "../../components/ui";
import {
  FileText,
  Calculator,
  TrendingUp,
  BarChart3,
  Users,
} from "lucide-react";

export default function ReportsTab({ id }) {
  const navigate = useNavigate();

  return (
    <Card>
      <CardContent className="p-6">
        <h3 className="text-lg font-semibold text-white mb-4">
          研发费用报表
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Button
            variant="outline"
            className="h-auto p-4 flex flex-col items-start"
            onClick={() =>
              navigate(`/rd-projects/${id}/reports?type=auxiliary-ledger`)
            }
          >
            <FileText className="h-5 w-5 mb-2" />
            <span className="font-medium">研发费用辅助账</span>
            <span className="text-xs text-slate-500 mt-1">
              税务要求的辅助账格式
            </span>
          </Button>
          <Button
            variant="outline"
            className="h-auto p-4 flex flex-col items-start"
            onClick={() =>
              navigate(`/rd-projects/${id}/reports?type=deduction-detail`)
            }
          >
            <Calculator className="h-5 w-5 mb-2" />
            <span className="font-medium">加计扣除明细</span>
            <span className="text-xs text-slate-500 mt-1">
              按项目、按类型汇总
            </span>
          </Button>
          <Button
            variant="outline"
            className="h-auto p-4 flex flex-col items-start"
            onClick={() =>
              navigate(`/rd-projects/${id}/reports?type=high-tech`)
            }
          >
            <TrendingUp className="h-5 w-5 mb-2" />
            <span className="font-medium">高新企业费用表</span>
            <span className="text-xs text-slate-500 mt-1">
              按六大费用类型汇总
            </span>
          </Button>
          <Button
            variant="outline"
            className="h-auto p-4 flex flex-col items-start"
            onClick={() =>
              navigate(`/rd-projects/${id}/reports?type=intensity`)
            }
          >
            <BarChart3 className="h-5 w-5 mb-2" />
            <span className="font-medium">研发投入强度</span>
            <span className="text-xs text-slate-500 mt-1">
              研发费用/营业收入
            </span>
          </Button>
          <Button
            variant="outline"
            className="h-auto p-4 flex flex-col items-start"
            onClick={() =>
              navigate(`/rd-projects/${id}/reports?type=personnel`)
            }
          >
            <Users className="h-5 w-5 mb-2" />
            <span className="font-medium">研发人员统计</span>
            <span className="text-xs text-slate-500 mt-1">
              研发人员占比、工时分配
            </span>
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
