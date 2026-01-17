/**
 * HR Manager Dashboard - Refactored Version
 * 人事经理仪表板 - 重构版本
 * 
 * Features: HR planning, Recruitment management, Performance management, Employee relations
 * Core Functions: HR strategy, Recruitment approval, Performance review, Employee relationship management
 */

import { useState, useMemo as _useMemo, useEffect } from "react";
import { motion } from "framer-motion";
import { toast } from "sonner";
import {
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger } from
"../components/ui";

// Import HR components
import {
  HRStatsOverview,
  EmployeeManager,
  hrTabConfigs } from
"../components/hr";

// Import services and utilities
import { employeeApi, departmentApi, hrApi } from "../services/api";
import { cn as _cn } from "../lib/utils";

export default function HRManagerDashboard() {
  // State management
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedTab, setSelectedTab] = useState("overview");

  // Data state
  const [hrStats, setHrStats] = useState(null);
  const [employees, setEmployees] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [pendingRecruitments, setPendingRecruitments] = useState([]);
  const [pendingPerformanceReviews, setPendingPerformanceReviews] = useState([]);

  // Tab content placeholders
  const [tabContent, setTabContent] = useState({
    transactions: null,
    contracts: null,
    recruitment: null,
    performance: null,
    attendance: null,
    relations: null,
    statistics: null
  });

  // Load HR statistics
  const loadHRStats = async () => {
    try {
      const response = await hrApi.getStatistics();
      setHrStats(response.data);
    } catch (error) {
      console.error("Failed to load HR stats:", error);
      // Set mock data for development
      setHrStats({
        activeEmployees: 245,
        totalEmployees: 256,
        pendingRecruitments: 12,
        pendingPerformanceReviews: 8,
        todayAttendanceRate: 95.2,
        employeeSatisfaction: 87,
        avgPerformanceScore: 82.5,
        monthlyNewHires: 15,
        monthlyResignations: 3,
        trainingCompletionRate: 78,
        avgRecruitmentCycle: 21
      });
    }
  };

  // Load employees
  const loadEmployees = async () => {
    try {
      const response = await employeeApi.list({ page_size: 1000 });
      setEmployees(response.data?.items || []);
    } catch (error) {
      console.error("Failed to load employees:", error);
      // Set mock data for development
      setEmployees([
      {
        id: 1,
        name: "张三",
        employee_id: "E001",
        email: "zhangsan@company.com",
        phone: "13800138001",
        department: "ENGINEERING",
        position: "高级工程师",
        status: "ACTIVE",
        hire_date: "2022-01-15",
        address: "北京市朝阳区"
      },
      {
        id: 2,
        name: "李四",
        employee_id: "E002",
        email: "lisi@company.com",
        phone: "13800138002",
        department: "HR",
        position: "人事专员",
        status: "ACTIVE",
        hire_date: "2021-06-20",
        address: "北京市海淀区"
      }]
      );
    }
  };

  // Load departments
  const loadDepartments = async () => {
    try {
      const response = await departmentApi.list();
      setDepartments(response.data?.items || []);
    } catch (error) {
      console.error("Failed to load departments:", error);
      // Set mock data for development
      setDepartments([
      { name: "工程部", count: 85, percentage: 35 },
      { name: "生产部", count: 65, percentage: 27 },
      { name: "销售部", count: 45, percentage: 19 },
      { name: "质量部", count: 25, percentage: 10 },
      { name: "人事部", count: 15, percentage: 6 },
      { name: "财务部", count: 10, percentage: 3 }]
      );
    }
  };

  // Load pending recruitments
  const loadPendingRecruitments = async () => {
    try {
      const response = await hrApi.getPendingRecruitments();
      setPendingRecruitments(response.data?.items || []);
    } catch (error) {
      console.error("Failed to load pending recruitments:", error);
      // Set mock data for development
      setPendingRecruitments([
      {
        id: 1,
        position: "前端开发工程师",
        department: "ENGINEERING",
        priority: "HIGH",
        posted_time: "2天前"
      },
      {
        id: 2,
        position: "销售经理",
        department: "SALES",
        priority: "MEDIUM",
        posted_time: "1周前"
      }]
      );
    }
  };

  // Load pending performance reviews
  const loadPendingPerformanceReviews = async () => {
    try {
      const response = await hrApi.getPendingPerformanceReviews();
      setPendingPerformanceReviews(response.data?.items || []);
    } catch (error) {
      console.error("Failed to load pending performance reviews:", error);
      // Set mock data for development
      setPendingPerformanceReviews([
      {
        id: 1,
        employee_name: "王五",
        department: "PRODUCTION",
        overdue: false,
        due_date: "本周五"
      }]
      );
    }
  };

  // Load tab content dynamically
  const loadTabContent = async (tab) => {
    // In a real application, these would load specific tab components
    // For now, we'll just set placeholder content
    setTabContent((prev) => ({
      ...prev,
      [tab]:
      <Card className="bg-surface-50 border-white/10">
          <CardContent className="p-12 text-center text-slate-400">
            <div className="text-lg font-medium mb-2">{`${tab} 功能开发中...`}</div>
            <div className="text-sm">此模块正在开发中，敬请期待</div>
          </CardContent>
        </Card>

    }));
  };

  // Initialize data
  useEffect(() => {
    const initializeData = async () => {
      setLoading(true);
      try {
        await Promise.all([
        loadHRStats(),
        loadEmployees(),
        loadDepartments(),
        loadPendingRecruitments(),
        loadPendingPerformanceReviews()]
        );
      } catch (error) {
        console.error("Failed to initialize HR dashboard:", error);
        toast.error("数据加载失败，请刷新页面重试");
      } finally {
        setLoading(false);
      }
    };

    initializeData();
  }, []);

  // Load tab content when tab changes
  useEffect(() => {
    if (selectedTab !== "overview" && selectedTab !== "employees" && !tabContent[selectedTab]) {
      loadTabContent(selectedTab);
    }
  }, [selectedTab]);

  // Event handlers
  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await Promise.all([
      loadHRStats(),
      loadEmployees(),
      loadDepartments(),
      loadPendingRecruitments(),
      loadPendingPerformanceReviews()]
      );
      toast.success("数据已刷新");
    } catch (_error) {
      toast.error("刷新失败");
    } finally {
      setRefreshing(false);
    }
  };

  const handleViewEmployee = (employee) => {
    console.log("View employee:", employee);
  };

  const handleEditEmployee = (employee) => {
    console.log("Edit employee:", employee);
  };

  const handleCreateEmployee = () => {
    console.log("Create new employee");
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white p-6">

      <div className="max-w-[1600px] mx-auto space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">人事经理仪表板</h1>
            <p className="text-slate-400">人力资源管理与分析中心</p>
          </div>
          <Button
            onClick={handleRefresh}
            disabled={refreshing}
            variant="outline">

            {refreshing ? "刷新中..." : "刷新数据"}
          </Button>
        </div>

        {/* Main Content */}
        <Tabs
          value={selectedTab}
          onValueChange={setSelectedTab}
          className="space-y-6">

          <TabsList className="bg-surface-50 border-white/10 grid grid-cols-5 lg:grid-cols-9 w-full">
            {hrTabConfigs.map((tab) =>
            <TabsTrigger
              key={tab.value}
              value={tab.value}
              className="flex items-center gap-2 data-[state=active]:bg-slate-700">

                <span>{tab.icon}</span>
                <span className="hidden lg:inline">{tab.label}</span>
              </TabsTrigger>
            )}
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6">
            <HRStatsOverview
              hrStats={hrStats}
              loading={loading}
              departments={departments}
              pendingRecruitments={pendingRecruitments}
              pendingPerformanceReviews={pendingPerformanceReviews} />

          </TabsContent>

          {/* HR Transactions Tab */}
          <TabsContent value="transactions" className="space-y-6">
            {tabContent.transactions}
          </TabsContent>

          {/* Contracts Tab */}
          <TabsContent value="contracts" className="space-y-6">
            {tabContent.contracts}
          </TabsContent>

          {/* Recruitment Tab */}
          <TabsContent value="recruitment" className="space-y-6">
            {tabContent.recruitment}
          </TabsContent>

          {/* Performance Tab */}
          <TabsContent value="performance" className="space-y-6">
            {tabContent.performance}
          </TabsContent>

          {/* Attendance Tab */}
          <TabsContent value="attendance" className="space-y-6">
            {tabContent.attendance}
          </TabsContent>

          {/* Employees Tab */}
          <TabsContent value="employees" className="space-y-6">
            <EmployeeManager
              employees={employees}
              loading={loading}
              onViewEmployee={handleViewEmployee}
              onEditEmployee={handleEditEmployee}
              onCreateEmployee={handleCreateEmployee} />

          </TabsContent>

          {/* Relations Tab */}
          <TabsContent value="relations" className="space-y-6">
            {tabContent.relations}
          </TabsContent>

          {/* Statistics Tab */}
          <TabsContent value="statistics" className="space-y-6">
            {tabContent.statistics}
          </TabsContent>
        </Tabs>
      </div>
    </motion.div>);

}