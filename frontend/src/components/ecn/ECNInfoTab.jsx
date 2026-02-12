/**
 * ECN Info Tab Component
 * ECN 基本信息标签页
 */
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import { formatDate } from "../../lib/utils";
import { getStatusBadge, getTypeBadge, getPriorityBadge } from "@/lib/constants/ecn";
import { 
  FileText, 
  Users, 
  Calendar, 
  DollarSign, 
  Layers,
  AlertTriangle 
} from "lucide-react";

export default function ECNInfoTab({ ecn }) {
  const statusBadge = getStatusBadge(ecn.status);
  const typeBadge = getTypeBadge(ecn.change_type);
  const priorityBadge = getPriorityBadge(ecn.priority);

  const InfoRow = ({ label, value, icon: Icon }) => (
    <div className="flex items-start py-3 border-b border-slate-200 last:border-0">
      <div className="flex items-center gap-2 w-40 text-sm text-slate-600">
        {Icon && <Icon className="w-4 h-4" />}
        {label}
      </div>
      <div className="flex-1 text-sm font-medium">{value || "-"}</div>
    </div>
  );

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* 基本信息 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="w-5 h-5" />
            基本信息
          </CardTitle>
        </CardHeader>
        <CardContent>
          <InfoRow label="ECN编号" value={ecn.code} icon={FileText} />
          <InfoRow 
            label="状态" 
            value={<Badge className={statusBadge.color}>{statusBadge.text}</Badge>}
          />
          <InfoRow 
            label="变更类型" 
            value={<Badge className={typeBadge.color}>{typeBadge.text}</Badge>}
          />
          <InfoRow 
            label="优先级" 
            value={<Badge className={priorityBadge.color}>{priorityBadge.text}</Badge>}
          />
          <InfoRow label="标题" value={ecn.title} />
          <InfoRow label="变更原因" value={ecn.change_reason} />
          {ecn.affected_products && (
            <InfoRow 
              label="影响产品" 
              value={ecn.affected_products} 
              icon={Layers}
            />
          )}
          {ecn.affected_projects && (
            <InfoRow 
              label="影响项目" 
              value={ecn.affected_projects}
            />
          )}
        </CardContent>
      </Card>

      {/* 人员和时间 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="w-5 h-5" />
            人员和时间
          </CardTitle>
        </CardHeader>
        <CardContent>
          <InfoRow 
            label="申请人" 
            value={ecn.requester_name || ecn.requester_id} 
            icon={Users}
          />
          <InfoRow 
            label="申请部门" 
            value={ecn.department_name || ecn.department}
          />
          <InfoRow 
            label="申请时间" 
            value={formatDate(ecn.request_date)} 
            icon={Calendar}
          />
          <InfoRow 
            label="要求完成日期" 
            value={formatDate(ecn.required_complete_date)}
            icon={AlertTriangle}
          />
          <InfoRow 
            label="创建时间" 
            value={formatDate(ecn.created_at)}
          />
          <InfoRow 
            label="更新时间" 
            value={formatDate(ecn.updated_at)}
          />
          {ecn.approved_at && (
            <InfoRow 
              label="批准时间" 
              value={formatDate(ecn.approved_at)}
            />
          )}
          {ecn.completed_at && (
            <InfoRow 
              label="完成时间" 
              value={formatDate(ecn.completed_at)}
            />
          )}
        </CardContent>
      </Card>

      {/* 变更描述 */}
      <Card className="lg:col-span-2">
        <CardHeader>
          <CardTitle>变更描述</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="prose prose-sm max-w-none">
            <div className="mb-4">
              <h4 className="text-sm font-semibold mb-2">变更内容</h4>
              <p className="text-sm text-slate-700 whitespace-pre-wrap">
                {ecn.description || "无"}
              </p>
            </div>
            
            {ecn.technical_details && (
              <div className="mb-4">
                <h4 className="text-sm font-semibold mb-2">技术细节</h4>
                <p className="text-sm text-slate-700 whitespace-pre-wrap">
                  {ecn.technical_details}
                </p>
              </div>
            )}

            {ecn.implementation_plan && (
              <div className="mb-4">
                <h4 className="text-sm font-semibold mb-2">实施计划</h4>
                <p className="text-sm text-slate-700 whitespace-pre-wrap">
                  {ecn.implementation_plan}
                </p>
              </div>
            )}

            {ecn.risk_assessment && (
              <div className="mb-4">
                <h4 className="text-sm font-semibold mb-2">风险评估</h4>
                <p className="text-sm text-slate-700 whitespace-pre-wrap">
                  {ecn.risk_assessment}
                </p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* 成本影响 */}
      {(ecn.estimated_cost || ecn.actual_cost) && (
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <DollarSign className="w-5 h-5" />
              成本影响
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {ecn.estimated_cost && (
                <div>
                  <div className="text-sm text-slate-600 mb-1">预估成本</div>
                  <div className="text-2xl font-bold text-blue-600">
                    ¥{ecn.estimated_cost?.toLocaleString()}
                  </div>
                </div>
              )}
              {ecn.actual_cost && (
                <div>
                  <div className="text-sm text-slate-600 mb-1">实际成本</div>
                  <div className="text-2xl font-bold text-emerald-600">
                    ¥{ecn.actual_cost?.toLocaleString()}
                  </div>
                </div>
              )}
              {ecn.estimated_cost && ecn.actual_cost && (
                <div>
                  <div className="text-sm text-slate-600 mb-1">成本差异</div>
                  <div className={`text-2xl font-bold ${
                    ecn.actual_cost > ecn.estimated_cost ? 'text-red-600' : 'text-emerald-600'
                  }`}>
                    {ecn.actual_cost > ecn.estimated_cost ? '+' : ''}
                    ¥{(ecn.actual_cost - ecn.estimated_cost).toLocaleString()}
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
