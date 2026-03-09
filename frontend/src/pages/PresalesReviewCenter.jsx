import { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { PageHeader } from "../components/layout";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import RequirementSurvey from "./RequirementSurvey";
import SolutionList from "./SolutionList";
import PresalesTasks from "./PresalesTasks";

const TAB_SURVEYS = "surveys";
const TAB_SOLUTIONS = "solutions";
const TAB_REVIEWS = "reviews";

function getTabFromPath(pathname) {
  if (pathname.startsWith("/requirement-survey")) {
    return TAB_SURVEYS;
  }
  if (
    pathname.startsWith("/presales/technical-solutions") ||
    pathname.startsWith("/presales/solutions") ||
    pathname.startsWith("/solutions")
  ) {
    return TAB_SOLUTIONS;
  }
  return TAB_REVIEWS;
}

function getTabFromSearch(searchParams) {
  const tab = searchParams.get("tab");
  if (tab === TAB_SURVEYS || tab === TAB_SOLUTIONS || tab === TAB_REVIEWS) {
    return tab;
  }
  return null;
}

export default function PresalesReviewCenter() {
  const location = useLocation();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const isUnifiedRoute = location.pathname.startsWith("/presales/technical-solutions");
  const [activeTab, setActiveTab] = useState(
    getTabFromSearch(searchParams) || getTabFromPath(location.pathname),
  );

  useEffect(() => {
    setActiveTab(getTabFromSearch(searchParams) || getTabFromPath(location.pathname));
  }, [location.pathname, searchParams]);

  const tabs = useMemo(
    () => [
      { value: TAB_SURVEYS, label: "需求调研", path: "/requirement-survey" },
      { value: TAB_SOLUTIONS, label: "方案管理", path: "/presales/solutions" },
      { value: TAB_REVIEWS, label: "工单看板", path: "/presales-tasks" }
    ],
    []
  );

  const handleTabChange = (value) => {
    if (isUnifiedRoute) {
      setSearchParams({ tab: value });
      setActiveTab(value);
      return;
    }

    const target = (tabs || []).find((tab) => tab.value === value);
    if (target) {
      navigate(target.path);
      setActiveTab(value);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="技术方案"
        description="统一管理需求调研、方案内容与评审工单"
      />

      <Tabs value={activeTab || "unknown"} onValueChange={handleTabChange}>
        <TabsList className="grid w-full grid-cols-3">
          {(tabs || []).map((tab) => (
            <TabsTrigger key={tab.value} value={tab.value}>
              {tab.label}
            </TabsTrigger>
          ))}
        </TabsList>

        <TabsContent value={TAB_SURVEYS || "unknown"} className="space-y-6">
          <RequirementSurvey embedded />
        </TabsContent>

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
