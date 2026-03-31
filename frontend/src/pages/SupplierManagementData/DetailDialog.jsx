import { Button } from "../../components/ui/button";
import { Badge } from "../../components/ui/badge";
import { Label } from "../../components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "../../components/ui/dialog";
import { cn } from "../../lib/utils";
import { getLevelColor, getStatusBadgeClass, getStatusLabel } from "./utils";

export default function DetailDialog({ open, onOpenChange, supplier }) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px] bg-slate-900 border-slate-700">
        <DialogHeader>
          <DialogTitle className="text-slate-200">供应商详情</DialogTitle>
        </DialogHeader>
        {supplier && (
          <div className="grid gap-4 py-4 text-sm">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-slate-400">供应商编码</Label>
                <p className="font-medium font-mono text-slate-200">
                  {supplier.supplier_code}
                </p>
              </div>
              <div>
                <Label className="text-slate-400">供应商名称</Label>
                <p className="font-medium text-slate-200">
                  {supplier.supplier_name}
                </p>
              </div>
              <div>
                <Label className="text-slate-400">类型</Label>
                <p className="font-medium text-slate-200">
                  {supplier.supplier_type || "-"}
                </p>
              </div>
              <div>
                <Label className="text-slate-400">等级</Label>
                <p className="font-medium">
                  {supplier.supplier_level && (
                    <Badge
                      className={cn(
                        "text-white",
                        getLevelColor(supplier.supplier_level)
                      )}
                    >
                      {supplier.supplier_level}级
                    </Badge>
                  )}
                </p>
              </div>
              <div>
                <Label className="text-slate-400">综合评分</Label>
                <p className="font-medium text-slate-200">
                  {supplier.overall_rating
                    ? `${parseFloat(supplier.overall_rating).toFixed(1)} / 5.0`
                    : "-"}
                </p>
              </div>
              <div>
                <Label className="text-slate-400">状态</Label>
                <p className="font-medium">
                  <Badge className={getStatusBadgeClass(supplier.status)}>
                    {getStatusLabel(supplier.status)}
                  </Badge>
                </p>
              </div>
              {supplier.contact_person && (
                <div>
                  <Label className="text-slate-400">联系人</Label>
                  <p className="font-medium text-slate-200">
                    {supplier.contact_person}
                  </p>
                </div>
              )}
              {supplier.contact_phone && (
                <div>
                  <Label className="text-slate-400">联系电话</Label>
                  <p className="font-medium text-slate-200">
                    {supplier.contact_phone}
                  </p>
                </div>
              )}
              {supplier.contact_email && (
                <div>
                  <Label className="text-slate-400">邮箱</Label>
                  <p className="font-medium text-slate-200">
                    {supplier.contact_email}
                  </p>
                </div>
              )}
              {supplier.address && (
                <div>
                  <Label className="text-slate-400">地址</Label>
                  <p className="font-medium text-slate-200">
                    {supplier.address}
                  </p>
                </div>
              )}
            </div>
          </div>
        )}
        <DialogFooter>
          <Button
            onClick={() => onOpenChange(false)}
            className="bg-slate-800 hover:bg-slate-700 text-slate-200"
          >
            关闭
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
