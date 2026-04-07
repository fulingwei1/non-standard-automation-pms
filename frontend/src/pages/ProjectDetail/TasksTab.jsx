import { useNavigate, useParams } from "react-router-dom";

export default function TasksTab() {
  const { id } = useParams();
  const navigate = useNavigate();

  return (
    <div className="space-y-6">
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">项目任务</h3>
            <Button onClick={() => navigate(`/projects/${id}/tasks`)}>
              <ListTodo className="mr-2 h-4 w-4" />
              任务管理
            </Button>
          </div>
          <p className="text-muted-foreground text-center py-8">
            点击"任务管理"查看完整任务列表
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
