import {
  Building2,
  AlertTriangle,
  MoreHorizontal,
  Edit,
  Trash2,
  Target,
  MessageSquare,
} from "lucide-react"
import {
  Card,
  CardContent,
  Button,
  Badge,
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from "../../components/ui"
import { cn } from "../../lib/utils"
import { gradeColors, statusConfig } from "./constants"

export function CustomerTable({ customers, onCustomerClick }) {
  return (
    <Card>
      <CardContent className="p-0">
        <table className="w-full">
          <thead>
            <tr className="border-b border-white/5">
              <th className="text-left p-4 text-sm font-medium text-slate-400">
                客户名称
              </th>
              <th className="text-left p-4 text-sm font-medium text-slate-400">
                等级
              </th>
              <th className="text-left p-4 text-sm font-medium text-slate-400">
                状态
              </th>
              <th className="text-left p-4 text-sm font-medium text-slate-400">
                行业
              </th>
              <th className="text-left p-4 text-sm font-medium text-slate-400">
                联系人
              </th>
              <th className="text-right p-4 text-sm font-medium text-slate-400">
                累计金额
              </th>
              <th className="text-right p-4 text-sm font-medium text-slate-400">
                待回款
              </th>
              <th className="text-center p-4 text-sm font-medium text-slate-400">
                操作
              </th>
            </tr>
          </thead>
          <tbody>
            {(customers || []).map((customer) => {
              const statusConf =
                statusConfig[customer.status] || statusConfig.active;
              return (
                <tr
                  key={customer.id}
                  onClick={() => onCustomerClick(customer)}
                  className="border-b border-white/5 hover:bg-surface-100 cursor-pointer transition-colors"
                >
                  <td className="p-4">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center">
                        <Building2 className="w-4 h-4 text-primary" />
                      </div>
                      <div>
                        <div className="font-medium text-white">
                          {customer.shortName}
                        </div>
                        <div className="text-xs text-slate-500">
                          {customer.location}
                        </div>
                      </div>
                      {customer.isWarning && (
                        <AlertTriangle className="w-4 h-4 text-amber-500" />
                      )}
                    </div>
                  </td>
                  <td className="p-4">
                    <Badge
                      variant="outline"
                      className={gradeColors[customer.grade] || gradeColors.B}
                    >
                      {customer.grade}级
                    </Badge>
                  </td>
                  <td className="p-4">
                    <div className="flex items-center gap-2">
                      <div
                        className={cn(
                          "w-2 h-2 rounded-full",
                          statusConf.color,
                        )}
                      />
                      <span
                        className={cn("text-sm", statusConf.textColor)}
                      >
                        {statusConf.label}
                      </span>
                    </div>
                  </td>
                  <td className="p-4 text-sm text-slate-400">
                    {customer.industry}
                  </td>
                  <td className="p-4">
                    <div className="text-sm text-white">
                      {customer.contactPerson}
                    </div>
                    <div className="text-xs text-slate-500">
                      {customer.phone}
                    </div>
                  </td>
                  <td className="p-4 text-right">
                    <span className="text-sm font-medium text-white">
                      ¥{(customer.totalAmount / 10000).toFixed(0)}万
                    </span>
                  </td>
                  <td className="p-4 text-right">
                    <span
                      className={cn(
                        "text-sm font-medium",
                        customer.pendingAmount > 0
                          ? "text-amber-400"
                          : "text-slate-500",
                      )}
                    >
                      ¥{(customer.pendingAmount / 10000).toFixed(0)}万
                    </span>
                  </td>
                  <td className="p-4">
                    <div className="flex justify-center">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8"
                          >
                            <MoreHorizontal className="w-4 h-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem>
                            <Target className="w-4 h-4 mr-2" />
                            新建商机
                          </DropdownMenuItem>
                          <DropdownMenuItem>
                            <MessageSquare className="w-4 h-4 mr-2" />
                            添加跟进
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem>
                            <Edit className="w-4 h-4 mr-2" />
                            编辑
                          </DropdownMenuItem>
                          <DropdownMenuItem className="text-red-400">
                            <Trash2 className="w-4 h-4 mr-2" />
                            删除
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </CardContent>
    </Card>
  );
}
