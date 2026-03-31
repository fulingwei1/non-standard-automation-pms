import { useNavigate, useParams } from "react-router-dom";
import { formatDate } from "../../lib/utils";
import { Card, CardContent, Button } from "../../components/ui";
import { CheckCircle, Clock, Flag } from "lucide-react";

export default function MilestonesTab({ milestones }) {
  const { id } = useParams();
  const navigate = useNavigate();

  return (
    <div className="space-y-6">
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">项目里程碑</h3>
            <Button onClick={() => navigate(`/projects/${id}/milestones`)}>
              <Flag className="mr-2 h-4 w-4" />
              里程碑管理
            </Button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {(milestones || []).map((milestone) => (
              <div key={milestone.id} className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-medium">{milestone.name || milestone.milestone_name}</h4>
                  {milestone.status === "COMPLETED" || milestone.status === "completed" ? (
                    <CheckCircle className="h-5 w-5 text-green-500" />
                  ) : (
                    <Clock className="h-5 w-5 text-gray-400" />
                  )}
                </div>
                <p className="text-sm text-gray-600 mb-2">{milestone.description}</p>
                <p className="text-sm font-medium">
                  {formatDate(milestone.target_date || milestone.planned_date)}
                </p>
              </div>
            ))}
            {milestones.length === 0 && (
              <p className="text-center text-gray-500 py-4 col-span-3">暂无里程碑</p>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
