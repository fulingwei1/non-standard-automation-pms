import { Users, Briefcase, Percent } from 'lucide-react'

/**
 * 权重输入卡片组件
 */
export const WeightInputCard = ({ type, label, description, icon: Icon, iconColor, weight, onChange }) => {
  return (
    <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700/50">
      <div className="flex items-center gap-3 mb-4">
        <div className={`h-12 w-12 rounded-full ${iconColor}/20 flex items-center justify-center`}>
          <Icon className={`h-6 w-6 ${iconColor}`} />
        </div>
        <div>
          <h3 className="text-white font-medium">{label}</h3>
          <p className="text-sm text-slate-400">{description}</p>
        </div>
      </div>

      <div className="space-y-4">
        <div className="flex items-center gap-4">
          <input
            type="number"
            min="0"
            max="100"
            value={weight}
            onChange={(e) => onChange(type, e.target.value)}
            className="w-24 h-12 px-4 text-center text-2xl font-bold bg-slate-900/50 border-2 border-slate-700 rounded-lg text-white focus:outline-none focus:border-blue-500"
          />
          <Percent className="h-6 w-6 text-slate-400" />
          <input
            type="range"
            min="0"
            max="100"
            value={weight}
            onChange={(e) => onChange(type, e.target.value)}
            className="flex-1 h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
          />
        </div>
        <p className="text-sm text-slate-400">
          {type === 'dept' 
            ? '部门经理根据员工日常表现、工作态度、部门贡献进行评价'
            : '项目经理根据员工在项目中的表现、任务完成情况进行评价'}
        </p>
      </div>
    </div>
  )
}
