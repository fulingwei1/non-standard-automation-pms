



import { staggerContainer } from "@/lib/animations";
import { DEPARTMENTS } from "./constants";

export default function Step4DeptObjectives({
  deptObjectivesInput,
  setDeptObjectivesInput,
  deptObjectivesResult,
  loading,
  onGenerate,
  onApply,
  onPrev,
}) {
  return (
    <motion.div {...staggerContainer} className="space-y-6">
      <Card className="bg-gray-800/50 border-gray-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Users className="w-5 h-5 text-blue-400" />
            部门信息
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label className="text-gray-300">选择部门</Label>
            <Select
              value={deptObjectivesInput.departmentName}
              onValueChange={(value) => {
                const dept = DEPARTMENTS.find((d) => d.value === value);
                setDeptObjectivesInput({
                  ...deptObjectivesInput,
                  departmentName: value,
                  departmentRole: dept?.role || "",
                });
              }}
            >
              <SelectTrigger className="bg-gray-900 border-gray-700 text-white">
                <SelectValue placeholder="请选择部门" />
              </SelectTrigger>
              <SelectContent className="bg-gray-800 border-gray-700">
                {DEPARTMENTS.map((dept) => (
                  <SelectItem key={dept.value} value={dept.value} className="text-white">
                    {dept.value}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label className="text-gray-300">部门职能描述</Label>
            <Textarea
              value={deptObjectivesInput.departmentRole}
              onChange={(e) => setDeptObjectivesInput({ ...deptObjectivesInput, departmentRole: e.target.value })}
              className="bg-gray-900 border-gray-700 text-white min-h-[80px]"
              placeholder="描述部门的主要职能和责任"
            />
          </div>
          <div>
            <Label className="text-gray-300">年度</Label>
            <Input
              type="number"
              value={deptObjectivesInput.year}
              onChange={(e) => setDeptObjectivesInput({ ...deptObjectivesInput, year: parseInt(e.target.value) })}
              className="bg-gray-900 border-gray-700 text-white"
            />
          </div>
          <Button
            onClick={onGenerate}
            disabled={loading || !deptObjectivesInput.departmentName}
            className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                AI 生成中...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4 mr-2" />
                AI 生成部门 OKR
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {deptObjectivesResult && (
        <motion.div {...staggerContainer} className="space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-white">
              {deptObjectivesInput.departmentName} OKR 目标
            </h3>
            <Button onClick={onApply} size="sm" variant="outline">
              <Upload className="w-4 h-4 mr-2" />
              导入系统
            </Button>
          </div>

          <div className="grid gap-4">
            {deptObjectivesResult.objectives?.map((obj, i) => (
              <Card key={i} className="bg-gray-800/50 border-gray-700 border-l-4 border-l-purple-500">
                <CardContent className="pt-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <div className="text-sm text-purple-400 font-medium mb-1">
                        Objective {i + 1}
                      </div>
                      <div className="text-white text-lg font-semibold">{obj.objective}</div>
                    </div>
                    <Badge variant="secondary" className="bg-gray-700 text-gray-300">
                      权重：{obj.weight}%
                    </Badge>
                  </div>
                  <div className="space-y-2 mb-4">
                    <div className="text-sm text-gray-400 font-medium">Key Results:</div>
                    {obj.key_results?.map((kr, krIndex) => (
                      <div key={krIndex} className="flex items-start gap-2 text-sm">
                        <Target className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0" />
                        <span className="text-gray-300">{kr}</span>
                      </div>
                    ))}
                  </div>
                  {obj.related_kpis?.length > 0 && (
                    <div className="pt-3 border-t border-gray-700">
                      <div className="text-sm text-gray-400 font-medium mb-2">关联 KPI:</div>
                      <div className="flex flex-wrap gap-2">
                        {obj.related_kpis.map((kpi, kpiIndex) => (
                          <Badge key={kpiIndex} variant="outline" className="text-xs">
                            {kpi.kpi_name}: {kpi.target_value} {kpi.unit}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>

          <div className="flex gap-4">
            <Button onClick={onPrev} variant="outline" className="flex-1">
              <ArrowLeft className="w-4 h-4 mr-2" />
              上一步
            </Button>
            <Button onClick={() => alert("完成！所有数据已导入系统。")} className="flex-1 bg-green-600 hover:bg-green-700">
              <Check className="w-4 h-4 mr-2" />
              完成
            </Button>
          </div>
        </motion.div>
      )}
    </motion.div>
  );
}
