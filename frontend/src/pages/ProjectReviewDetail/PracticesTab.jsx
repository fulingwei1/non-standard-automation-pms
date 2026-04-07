/**
 * Best Practices tab content for ProjectReviewDetail
 */




import { staggerChild } from "./constants";

export default function PracticesTab({
  bestPractices,
  review,
  setPracticeDialog,
  setPracticeForm,
  setDeletePracticeDialog,
}) {
  return (
    <>
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium text-white">最佳实践</h3>
        <Button
          onClick={() =>
          setPracticeDialog({ open: true, practice: null })
          }
          disabled={review.status !== "DRAFT"}>

          <Plus className="h-4 w-4 mr-2" />
          添加最佳实践
        </Button>
      </div>

      {bestPractices.length === 0 ?
      <Card className="bg-slate-800/50 border-slate-700/50">
          <CardContent className="p-12 text-center">
            <BookOpen className="w-12 h-12 text-slate-400 mx-auto mb-4" />
            <p className="text-slate-400">暂无最佳实践</p>
            {review.status === "DRAFT" &&
          <Button
            onClick={() =>
            setPracticeDialog({ open: true, practice: null })
            }
            className="mt-4">

                <Plus className="h-4 w-4 mr-2" />
                添加第一条最佳实践
          </Button>
          }
          </CardContent>
      </Card> :

      <div className="grid gap-4">
          {(bestPractices || []).map((practice) =>
        <motion.div
          key={practice.id}
          variants={staggerChild}
          className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-6">

              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="p-2 rounded-lg bg-green-500/20">
                      <BookOpen className="w-4 h-4 text-green-400" />
                    </div>
                    <div>
                      <h4 className="text-white font-medium">
                        {practice.title}
                      </h4>
                      <Badge variant="outline" className="border-green-500/30 text-green-400">
                        {practice.category || "通用实践"}
                      </Badge>
                    </div>
                  </div>
                  <p className="text-slate-300 mb-3">
                    {practice.description}
                  </p>
                  {practice.applicability &&
              <div className="mb-3">
                      <h5 className="text-sm font-medium text-white mb-1">
                        适用范围:
                      </h5>
                      <p className="text-slate-400 text-sm">
                        {practice.applicability}
                      </p>
              </div>
              }
                  {practice.benefits &&
              <div className="mb-3">
                      <h5 className="text-sm font-medium text-white mb-1">
                        预期收益:
                      </h5>
                      <p className="text-slate-400 text-sm">
                        {practice.benefits}
                      </p>
              </div>
              }
                  {practice.implementation &&
              <div>
                      <h5 className="text-sm font-medium text-white mb-1">
                        实施要点:
                      </h5>
                      <p className="text-slate-400 text-sm">
                        {practice.implementation}
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
                  setPracticeDialog({ open: true, practice });
                  setPracticeForm({
                    title: practice.title,
                    description: practice.description,
                    category: practice.category,
                    applicability: practice.applicability,
                    benefits: practice.benefits,
                    implementation: practice.implementation,
                    tags: practice.tags || []
                  });
                }}>

                      <Edit className="h-4 w-4" />
                    </Button>
                    <Button
                variant="ghost"
                size="sm"
                onClick={() =>
                setDeletePracticeDialog({
                  open: true,
                  practiceId: practice.id
                })
                }>

                      <Trash2 className="h-4 w-4" />
                    </Button>
            </div>
            }
              </div>
        </motion.div>
        )}
      </div>
      }
    </>
  );
}
