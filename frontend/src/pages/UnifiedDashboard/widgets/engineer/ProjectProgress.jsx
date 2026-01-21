/**
 * 项目进度组件 (Project Progress)
 */
import { Card, CardContent, CardHeader, CardTitle } from '../../../../components/ui/card';
import { Progress } from '../../../../components/ui/progress';

const defaultProjects = [
  { id: 'PJ250101-001', name: '智能检测设备', progress: 75, status: 'on-track' },
  { id: 'PJ250101-002', name: '自动组装线', progress: 45, status: 'delayed' },
  { id: 'PJ250101-003', name: 'EOL测试设备', progress: 90, status: 'on-track' },
];

export default function ProjectProgress({ view, filter, data }) {
  const projects = data?.projects || defaultProjects;

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">项目进度</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {projects.map(project => (
            <div key={project.id} className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="font-medium">{project.name}</span>
                <span className="text-muted-foreground">{project.progress}%</span>
              </div>
              <Progress value={project.progress} className="h-2" />
              <p className="text-xs text-muted-foreground">{project.id}</p>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
