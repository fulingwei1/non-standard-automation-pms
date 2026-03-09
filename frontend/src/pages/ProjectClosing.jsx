/**
 * 项目收尾 - 整合结项管理、项目复盘、经验教训
 *
 * Tab 1: 结项管理 - 结项申请、审批流程、状态跟踪
 * Tab 2: 项目复盘 - 复盘报告（事后/中期/季度）
 * Tab 3: 经验教训 - 知识库（按分类浏览、添加经验）
 */
import { useState, useEffect, lazy, Suspense } from "react";
import { useSearchParams } from "react-router-dom";
import { motion } from "framer-motion";
import {
  FileCheck,
  ClipboardList,
  Lightbulb,
  Loader2
} from "lucide-react";
import { PageHeader } from "../components/layout/PageHeader";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { staggerContainer } from "../lib/animations";

// 懒加载各子模块内容组件
const ClosureContent = lazy(() => import("./ProjectClosureManagement"));
const ReviewContent = lazy(() => import("./ProjectReviewList"));
const LessonsContent = lazy(() => import("./LessonsLearned"));

// Tab 配置
const TABS = [
  {
    id: "closure",
    label: "结项管理",
    icon: FileCheck,
    description: "项目结项申请、审批流程"
  },
  {
    id: "review",
    label: "项目复盘",
    icon: ClipboardList,
    description: "复盘报告与分析"
  },
  {
    id: "lessons",
    label: "经验教训",
    icon: Lightbulb,
    description: "知识沉淀与复用"
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

export default function ProjectClosing() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [activeTab, setActiveTab] = useState(() => {
    // 从 URL 参数读取初始 tab
    return searchParams.get("tab") || "closure";
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
        title="项目收尾"
        description={currentTabConfig?.description || "项目结项、复盘与经验沉淀"}
      />

      <Tabs value={activeTab} onValueChange={handleTabChange} className="space-y-6">
        <TabsList className="grid w-full grid-cols-3 lg:w-[500px]">
          {TABS.map((tab) => {
            const Icon = tab.icon;
            return (
              <TabsTrigger
                key={tab.id}
                value={tab.id}
                className="flex items-center gap-2"
              >
                <Icon className="h-4 w-4" />
                <span className="hidden sm:inline">{tab.label}</span>
              </TabsTrigger>
            );
          })}
        </TabsList>

        {/* 结项管理 */}
        <TabsContent value="closure" className="mt-6">
          <Suspense fallback={<LoadingFallback />}>
            <ClosureContent />
          </Suspense>
        </TabsContent>

        {/* 项目复盘 */}
        <TabsContent value="review" className="mt-6">
          <Suspense fallback={<LoadingFallback />}>
            <ReviewContent />
          </Suspense>
        </TabsContent>

        {/* 经验教训 */}
        <TabsContent value="lessons" className="mt-6">
          <Suspense fallback={<LoadingFallback />}>
            <LessonsContent />
          </Suspense>
        </TabsContent>
      </Tabs>
    </motion.div>
  );
}
