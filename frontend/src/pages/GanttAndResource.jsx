/**
 * 甘特与资源 - 整合任务甘特和资源甘特
 *
 * Tab 1: 任务甘特 - 依赖关系与关键路径
 * Tab 2: 资源甘特 - 人员负载时间线
 */
import { useState, useEffect, lazy } from "react";
import { useSearchParams } from "react-router-dom";
import {
  GitBranch,
  Users
} from "lucide-react";
import { staggerContainer } from "../lib/animations";

// 懒加载子模块
const TaskGantt = lazy(() => import("./GanttDependency"));
const ResourceGantt = lazy(() => import("./ResourceOverview"));

// Tab 配置
const TABS = [
  {
    id: "task",
    label: "任务甘特",
    icon: GitBranch,
    description: "任务时间线、依赖关系与关键路径分析"
  },
  {
    id: "resource",
    label: "资源甘特",
    icon: Users,
    description: "人员负载时间线与冲突分析"
  }
];

// 加载占位组件
function LoadingFallback() {
  return (
    <div className="flex items-center justify-center py-20">
      <Loader2 className="h-8 w-8 animate-spin text-primary" />
      <span className="ml-2 text-muted-foreground">加载中...</span>
    </div>
  );
}

export default function GanttAndResource() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [activeTab, setActiveTab] = useState(() => {
    return searchParams.get("tab") || "task";
  });

  // 同步 tab 状态到 URL
  useEffect(() => {
    const currentTab = searchParams.get("tab");
    if (currentTab !== activeTab) {
      setSearchParams({ tab: activeTab }, { replace: true });
    }
  }, [activeTab, searchParams, setSearchParams]);

  const handleTabChange = (value) => {
    setActiveTab(value);
  };

  const currentTabConfig = TABS.find(t => t.id === activeTab);

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={staggerContainer}
      className="space-y-6 p-6"
    >
      <PageHeader
        title="甘特与资源"
        description={currentTabConfig?.description || "项目计划与资源管理"}
      />

      <Tabs value={activeTab} onValueChange={handleTabChange} className="space-y-6">
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

        {/* 任务甘特 */}
        <TabsContent value="task" className="mt-6">
          <Suspense fallback={<LoadingFallback />}>
            <TaskGantt embedded />
          </Suspense>
        </TabsContent>

        {/* 资源甘特 */}
        <TabsContent value="resource" className="mt-6">
          <Suspense fallback={<LoadingFallback />}>
            <ResourceGantt embedded />
          </Suspense>
        </TabsContent>
      </Tabs>
    </motion.div>
  );
}
