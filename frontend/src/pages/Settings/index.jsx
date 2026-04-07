import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { fadeIn, staggerContainer } from "../../lib/animations";


export default function Settings() {
  const navigate = useNavigate();
  // Get section from URL query parameter
  const urlParams = new URLSearchParams(window.location.search);
  const sectionFromUrl = urlParams.get("section");

  // Redirect knowledge section to knowledge-base page
  useEffect(() => {
    if (sectionFromUrl === "knowledge") {
      navigate("/knowledge-base", { replace: true });
    }
  }, [sectionFromUrl, navigate]);

  const [activeSection, setActiveSection] = useState(
    sectionFromUrl || "profile",
  );

  // Update active section when URL changes
  useEffect(() => {
    const handleLocationChange = () => {
      const urlParams = new URLSearchParams(window.location.search);
      const sectionFromUrl = urlParams.get("section");
      if (sectionFromUrl && sectionFromUrl !== activeSection) {
        setActiveSection(sectionFromUrl);
      }
    };

    // Check on mount and when location changes
    handleLocationChange();

    // Listen for popstate events (back/forward navigation)
    window.addEventListener("popstate", handleLocationChange);

    return () => {
      window.removeEventListener("popstate", handleLocationChange);
    };
  }, [activeSection]);

  const renderSection = () => {
    switch (activeSection) {
      case "profile":
        return <ProfileSection />;
      case "notifications":
        return <NotificationsSection />;
      case "security":
        return <SecuritySection />;
      case "appearance":
        return <AppearanceSection />;
      case "language":
        return <LanguageSection />;
      default:
        return <ProfileSection />;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="container mx-auto px-4 py-6">
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="space-y-6"
        >
          <PageHeader title="个人设置" description="管理您的账户设置和偏好" />

          <motion.div
            variants={fadeIn}
            className="flex flex-col lg:flex-row gap-6"
          >
            {/* Sidebar Navigation */}
            <SettingsSidebar
              activeSection={activeSection}
              onSectionChange={setActiveSection}
            />

            {/* Content Area */}
            <div className="flex-1 min-w-0">{renderSection()}</div>
          </motion.div>
        </motion.div>
      </div>
    </div>
  );
}
