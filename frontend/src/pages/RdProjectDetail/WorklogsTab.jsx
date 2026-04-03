import { useNavigate } from "react-router-dom";
import {
  Card,
  CardContent,
  Button,
} from "../../components/ui";
import { FileText } from "lucide-react";

export default function WorklogsTab({ id }) {
  const navigate = useNavigate();

  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white">
            研发人员工作日志
          </h3>
          <Button onClick={() => navigate(`/rd-projects/${id}/worklogs`)}>
            查看全部
          </Button>
        </div>
        <div className="text-center py-12 text-slate-500">
          <FileText className="h-12 w-12 mx-auto mb-4 text-slate-600" />
          <p>工作日志管理</p>
          <Button
            variant="outline"
            className="mt-4"
            onClick={() => navigate(`/rd-projects/${id}/worklogs`)}
          >
            进入工作日志页面
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
