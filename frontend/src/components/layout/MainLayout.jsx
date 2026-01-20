import { useState, useEffect } from "react";
import { AnimatePresence } from "framer-motion";
import { cn } from "../../lib/utils";
import { Sidebar } from "./Sidebar";
import { Header } from "./Header";
import { ToastContainer, useToast } from "../ui";

/**
 * 主布局组件
 */
export function MainLayout({ children, onLogout }) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const { toasts, removeToast } = useToast();
  // Get user from localStorage
  const [user, setUser] = useState(() => {
    try {
      const userStr = localStorage.getItem("user");
      if (userStr) {
        return JSON.parse(userStr);
      }
    } catch (e) {
      console.warn("Failed to parse user from localStorage:", e);
    }
    return null;
  });

  // Update user when localStorage changes
  useEffect(() => {
    const handleStorageChange = () => {
      try {
        const userStr = localStorage.getItem("user");
        if (userStr) {
          setUser(JSON.parse(userStr));
        } else {
          setUser(null);
        }
      } catch (e) {
        console.warn("Failed to parse user from localStorage:", e);
        setUser(null);
      }
    };

    // Listen for storage events (from other tabs)
    window.addEventListener("storage", handleStorageChange);

    // Also check on mount
    handleStorageChange();

    return () => {
      window.removeEventListener("storage", handleStorageChange);
    };
  }, []);

  return (
    <div className="min-h-screen bg-surface-0">
      <ToastContainer toasts={toasts} onClose={removeToast} />
      {/* Sidebar */}
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
        onLogout={onLogout}
      />

      {/* Header */}
      <Header
        sidebarCollapsed={sidebarCollapsed}
        user={user}
        onLogout={onLogout}
      />

      {/* Main Content */}
      <main
        className={cn(
          "pt-16 min-h-screen transition-all duration-300",
          sidebarCollapsed ? "pl-[72px]" : "pl-60",
        )}
      >
        <div className="p-6">
          <AnimatePresence mode="wait">{children}</AnimatePresence>
        </div>
      </main>
    </div>
  );
}
