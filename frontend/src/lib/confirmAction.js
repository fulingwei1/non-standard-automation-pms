import React from "react";
import { createRoot } from "react-dom/client";
import ConfirmDialog from "../components/common/ConfirmDialog";

const DESTRUCTIVE_KEYWORDS = ["删除", "移除", "清空", "不可撤销", "撤销", "注销", "禁用"];

const normalizeOptions = (options) => {
  if (typeof options === "string") {
    return { description: options };
  }
  return options || {};
};

const resolveVariant = (variant, description) => {
  if (variant) return variant;
  const text = description || "";
  const isDestructive = DESTRUCTIVE_KEYWORDS.some((keyword) => text.includes(keyword));
  return isDestructive ? "destructive" : "default";
};

export function confirmAction(options = {}) {
  const normalized = normalizeOptions(options);
  const {
    title = "请确认",
    description = "",
    confirmText = "确认",
    cancelText = "取消",
    icon,
    children,
    confirmDisabled = false,
    cancelDisabled = false,
    contentClassName = "",
    titleClassName = "",
    descriptionClassName = "",
    confirmButtonClassName = "",
    cancelButtonClassName = "",
  } = normalized;

  const variant = resolveVariant(normalized.variant, description);

  if (typeof document === "undefined") {
    return Promise.resolve(true);
  }

  return new Promise((resolve) => {
    const container = document.createElement("div");
    document.body.appendChild(container);
    const root = createRoot(container);

    const cleanup = (result) => {
      root.unmount();
      container.remove();
      resolve(result);
    };

    const handleOpenChange = (open) => {
      if (!open) {
        cleanup(false);
      }
    };

    const handleConfirm = () => {
      cleanup(true);
    };

    root.render(
      <ConfirmDialog
        open
        onOpenChange={handleOpenChange}
        onConfirm={handleConfirm}
        title={title}
        description={description}
        confirmText={confirmText}
        cancelText={cancelText}
        variant={variant}
        icon={icon}
        confirmDisabled={confirmDisabled}
        cancelDisabled={cancelDisabled}
        contentClassName={contentClassName}
        titleClassName={titleClassName}
        descriptionClassName={descriptionClassName}
        confirmButtonClassName={confirmButtonClassName}
        cancelButtonClassName={cancelButtonClassName}
      >
        {children}
      </ConfirmDialog>,
    );
  });
}
