

import { cn } from "../../lib/utils";
import { getStatusStyle, getStatusName, getMethodIcon } from "./utils";

export default function SurveyDetailPanel({ survey, onClose }) {
  if (!survey) {return null;}

  const methodConfig = getMethodIcon(survey.method);
  const MethodIcon = methodConfig.icon;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ x: "100%" }}
        animate={{ x: 0 }}
        exit={{ x: "100%" }}
        transition={{ type: "spring", damping: 25, stiffness: 200 }}
        className="fixed right-0 top-0 h-full w-full md:w-[500px] bg-surface-100/95 backdrop-blur-xl border-l border-white/5 shadow-2xl z-50 flex flex-col"
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-white/5">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Badge className={cn("text-xs", getStatusStyle(survey.status))}>
                {getStatusName(survey.status)}
              </Badge>
              <span className="text-xs text-slate-500">{survey.code}</span>
            </div>
            <h2 className="text-lg font-semibold text-white">
              {survey.customer}
            </h2>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="w-5 h-5 text-slate-400" />
          </Button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto custom-scrollbar p-4 space-y-6">
          {/* 基本信息 */}
          <div className="space-y-3">
            <h4 className="text-sm font-medium text-slate-400">基本信息</h4>
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-surface-50 p-3 rounded-lg">
                <p className="text-xs text-slate-500 mb-1">调研方式</p>
                <p className="text-sm text-white flex items-center gap-1">
                  <MethodIcon className={cn("w-4 h-4", methodConfig.color)} />
                  {survey.methodName}
                </p>
              </div>
              <div className="bg-surface-50 p-3 rounded-lg">
                <p className="text-xs text-slate-500 mb-1">调研日期</p>
                <p className="text-sm text-white">{survey.scheduledDate}</p>
              </div>
              <div className="bg-surface-50 p-3 rounded-lg">
                <p className="text-xs text-slate-500 mb-1">联系人</p>
                <p className="text-sm text-white">{survey.contactPerson}</p>
              </div>
              <div className="bg-surface-50 p-3 rounded-lg">
                <p className="text-xs text-slate-500 mb-1">联系电话</p>
                <p className="text-sm text-white">{survey.contactPhone}</p>
              </div>
            </div>
            {survey.location && (
              <div className="bg-surface-50 p-3 rounded-lg">
                <p className="text-xs text-slate-500 mb-1">调研地点</p>
                <p className="text-sm text-white flex items-center gap-1">
                  <MapPin className="w-4 h-4 text-primary" />
                  {survey.location}
                </p>
              </div>
            )}
          </div>

          {/* 调研摘要 */}
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-slate-400">调研摘要</h4>
            <p className="text-sm text-white bg-surface-50 p-3 rounded-lg">
              {survey.summary}
            </p>
          </div>

          {/* 产品信息 */}
          {survey.productInfo && (
            <div className="space-y-3">
              <h4 className="text-sm font-medium text-slate-400 flex items-center gap-2">
                <Package className="w-4 h-4 text-primary" />
                产品信息
              </h4>
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-surface-50 p-3 rounded-lg">
                  <p className="text-xs text-slate-500 mb-1">产品名称</p>
                  <p className="text-sm text-white">
                    {survey.productInfo.name}
                  </p>
                </div>
                <div className="bg-surface-50 p-3 rounded-lg">
                  <p className="text-xs text-slate-500 mb-1">型号规格</p>
                  <p className="text-sm text-white">
                    {survey.productInfo.model}
                  </p>
                </div>
                <div className="bg-surface-50 p-3 rounded-lg">
                  <p className="text-xs text-slate-500 mb-1">外形尺寸</p>
                  <p className="text-sm text-white">
                    {survey.productInfo.size}
                  </p>
                </div>
                <div className="bg-surface-50 p-3 rounded-lg">
                  <p className="text-xs text-slate-500 mb-1">材质</p>
                  <p className="text-sm text-white">
                    {survey.productInfo.material}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* 测试需求 */}
          {survey.testRequirements?.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-sm font-medium text-slate-400 flex items-center gap-2">
                <Settings className="w-4 h-4 text-primary" />
                测试需求
              </h4>
              <div className="flex flex-wrap gap-2">
                {(survey.testRequirements || []).map((item, index) => (
                  <Badge key={index} variant="outline" className="text-xs">
                    {item}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* 产能需求 */}
          {survey.capacityRequirements && (
            <div className="space-y-3">
              <h4 className="text-sm font-medium text-slate-400 flex items-center gap-2">
                <Target className="w-4 h-4 text-primary" />
                产能需求
              </h4>
              <div className="grid grid-cols-3 gap-3">
                <div className="bg-surface-50 p-3 rounded-lg text-center">
                  <p className="text-xs text-slate-500 mb-1">年产量</p>
                  <p className="text-lg font-bold text-white">
                    {(survey.capacityRequirements.annual / 10000).toFixed(0)}万
                  </p>
                </div>
                <div className="bg-surface-50 p-3 rounded-lg text-center">
                  <p className="text-xs text-slate-500 mb-1">日产量</p>
                  <p className="text-lg font-bold text-white">
                    {survey.capacityRequirements.daily}
                  </p>
                </div>
                <div className="bg-surface-50 p-3 rounded-lg text-center">
                  <p className="text-xs text-slate-500 mb-1">UPH</p>
                  <p className="text-lg font-bold text-white">
                    {survey.capacityRequirements.uph}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* 场地条件 */}
          {survey.siteConditions && (
            <div className="space-y-3">
              <h4 className="text-sm font-medium text-slate-400 flex items-center gap-2">
                <Building2 className="w-4 h-4 text-primary" />
                场地条件
              </h4>
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-surface-50 p-3 rounded-lg">
                  <p className="text-xs text-slate-500 mb-1 flex items-center gap-1">
                    <Ruler className="w-3 h-3" />
                    可用面积
                  </p>
                  <p className="text-sm text-white">
                    {survey.siteConditions.area}
                  </p>
                </div>
                <div className="bg-surface-50 p-3 rounded-lg">
                  <p className="text-xs text-slate-500 mb-1 flex items-center gap-1">
                    <Zap className="w-3 h-3" />
                    电源
                  </p>
                  <p className="text-sm text-white">
                    {survey.siteConditions.power}
                  </p>
                </div>
                <div className="bg-surface-50 p-3 rounded-lg">
                  <p className="text-xs text-slate-500 mb-1">气源</p>
                  <p className="text-sm text-white">
                    {survey.siteConditions.airPressure}
                  </p>
                </div>
                <div className="bg-surface-50 p-3 rounded-lg">
                  <p className="text-xs text-slate-500 mb-1 flex items-center gap-1">
                    <Thermometer className="w-3 h-3" />
                    环境
                  </p>
                  <p className="text-sm text-white">
                    {survey.siteConditions.environment}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* 预算和时间 */}
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-gradient-to-br from-emerald-500/10 to-teal-500/10 p-4 rounded-lg border border-emerald-500/20">
              <p className="text-xs text-slate-400 mb-1 flex items-center gap-1">
                <DollarSign className="w-3 h-3" />
                预算范围
              </p>
              <p className="text-lg font-bold text-emerald-400">
                {survey.budget}
              </p>
            </div>
            <div className="bg-gradient-to-br from-blue-500/10 to-cyan-500/10 p-4 rounded-lg border border-blue-500/20">
              <p className="text-xs text-slate-400 mb-1 flex items-center gap-1">
                <Calendar className="w-3 h-3" />
                交付时间
              </p>
              <p className="text-lg font-bold text-blue-400">
                {survey.timeline}
              </p>
            </div>
          </div>

          {/* 竞争情况 */}
          {survey.competitors?.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-sm font-medium text-slate-400">竞争情况</h4>
              <div className="flex flex-wrap gap-2">
                {(survey.competitors || []).map((item, index) => (
                  <Badge key={index} variant="destructive" className="text-xs">
                    {item}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* 待确认问题 */}
          {survey.pendingQuestions?.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-sm font-medium text-amber-400 flex items-center gap-2">
                <HelpCircle className="w-4 h-4" />
                待确认问题
              </h4>
              <div className="space-y-2">
                {(survey.pendingQuestions || []).map((question, index) => (
                  <div
                    key={index}
                    className="flex items-center gap-2 bg-amber-500/10 p-3 rounded-lg border border-amber-500/20"
                  >
                    <AlertTriangle className="w-4 h-4 text-amber-400" />
                    <span className="text-sm text-white">{question}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 附件 */}
          {survey.attachments?.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-sm font-medium text-slate-400 flex items-center gap-2">
                <Paperclip className="w-4 h-4 text-primary" />
                附件 ({survey.attachments?.length})
              </h4>
              <div className="space-y-2">
                {(survey.attachments || []).map((file, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between bg-surface-50 p-3 rounded-lg"
                  >
                    <div className="flex items-center gap-2">
                      {file.type === "image" ? (
                        <Image className="w-4 h-4 text-slate-400" />
                      ) : (
                        <FileText className="w-4 h-4 text-slate-400" />
                      )}
                      <span className="text-sm text-white">{file.name}</span>
                      <span className="text-xs text-slate-500">
                        {file.size}
                      </span>
                    </div>
                    <Button variant="ghost" size="sm">
                      <Eye className="w-4 h-4" />
                    </Button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-white/5 flex gap-2">
          <Button variant="outline" className="flex-1">
            <Edit className="w-4 h-4 mr-2" />
            编辑
          </Button>
          <Button className="flex-1">
            <FileText className="w-4 h-4 mr-2" />
            生成方案
          </Button>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
