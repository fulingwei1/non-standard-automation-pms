

import { toast } from "../../components/ui/toast";
import { getServiceTypeConfig } from "../../components/service-record";

export default function DetailDialog({ open, onOpenChange, record }) {
  if (!record) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-5xl bg-slate-900 border-slate-700 max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>服务记录详情</DialogTitle>
        </DialogHeader>

        <div className="space-y-6">
          {/* 基本信息 */}
          <div>
            <h3 className="text-lg font-semibold text-white mb-4">基本信息</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <div>
                <span className="text-sm text-slate-400">记录编号:</span>
                <p className="text-white">{record.record_no}</p>
              </div>
              <div>
                <span className="text-sm text-slate-400">项目名称:</span>
                <p className="text-white">{record.project_name}</p>
              </div>
              <div>
                <span className="text-sm text-slate-400">客户名称:</span>
                <p className="text-white">{record.customer_name}</p>
              </div>
              <div>
                <span className="text-sm text-slate-400">服务类型:</span>
                <p className="text-white">
                  {getServiceTypeConfig(record.service_type).label}
                </p>
              </div>
              <div>
                <span className="text-sm text-slate-400">服务地点:</span>
                <p className="text-white">{record.service_location}</p>
              </div>
              <div>
                <span className="text-sm text-slate-400">服务日期:</span>
                <p className="text-white">
                  {record.service_date
                    ? new Date(record.service_date).toLocaleDateString()
                    : "-"}
                </p>
              </div>
            </div>
          </div>

          {/* 服务内容 */}
          <div>
            <h3 className="text-lg font-semibold text-white mb-4">服务内容</h3>
            <p className="text-slate-300">
              {record.service_content || "-"}
            </p>
          </div>

          {/* 服务结果 */}
          <div>
            <h3 className="text-lg font-semibold text-white mb-4">服务结果</h3>
            <p className="text-slate-300">
              {record.service_result || "-"}
            </p>
          </div>

          {/* 照片展示 */}
          {record.photos && record.photos?.length > 0 && (
            <div>
              <h3 className="text-lg font-semibold text-white mb-4">
                服务照片
              </h3>
              <div className="grid grid-cols-4 gap-4">
                {(record.photos || []).map((photo, index) => (
                  <img
                    key={index}
                    src={photo.url || photo}
                    alt={`服务照片 ${index + 1}`}
                    className="w-full h-32 object-cover rounded border border-slate-700"
                  />
                ))}
              </div>
            </div>
          )}

          {/* 客户反馈 */}
          {record.customer_feedback && (
            <div>
              <h3 className="text-lg font-semibold text-white mb-4">
                客户反馈
              </h3>
              <div className="bg-slate-800/50 p-4 rounded">
                {record.customer_satisfaction && (
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-sm text-slate-400">满意度:</span>
                    <div className="flex">
                      {[1, 2, 3, 4, 5].map((star) => (
                        <Star
                          key={star}
                          className={`h-4 w-4 ${
                            star <= record.customer_satisfaction
                              ? "text-yellow-400 fill-current"
                              : "text-slate-600"
                          }`}
                        />
                      ))}
                    </div>
                  </div>
                )}
                <p className="text-slate-300">{record.customer_feedback}</p>
              </div>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            关闭
          </Button>
          <Button
            onClick={() => {
              toast.info("报告下载功能开发中...");
            }}
            className="bg-blue-500 hover:bg-blue-600"
          >
            <Download className="h-4 w-4 mr-2" />
            下载报告
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
