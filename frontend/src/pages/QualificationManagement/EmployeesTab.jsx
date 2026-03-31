/**
 * EmployeesTab - 员工认证管理标签页
 */
import { useNavigate } from "react-router-dom";
import { Eye, TrendingUp } from "lucide-react";
import { Button } from "../../components/ui/button";
import { Badge } from "../../components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../../components/ui/table";
import { formatDate } from "../../lib/utils";
import { getLevelBadgeColor, getStatusInfo } from "./constants";

export function EmployeesTab({
  qualifications,
  qualificationFilter,
  setQualificationFilter,
}) {
  const navigate = useNavigate();

  const getStatusBadge = (status) => {
    const statusInfo = getStatusInfo(status);
    return <Badge className={statusInfo.color}>{statusInfo.label}</Badge>;
  };

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <Select
          value={qualificationFilter.position_type}
          onValueChange={(value) =>
          setQualificationFilter({
            ...qualificationFilter,
            position_type: value
          })
          }>

          <SelectTrigger className="w-[200px]">
            <SelectValue placeholder="筛选岗位类型" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">全部</SelectItem>
            <SelectItem value="ENGINEER">工程师</SelectItem>
            <SelectItem value="SALES">销售</SelectItem>
            <SelectItem value="CUSTOMER_SERVICE">客服</SelectItem>
            <SelectItem value="WORKER">生产工人</SelectItem>
          </SelectContent>
        </Select>
        <Select
          value={qualificationFilter.status}
          onValueChange={(value) =>
          setQualificationFilter({
            ...qualificationFilter,
            status: value
          })
          }>

          <SelectTrigger className="w-[150px]">
            <SelectValue placeholder="状态" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">全部</SelectItem>
            <SelectItem value="PENDING">待认证</SelectItem>
            <SelectItem value="APPROVED">已认证</SelectItem>
            <SelectItem value="EXPIRED">已过期</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>员工</TableHead>
            <TableHead>岗位类型</TableHead>
            <TableHead>当前等级</TableHead>
            <TableHead>认证日期</TableHead>
            <TableHead>状态</TableHead>
            <TableHead>操作</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {(qualifications || []).map((qual) =>
          <TableRow key={qual.id}>
              <TableCell className="font-medium">
                员工 #{qual.employee_id}
              </TableCell>
              <TableCell>{qual.position_type}</TableCell>
              <TableCell>
                <Badge
                className={getLevelBadgeColor(qual.level?.level_code)}>

                  {qual.level?.level_name || qual.current_level_id}
                </Badge>
              </TableCell>
              <TableCell>
                {qual.certified_date ?
              formatDate(qual.certified_date) :
              "-"}
              </TableCell>
              <TableCell>{getStatusBadge(qual.status)}</TableCell>
              <TableCell>
                <div className="flex gap-2">
                  <Button
                  variant="ghost"
                  size="sm"
                  onClick={() =>
                  navigate(
                    `/qualifications/employees/${qual.employee_id}/view`
                  )
                  }
                  title="查看详情">

                    <Eye className="h-4 w-4" />
                  </Button>
                  <Button
                  variant="ghost"
                  size="sm"
                  onClick={() =>
                  navigate(
                    `/qualifications/employees/${qual.employee_id}/promote`
                  )
                  }
                  title="晋升评估">

                    <TrendingUp className="h-4 w-4" />
                  </Button>
                </div>
              </TableCell>
          </TableRow>
          )}
        </TableBody>
      </Table>
    </div>
  );
}
