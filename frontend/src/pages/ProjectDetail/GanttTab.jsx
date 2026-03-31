import { useNavigate, useParams } from "react-router-dom";
import { Card, CardContent, Button } from "../../components/ui";
import StageGantt from "../../components/project/StageGantt";
import { GitBranch } from "lucide-react";

export default function GanttTab({ stages }) {
  const { id } = useParams();
  const navigate = useNavigate();

  return (
    <div className="space-y-6">
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">项目进度甘特图</h3>
            <Button onClick={() => navigate(`/projects/${id}/gantt`)}>
              <GitBranch className="mr-2 h-4 w-4" />
              完整甘特图
            </Button>
          </div>
          <StageGantt stages={stages} />
        </CardContent>
      </Card>
    </div>
  );
}
