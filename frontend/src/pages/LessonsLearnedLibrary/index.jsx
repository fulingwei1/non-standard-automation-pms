import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { PageHeader } from "../../components/layout/PageHeader";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "../../components/ui";
import { useLessonsLearnedLibrary } from "./hooks";
import { LessonFilters, LessonList, LessonStatistics } from "./components";

const staggerContainer = {
    hidden: { opacity: 0 },
    visible: {
        opacity: 1,
        transition: { staggerChildren: 0.05, delayChildren: 0.1 }
    }
};

export default function LessonsLearnedLibrary() {
    const navigate = useNavigate();
    const {
        loading,
        lessons,
        total,
        page, setPage,
        pageSize,
        keyword, setKeyword,
        lessonType, setLessonType,
        category, setCategory,
        status, setStatus,
        priority, setPriority,
        statistics,
        categories,
        activeTab, setActiveTab
    } = useLessonsLearnedLibrary();

    const handleViewReview = (reviewId) => {
        navigate(`/projects/reviews/${reviewId}`);
    };

    return (
        <motion.div initial="hidden" animate="visible" variants={staggerContainer}>
            <PageHeader
                title="经验教训库"
                description="跨项目搜索和管理经验教训，沉淀项目知识"
            />

            <Tabs
                value={activeTab || "unknown"}
                onValueChange={setActiveTab}
                className="space-y-6"
            >
                <TabsList className="grid w-full grid-cols-2">
                    <TabsTrigger value="list">经验教训列表</TabsTrigger>
                    <TabsTrigger value="statistics">统计分析</TabsTrigger>
                </TabsList>

                <TabsContent value="list" className="space-y-6">
                    <LessonFilters
                        keyword={keyword} setKeyword={setKeyword}
                        lessonType={lessonType} setLessonType={setLessonType}
                        category={category} setCategory={setCategory}
                        status={status} setStatus={setStatus}
                        priority={priority} setPriority={setPriority}
                        categories={categories}
                    />
                    <LessonList
                        loading={loading}
                        lessons={lessons}
                        total={total}
                        page={page}
                        pageSize={pageSize}
                        setPage={setPage}
                        onViewReview={handleViewReview}
                    />
                </TabsContent>

                <TabsContent value="statistics" className="space-y-6">
                    <LessonStatistics statistics={statistics} />
                </TabsContent>
            </Tabs>
        </motion.div>
    );
}
