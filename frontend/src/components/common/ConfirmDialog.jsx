/**
 * ConfirmDialog - 通用确认对话框
 * 用于非删除类操作的确认提示（可通过 variant 切换样式）
 */

import React from "react";
import { AlertTriangle, HelpCircle } from "lucide-react";
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
 * @param {string} title - 标题，默认"请确认"
 * @param {string} description - 描述文本
 * @param {React.ReactNode} children - 附加信息区域
 * @param {Function} onConfirm - 确认回调
 * @param {string} confirmText - 确认按钮文字，默认"确认"
 * @param {string} cancelText - 取消按钮文字，默认"取消"
 * @param {"default"|"destructive"} variant - 样式变体
 * @param {React.ComponentType} icon - 自定义图标组件
 * @param {boolean} confirmDisabled - 确认按钮禁用
 * @param {boolean} cancelDisabled - 取消按钮禁用
 * @param {string} contentClassName - DialogContent 额外样式
 * @param {string} titleClassName - 标题额外样式
 * @param {string} descriptionClassName - 描述额外样式
 * @param {string} confirmButtonClassName - 确认按钮额外样式
 * @param {string} cancelButtonClassName - 取消按钮额外样式
 */
const ConfirmDialog = ({
  open,
  onOpenChange,
  title = "请确认",
  description = "",
  children,
  onConfirm,
  confirmText = "确认",
  cancelText = "取消",
  variant = "default",
  icon: Icon,
  confirmDisabled = false,
  cancelDisabled = false,
  contentClassName = "",
  titleClassName = "",
  descriptionClassName = "",
  confirmButtonClassName = "",
  cancelButtonClassName = "",
}) => {
  const IconComponent = Icon || (variant === "destructive" ? AlertTriangle : HelpCircle);
  const iconClassName = variant === "destructive" ? "text-red-400" : "text-slate-400";
  const confirmVariant = variant === "destructive" ? "destructive" : "default";

  const handleConfirm = () => {
    onConfirm?.();
    onOpenChange?.(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className={contentClassName || undefined}>
        <DialogHeader>
          <DialogTitle className={["flex items-center gap-2", titleClassName].filter(Boolean).join(" ")}>
            {IconComponent && <IconComponent className={`h-5 w-5 ${iconClassName}`} />}
            {title}
          </DialogTitle>
          {description && (
            <DialogDescription className={descriptionClassName || undefined}>
              {description}
            </DialogDescription>
          )}
        </DialogHeader>

        {children && <div className="py-4">{children}</div>}

        <DialogFooter className="gap-2">
          <Button
            variant="outline"
            onClick={() => onOpenChange?.(false)}
            disabled={cancelDisabled}
            className={cancelButtonClassName || undefined}
          >
            {cancelText}
          </Button>
          <Button
            variant={confirmVariant}
            onClick={handleConfirm}
            disabled={confirmDisabled}
            className={confirmButtonClassName || undefined}
          >
            {confirmText}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default ConfirmDialog;
