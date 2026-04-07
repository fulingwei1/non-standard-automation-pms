/**
 * DetailDialog - Dialog for viewing alert details
 */



import {
  getAlertLevelConfig,
  getAlertStatusConfig,
  getAlertTypeConfig } from
"../../components/alert-center";

export default function DetailDialog({
  open,
  onOpenChange,
  selectedAlert
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>预警详情</DialogTitle>
        </DialogHeader>
        {selectedAlert &&
        <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="text-lg font-semibold text-white mb-4">基本信息</h3>
                <div className="space-y-3">
                  <div>
                    <span className="text-sm text-slate-400">预警编号:</span>
                    <p className="text-white">{selectedAlert.alert_no || '-'}</p>
                  </div>
                  <div>
                    <span className="text-sm text-slate-400">预警级别:</span>
                    <p className="text-white">
                      {getAlertLevelConfig(selectedAlert.alert_level).label}
                    </p>
                  </div>
                  <div>
                    <span className="text-sm text-slate-400">预警类型:</span>
                    <p className="text-white">
                      {getAlertTypeConfig(selectedAlert.alert_type).label}
                    </p>
                  </div>
                  <div>
                    <span className="text-sm text-slate-400">当前状态:</span>
                    <p className="text-white">
                      {getAlertStatusConfig(selectedAlert.status).label}
                    </p>
                  </div>
                </div>
              </div>
              <div>
                <h3 className="text-lg font-semibold text-white mb-4">时间信息</h3>
                <div className="space-y-3">
                  <div>
                    <span className="text-sm text-slate-400">触发时间:</span>
                    <p className="text-white">
                      {selectedAlert.triggered_at ? new Date(selectedAlert.triggered_at).toLocaleString() : '-'}
                    </p>
                  </div>
                  {selectedAlert.first_action_time &&
                <div>
                      <span className="text-sm text-slate-400">首次响应:</span>
                      <p className="text-white">
                        {new Date(selectedAlert.first_action_time).toLocaleString()}
                      </p>
                </div>
                }
                  {selectedAlert.resolved_time &&
                <div>
                      <span className="text-sm text-slate-400">解决时间:</span>
                      <p className="text-white">
                        {new Date(selectedAlert.resolved_time).toLocaleString()}
                      </p>
                </div>
                }
                </div>
              </div>
            </div>

            {selectedAlert.description &&
          <div>
                <h3 className="text-lg font-semibold text-white mb-4">详细描述</h3>
                <p className="text-slate-300">{selectedAlert.description}</p>
          </div>
          }

            {selectedAlert.trigger_data &&
          <div>
                <h3 className="text-lg font-semibold text-white mb-4">触发数据</h3>
                <pre className="bg-slate-800 p-4 rounded text-sm text-slate-300 overflow-auto">
                  {JSON.stringify(selectedAlert.trigger_data, null, 2)}
                </pre>
          </div>
          }
        </div>
        }
        <DialogFooter>
          <Button
            onClick={() => onOpenChange(false)}
            className="w-full">

            关闭
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
