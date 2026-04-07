/**
 * AI 项目工具 - 整合智能排计划和工程师调度
 *
 * Tab 1: AI智能排计划 - 选择项目后生成计划
 * Tab 2: 工程师调度 - 选择项目后推荐工程师
 */
import { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import {
  Calendar,
  Users
} from "lucide-react";


import { staggerContainer } from "../lib/animations";
import { projectApi } from "../services/api";

// Tab 配置
const TABS = [
  {
    id: "schedule",
    label: "智能排计划",
    icon: Calendar,
    description: "AI 自动生成项目计划（正常/高强度模式）",
    targetPath: (id) => `/projects/${id}/schedule-generation`
  },
  {
    id: "engineer",
    label: "工程师调度",
    icon: Users,
    description: "智能推荐工程师，查看负载看板",
    targetPath: (id) => `/projects/${id}/engineer-recommendation`
  }
];

// 项目卡片组件
function ProjectCard({ project, onSelect }) {
  const healthColors = {
    GREEN: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
    YELLOW: "bg-amber-500/20 text-amber-400 border-amber-500/30",
    RED: "bg-red-500/20 text-red-400 border-red-500/30"
  };

  return (
    <motion.div
      whileHover={{ scale: 1.01 }}
      whileTap={{ scale: 0.99 }}
      className="group"
    >
      <Button
        variant="ghost"
        className="w-full justify-between h-auto py-4 px-4 hover:bg-white/5"
        onClick={() => onSelect(project)}
      >
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
            <Sparkles className="w-5 h-5 text-primary" />
          </div>
          <div className="text-left">
            <div className="font-medium">{project.name || project.code || `项目 ${project.id}`}</div>
            <div className="text-xs text-muted-foreground">
              {project.customer_name || "未指定客户"}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {project.health && (
            <Badge className={healthColors[project.health] || "bg-slate-500/20"}>
              {project.health === "GREEN" ? "健康" : project.health === "YELLOW" ? "关注" : "风险"}
            </Badge>
          )}
          <ChevronRight className="w-4 h-4 text-muted-foreground group-hover:text-primary transition-colors" />
        </div>
      </Button>
    </motion.div>
  );
}

export default function AIProjectTools() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [activeTab, setActiveTab] = useState(() => searchParams.get("tab") || "schedule");
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");

  // 同步 tab 到 URL
  useEffect(() => {
    const currentTab = searchParams.get("tab");
    if (currentTab !== activeTab) {
      setSearchParams({ tab: activeTab }, { replace: true });
    }
  }, [activeTab, searchParams, setSearchParams]);

  // 加载项目列表
  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    projectApi
      .list({ page_size: 100 })
      .then((res) => {
        if (cancelled) return;
        const list = res?.data?.items ?? res?.items ?? res?.data ?? res ?? [];
        setProjects(Array.isArray(list) ? list : []);
      })
      .catch(() => setProjects([]))
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  // 项目筛选
  const filteredProjects = projects.filter((p) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      (p.name || "").toLowerCase().includes(query) ||
      (p.code || "").toLowerCase().includes(query) ||
      (p.customer_name || "").toLowerCase().includes(query)
    );
  });

  // 处理项目选择
  const handleSelectProject = (project) => {
    const tabConfig = TABS.find((t) => t.id === activeTab);
    if (tabConfig) {
      navigate(tabConfig.targetPath(project.id));
    }
  };

  const currentTabConfig = TABS.find((t) => t.id === activeTab);

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={staggerContainer}
      className="space-y-6 p-6"
    >
      <PageHeader
        title="AI 项目工具"
        description={currentTabConfig?.description || "智能排计划与工程师调度"}
        icon={<Sparkles className="w-6 h-6 text-primary" />}
      />

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-2 lg:w-[400px]">
          {TABS.map((tab) => {
            const Icon = tab.icon;
            return (
              <TabsTrigger
                key={tab.id}
                value={tab.id}
                className="flex items-center gap-2"
              >
                <Icon className="h-4 w-4" />
                <span>{tab.label}</span>
              </TabsTrigger>
            );
          })}
        </TabsList>

        {/* 搜索框 */}
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="搜索项目名称、编号或客户..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>

        {/* 项目列表 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              {currentTabConfig && <currentTabConfig.icon className="w-5 h-5" />}
              选择项目
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
              </div>
            ) : filteredProjects.length === 0 ? (
              <p className="text-muted-foreground text-center py-8">
                {searchQuery ? "未找到匹配的项目" : "暂无项目，请先创建项目"}
              </p>
            ) : (
              <div className="divide-y divide-white/5">
                {filteredProjects.map((project) => (
                  <ProjectCard
                    key={project.id}
                    project={project}
                    onSelect={handleSelectProject}
                  />
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </Tabs>
    </motion.div>
  );
}
