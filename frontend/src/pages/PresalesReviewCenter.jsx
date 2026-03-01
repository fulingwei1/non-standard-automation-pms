import React, { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { PageHeader } from "../components/layout";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import SolutionList from "./SolutionList";
import PresalesTasks from "./PresalesTasks";

const TAB_SOLUTIONS = "solutions";
const TAB_REVIEWS = "reviews";

function getTabFromPath(pathname) {
  if (pathname.startsWith("/solutions")) {
    return TAB_SOLUTIONS;
  }
  return TAB_REVIEWS;
}

export default function PresalesReviewCenter() {
  const location = useLocation();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState(getTabFromPath(location.pathname));

  useEffect(() => {
    setActiveTab(getTabFromPath(location.pathname));
  }, [location.pathname]);

  const tabs = useMemo(
    () => [
      { value: TAB_SOLUTIONS, label: "方案中心", path: "/solutions" },
      { value: TAB_REVIEWS, label: "方案评审", path: "/presales-tasks" }
    ],
    []
  );

  const handleTabChange = (value) => {
    const target = (tabs || []).find((tab) => tab.value === value);
    if (target) {
      navigate(target.path);
      setActiveTab(value);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="方案评审"
        description="统一查看方案中心与方案评审"
      />

      <Tabs value={activeTab || "unknown"} onValueChange={handleTabChange}>
        <TabsList className="grid w-full grid-cols-2">
          {(tabs || []).map((tab) => (
            <TabsTrigger key={tab.value} value={tab.value}>
              {tab.label}
            </TabsTrigger>
          ))}
        </TabsList>

        <TabsContent value={TAB_SOLUTIONS || "unknown"} className="space-y-6">
          <SolutionList embedded />
        </TabsContent>

        <TabsContent value={TAB_REVIEWS || "unknown"} className="space-y-6">
          <PresalesTasks embedded />
        </TabsContent>
      </Tabs>
    </div>
  );
}
