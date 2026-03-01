/**
 * 工程师调度 - 项目选择入口
 * 选择项目后跳转到 /projects/:id/engineer-recommendation
 */

import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Users, ChevronRight, Loader2 } from "lucide-react";
import { PageHeader } from "../components/layout";
import { Card, CardContent, Button } from "../components/ui";
import { projectApi } from "../services/api";

export default function EngineerRecommendationEntry() {
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
        title="工程师调度"
        description="选择项目后进入工程师负载看板与智能推荐"
        icon={<Users className="w-6 h-6 text-cyan-500" />}
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
                    onClick={() => navigate(`/projects/${p.id}/engineer-recommendation`)}
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
