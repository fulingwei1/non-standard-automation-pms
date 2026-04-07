import { useNavigate } from "react-router-dom";


import { fadeIn } from "../../lib/animations";
import {
  getServiceStatusConfig,
  getServiceTypeConfig,
} from "../../components/service-record";
import { getServiceTypeIcon } from "./useServiceRecordPage";

export default function RecordListItem({ record, index, onViewDetail }) {
  const navigate = useNavigate();
  const statusConfig = getServiceStatusConfig(record.status);
  const typeConfig = getServiceTypeConfig(record.service_type);
  const TypeIcon = getServiceTypeIcon(record.service_type);

  return (
    <motion.div key={record.id} variants={fadeIn} custom={index}>
      <Card className="bg-slate-800/50 border-slate-700 hover:bg-slate-800/70 transition-colors">
        <CardContent className="p-6">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-4">
                <TypeIcon className="h-5 w-5 text-blue-400" />
                <h3 className="text-lg font-semibold text-white">
                  {record.project_name || "未命名项目"}
                </h3>
                <Badge className={statusConfig.color}>
                  {statusConfig.label}
                </Badge>
                <Badge
                  variant="outline"
                  className="border-blue-500 text-blue-400"
                >
                  {typeConfig.label}
                </Badge>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
                <div className="flex items-center gap-2 text-sm">
                  <User className="h-4 w-4 text-slate-400" />
                  <span className="text-slate-300">客户:</span>
                  <span className="text-white">{record.customer_name}</span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <MapPin className="h-4 w-4 text-slate-400" />
                  <span className="text-slate-300">地点:</span>
                  <span className="text-white truncate">
                    {record.service_location}
                  </span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <Calendar className="h-4 w-4 text-slate-400" />
                  <span className="text-slate-300">日期:</span>
                  <span className="text-white">
                    {record.service_date
                      ? new Date(record.service_date).toLocaleDateString()
                      : "未设置"}
                  </span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <Clock className="h-4 w-4 text-slate-400" />
                  <span className="text-slate-300">工程师:</span>
                  <span className="text-white">
                    {record.service_engineer}
                  </span>
                </div>
              </div>

              {record.service_content && (
                <div className="mb-4">
                  <p className="text-sm text-slate-400 mb-1">服务内容:</p>
                  <p className="text-sm text-white line-clamp-2">
                    {record.service_content}
                  </p>
                </div>
              )}

              {record.photos && record.photos?.length > 0 && (
                <div className="flex items-center gap-2 text-sm">
                  <Camera className="h-4 w-4 text-slate-400" />
                  <span className="text-slate-300">照片:</span>
                  <span className="text-white">
                    {record.photos?.length} 张
                  </span>
                </div>
              )}
            </div>

            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onViewDetail(record)}
                className="text-slate-400 hover:text-white"
              >
                <Eye className="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate(`/service/records/${record.id}/edit`)}
                className="text-slate-400 hover:text-white"
              >
                <Edit className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
