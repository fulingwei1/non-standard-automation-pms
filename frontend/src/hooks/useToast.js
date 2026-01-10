import { useState, useCallback } from "react";

export function useToast() {
  const [toasts, setToasts] = useState([]);

  const toast = useCallback(({ title, description, variant = "default" }) => {
    const id = Date.now();
    const newToast = {
      id,
      title,
      description,
      variant,
    };

    setToasts((prev) => [...prev, newToast]);

    // 自动移除
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 3000);

    // 简单的浏览器 alert 作为降级方案
    if (variant === "destructive") {
      alert(`${title}: ${description}`);
    } else {
      console.log(`${title}: ${description}`);
    }
  }, []);

  return { toast, toasts };
}
