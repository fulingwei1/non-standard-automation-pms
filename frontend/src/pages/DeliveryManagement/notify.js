const getToastType = ({ title, variant } = {}) => {
  if (variant === "destructive" || title === "错误") return "error";
  if (variant === "warning" || title === "警告") return "warning";
  if (variant === "success" || title === "成功") return "success";
  return "info";
};

export const notifyDelivery = (toastApi, options = {}) => {
  if (typeof toastApi === "function") {
    toastApi(options);
    return;
  }

  const type = getToastType(options);
  const message = options.description || options.title || "";
  const sender = toastApi?.[type] || toastApi?.info || toastApi?.success;
  if (typeof sender === "function") {
    sender(message);
  }
};
