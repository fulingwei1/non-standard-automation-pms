



import { cn } from "../../lib/utils";
import { fadeIn } from "../../lib/animations";
import { getStatusStyle, getStatusName, getMethodIcon } from "./utils";

export default function SurveyCard({ survey, onClick }) {
  const methodConfig = getMethodIcon(survey.method);
  const MethodIcon = methodConfig.icon;

  return (
    <motion.div
      variants={fadeIn}
      className="p-4 rounded-xl bg-surface-100/50 backdrop-blur-lg border border-white/5 hover:bg-white/[0.03] cursor-pointer transition-all group"
      onClick={() => onClick(survey)}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1.5 flex-wrap">
            <Badge className={cn("text-xs", getStatusStyle(survey.status))}>
              {getStatusName(survey.status)}
            </Badge>
            <span className="text-xs text-slate-500">{survey.code}</span>
          </div>
          <h4 className="text-sm font-medium text-white group-hover:text-primary transition-colors">
            {survey.customer}
          </h4>
          <p className="text-xs text-slate-500 mt-0.5">{survey.opportunity}</p>
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="opacity-0 group-hover:opacity-100 transition-opacity"
              onClick={(e) => e.stopPropagation()}
            >
              <MoreHorizontal className="w-4 h-4 text-slate-400" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem>
              <Eye className="w-4 h-4 mr-2" />
              查看详情
            </DropdownMenuItem>
            <DropdownMenuItem>
              <Edit className="w-4 h-4 mr-2" />
              编辑
            </DropdownMenuItem>
            <DropdownMenuItem>
              <FileText className="w-4 h-4 mr-2" />
              生成方案
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem className="text-red-400">
              <Trash2 className="w-4 h-4 mr-2" />
              删除
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      <p className="text-xs text-slate-500 line-clamp-2 mb-3">
        {survey.summary}
      </p>

      <div className="flex items-center gap-3 text-xs text-slate-500 mb-3">
        <span className="flex items-center gap-1">
          <MethodIcon className={cn("w-3 h-3", methodConfig.color)} />
          {survey.methodName}
        </span>
        <span className="flex items-center gap-1">
          <User className="w-3 h-3" />
          {survey.contactPerson}
        </span>
      </div>

      {survey.pendingQuestions?.length > 0 && (
        <div className="flex items-center gap-2 mb-3">
          <AlertTriangle className="w-3 h-3 text-amber-400" />
          <span className="text-xs text-amber-400">
            {survey.pendingQuestions?.length} 个待确认问题
          </span>
        </div>
      )}

      <div className="flex items-center justify-between text-xs pt-3 border-t border-white/5">
        <div className="flex items-center gap-3 text-slate-500">
          <span className="flex items-center gap-1">
            <Calendar className="w-3 h-3" />
            {survey.scheduledDate}
          </span>
          <span className="flex items-center gap-1">
            <Users className="w-3 h-3" />
            {survey.engineer}
          </span>
        </div>
        {survey.attachments?.length > 0 && (
          <span className="flex items-center gap-1 text-slate-500">
            <Paperclip className="w-3 h-3" />
            {survey.attachments?.length}
          </span>
        )}
      </div>
    </motion.div>
  );
}
