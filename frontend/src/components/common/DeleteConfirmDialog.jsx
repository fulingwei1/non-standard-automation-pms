/**
 * DeleteConfirmDialog - 通用删除确认对话框
 * 通用的删除确认警告对话框，可在不同业务模块中复用
 */

import React from "react";
import { AlertTriangle } from "lucide-react";
import {
 Dialog,
 DialogContent,
 DialogHeader,
 DialogTitle,
 DialogDescription,
  DialogFooter,
} from "../ui/dialog";
import { Button } from "../ui/button";

/**
 * @param {boolean} open - 对话框是否打开
 * @param {Function} onOpenChange - 对话框打开状态变化回调
 * @param {string} title - 标题，默认"确认删除"
 * @param {string} description - 描述文本
 * @param {React.ReactNode} children - 附加信息区域
 * @param {Function} onConfirm - 确认删除回调
 * @param {string} confirmText - 确认按钮文字，默认"确认删除"
 * @param {string} cancelText - 取消按钮文字，默认"取消"
 */
const DeleteConfirmDialog = ({
 open,
 onOpenChange,
 title = "确认删除",
 description = "此操作不可撤销，请谨慎操作",
 children,
 onConfirm,
 confirmText = "确认删除",
 cancelText = "取消",
}) => {
 const handleConfirm = () => {
 onConfirm?.();
  onOpenChange(false);
 };

 return (
 <Dialog open={open} onOpenChange={onOpenChange}>
 <DialogContent>
 <DialogHeader>
  <DialogTitle className="flex items-center gap-2">
  <AlertTriangle className="h-5 w-5 text-red-400" />
  {title}
    </DialogTitle>
  {description && (
  <DialogDescription>{description}</DialogDescription>
 )}
  </DialogHeader>

  {children && <div className="py-4">{children}</div>}

    <DialogFooter className="gap-2">
  <Button variant="outline" onClick={() => onOpenChange(false)}>
  {cancelText}
   </Button>
  <Button
  variant="destructive"
   onClick={handleConfirm}
   className="bg-red-500 hover:bg-red-600 text-white"
 >
  {confirmText}
  </Button>
 </DialogFooter>
  </DialogContent>
  </Dialog>
 );
};

export default DeleteConfirmDialog;
