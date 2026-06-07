import { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { PageHeader } from "../components/layout";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import RequirementSurvey from "./RequirementSurvey";
import PresaleProposals from "./PresaleProposals";
import PresalesTasks from "./PresalesTasks";
import TechnicalParameterManagement from "./TechnicalParameterManagement";
import PresalesCostEstimation from "./PresalesCostEstimation";
import BiddingCenter from "./BiddingCenter";
import PresaleTemplates from "./PresaleTemplates";

const TAB_SURVEYS = "surveys";
const TAB_SOLUTIONS = "solutions";
const TAB_PARAMETERS = "parameters";
const TAB_COST = "cost";
const TAB_BIDS = "bids";
const TAB_KNOWLEDGE = "knowledge";
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
  if (pathname.startsWith("/presales/cost-estimation")) {
    return TAB_COST;
  }
  if (pathname.startsWith("/bidding") || pathname.startsWith("/presales/bids")) {
    return TAB_BIDS;
  }
  if (pathname.startsWith("/presales/templates") || pathname.startsWith("/presale-templates")) {
    return TAB_KNOWLEDGE;
  }
  return TAB_REVIEWS;
}

function getTabFromSearch(searchParams) {
  const tab = searchParams.get("tab");
  if (
    tab === TAB_SURVEYS ||
    tab === TAB_SOLUTIONS ||
    tab === TAB_PARAMETERS ||
    tab === TAB_COST ||
    tab === TAB_BIDS ||
    tab === TAB_KNOWLEDGE ||
    tab === TAB_REVIEWS
  ) {
    return tab;
  }
  return null;
}

function buildUnifiedTabPath(tab, searchParams) {
  const nextParams = new URLSearchParams(searchParams);
  nextParams.set("tab", tab);
  return `/presales/technical-solutions?${nextParams.toString()}`;
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
      { value: TAB_SURVEYS, label: "需求调研", path: "/presales/technical-solutions?tab=surveys" },
      { value: TAB_SOLUTIONS, label: "方案管理", path: "/presales/technical-solutions?tab=solutions" },
      { value: TAB_PARAMETERS, label: "技术参数", path: "/presales/technical-solutions?tab=parameters" },
      { value: TAB_COST, label: "成本估算", path: "/presales/technical-solutions?tab=cost" },
      { value: TAB_BIDS, label: "投标支持", path: "/presales/technical-solutions?tab=bids" },
      { value: TAB_KNOWLEDGE, label: "知识模板", path: "/presales/technical-solutions?tab=knowledge" },
      { value: TAB_REVIEWS, label: "工单看板", path: "/presales/technical-solutions?tab=reviews" }
    ],
    []
  );

  const handleTabChange = (value) => {
    if (isUnifiedRoute) {
      const nextParams = new URLSearchParams(searchParams);
      nextParams.set("tab", value);
      setSearchParams(nextParams);
      setActiveTab(value);
      return;
    }

    navigate(buildUnifiedTabPath(value, searchParams));
    setActiveTab(value);
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="售前技术支持中心"
        description="统一处理需求调研、技术方案、参数模板、成本估算、投标支持、知识模板与评审工单。"
      />

      <Tabs value={activeTab || "unknown"} onValueChange={handleTabChange}>
        <TabsList className="grid w-full grid-cols-2 md:grid-cols-4 xl:grid-cols-7">
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
          <PresaleProposals embedded />
        </TabsContent>

        <TabsContent value={TAB_PARAMETERS || "unknown"} className="space-y-6">
          <TechnicalParameterManagement embedded />
        </TabsContent>

        <TabsContent value={TAB_COST || "unknown"} className="space-y-6">
          <PresalesCostEstimation embedded />
        </TabsContent>

        <TabsContent value={TAB_BIDS || "unknown"} className="space-y-6">
          <BiddingCenter embedded />
        </TabsContent>

        <TabsContent value={TAB_KNOWLEDGE || "unknown"} className="space-y-6">
          <PresaleTemplates embedded />
        </TabsContent>

        <TabsContent value={TAB_REVIEWS || "unknown"} className="space-y-6">
          <PresalesTasks embedded />
        </TabsContent>
      </Tabs>
    </div>
  );
}
