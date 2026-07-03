/**
 * PageHeader — title bar with action buttons for the delivery list view
 */

import { Truck, CalendarPlus, RefreshCw, Download } from "lucide-react";
import { Button } from "../../components/ui";

const PageHeader = ({ canCreateFromProject = false, onNew, onRefresh, onExport }) => (
  <div className="mb-6">
    <div className="flex items-center justify-between">
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2 mb-1">
          <Truck className="w-6 h-6" />
          发货管理
        </h1>
        <p className="text-slate-400">
          PMC 发货管理 - 发货计划、订单列表、在途跟踪
        </p>
      </div>
      <div className="flex gap-2">
        {canCreateFromProject && (
          <Button className="flex items-center gap-2" onClick={onNew}>
            <CalendarPlus size={16} />
            生成发货计划
          </Button>
        )}
        <Button
          variant="outline"
          className="flex items-center gap-2"
          onClick={onRefresh}
        >
          <RefreshCw size={16} />
          刷新
        </Button>
        <Button variant="outline" className="flex items-center gap-2" onClick={onExport}>
          <Download size={16} />
          导出报表
        </Button>
      </div>
    </div>
  </div>
);

export default PageHeader;
