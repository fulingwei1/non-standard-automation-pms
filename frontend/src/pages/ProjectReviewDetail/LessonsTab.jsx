/**
 * Lessons tab content for ProjectReviewDetail
 */
import { cn } from "../../lib/utils";




import { getLessonType } from "../../components/project-review";
import { staggerChild } from "./constants";

export default function LessonsTab({
  lessons,
  review,
  setLessonDialog,
  setLessonForm,
  setDeleteLessonDialog,
}) {
  return (
    <>
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium text-white">经验教训</h3>
        <Button
          onClick={() =>
          setLessonDialog({ open: true, lesson: null })
          }
          disabled={review.status !== "DRAFT"}>

          <Plus className="h-4 w-4 mr-2" />
          添加经验教训
        </Button>
      </div>

      {lessons.length === 0 ?
      <Card className="bg-slate-800/50 border-slate-700/50">
          <CardContent className="p-12 text-center">
            <FileText className="w-12 h-12 text-slate-400 mx-auto mb-4" />
            <p className="text-slate-400">暂无经验教训</p>
            {review.status === "DRAFT" &&
          <Button
            onClick={() =>
            setLessonDialog({ open: true, lesson: null })
            }
            className="mt-4">

                <Plus className="h-4 w-4 mr-2" />
                添加第一条经验教训
          </Button>
          }
          </CardContent>
      </Card> :

      <div className="grid gap-4">
          {(lessons || []).map((lesson) => {
          const lessonType = getLessonType(lesson.type);
          const Icon = lessonType.icon;

          return (
            <motion.div
              key={lesson.id}
              variants={staggerChild}
              className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-6">

                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-3">
                      <div className={`p-2 rounded-lg ${lessonType.bgColor}`}>
                        <Icon className={`w-4 h-4 ${lessonType.textColor}`} />
                      </div>
                      <div>
                        <h4 className="text-white font-medium">
                          {lesson.title}
                        </h4>
                        <Badge
                        variant="outline"
                        className={cn(
                          "border",
                          lessonType.borderColor,
                          lessonType.textColor
                        )}>

                          {lessonType.label}
                        </Badge>
                      </div>
                    </div>
                    <p className="text-slate-300 mb-3">
                      {lesson.description}
                    </p>
                    {lesson.actions &&
                  <div>
                        <h5 className="text-sm font-medium text-white mb-2">
                          改进措施:
                        </h5>
                        <p className="text-slate-400 text-sm">
                          {lesson.actions}
                        </p>
                  </div>
                  }
                  </div>
                  {review.status === "DRAFT" &&
                <div className="flex items-center gap-2 ml-4">
                      <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      setLessonDialog({ open: true, lesson });
                      setLessonForm({
                        title: lesson.title,
                        description: lesson.description,
                        category: lesson.category,
                        impact: lesson.impact,
                        actions: lesson.actions,
                        tags: lesson.tags || []
                      });
                    }}>

                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button
                    variant="ghost"
                    size="sm"
                    onClick={() =>
                    setDeleteLessonDialog({
                      open: true,
                      lessonId: lesson.id
                    })
                    }>

                        <Trash2 className="h-4 w-4" />
                      </Button>
                </div>
                }
                </div>
            </motion.div>);

        })}
      </div>
      }
    </>
  );
}
