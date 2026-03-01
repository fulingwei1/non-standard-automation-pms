/**
 * AI 智能排计划 - 项目选择入口
 * 选择项目后跳转到 /projects/:id/schedule-generation
 */

import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Calendar, ChevronRight, Loader2 } from "lucide-react";
import { PageHeader } from "../components/layout";
import { Card, CardContent, Button } from "../components/ui";
import { projectApi } from "../services/api";

export default function ScheduleGenerationEntry() {
  const navigate = useNavigate();
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    projectApi.list({ page_size: 100 }).then((res) => {
      if (cancelled) return;
      const list = res?.data?.items ?? res?.items ?? res?.data ?? res ?? [];
      setProjects(Array.isArray(list) ? list : []);
    }).catch(() => setProjects([])).finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);

  return (
    <div className="space-y-6">
      <PageHeader
        title="AI 智能排计划"
        description="选择项目后进入计划生成（正常/高强度两种模式）"
        icon={<Calendar className="w-6 h-6 text-cyan-500" />}
      />
      <Card>
        <CardContent className="pt-6">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
            </div>
          ) : projects.length === 0 ? (
            <p className="text-muted-foreground text-center py-8">暂无项目，请先创建项目</p>
          ) : (
            <ul className="divide-y">
              {projects.map((p) => (
                <li key={p.id}>
                  <Button
                    variant="ghost"
                    className="w-full justify-between h-auto py-4"
                    onClick={() => navigate(`/projects/${p.id}/schedule-generation`)}
                  >
                    <span className="font-medium">{p.name ?? p.code ?? `项目 ${p.id}`}</span>
                    <ChevronRight className="w-4 h-4" />
                  </Button>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
