
import { PROJECT_TABS } from "./constants";
import { useProjectDetail } from "./useProjectDetail";

export default function ProjectDetail() {
  const {
    navigate,
    loading,
    project,
    normalizedProject,
    stages,
    milestones,
    members,
    costs,
    documents,
    activeTab,
    setActiveTab,
    showAddMemberDialog,
    setShowAddMemberDialog,
    newMember,
    setNewMember,
    addingMember,
    availableUsers,
    loadingUsers,
    setShowEditDialog,
    fetchProjectData,
    handleOpenAddMember,
    handleAddMember,
    calculateProgress,
    calculateBudgetUtilization,
  } = useProjectDetail();

  if (loading) {
    return <SkeletonProjectDetail />;
  }

  if (!project) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">项目未找到</h3>
        <p className="text-gray-500 mb-4">请检查项目ID是否正确</p>
        <Button onClick={() => navigate("/projects")}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          返回项目列表
        </Button>
      </div>
    );
  }

  const p = normalizedProject;
  const progress = calculateProgress();
  const budgetUtilization = calculateBudgetUtilization(normalizedProject);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="space-y-6"
    >
      <PageHeader
        title={p.name}
        description={p.description}
        actions={
          <div className="flex space-x-2">
            <Button variant="outline" onClick={() => setShowEditDialog(true)}>
              <Edit2 className="mr-2 h-4 w-4" />
              编辑
            </Button>
            <Button variant="outline">
              <Share className="mr-2 h-4 w-4" />
              分享
            </Button>
            <Button variant="outline">
              <Download className="mr-2 h-4 w-4" />
              导出
            </Button>
          </div>
        }
      />

      {/* Tab 导航 */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-6 lg:w-[720px]">
          {PROJECT_TABS.map((tab) => {
            const Icon = tab.icon;
            return (
              <TabsTrigger key={tab.id} value={tab.id} className="flex items-center gap-2">
                <Icon className="h-4 w-4" />
                <span className="hidden sm:inline">{tab.label}</span>
              </TabsTrigger>
            );
          })}
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <OverviewTab
            project={project}
            normalizedProject={p}
            stages={stages}
            members={members}
            progress={progress}
            budgetUtilization={budgetUtilization}
            onOpenAddMember={handleOpenAddMember}
            onRefresh={fetchProjectData}
          />
        </TabsContent>

        <TabsContent value="tasks" className="space-y-6">
          <TasksTab />
        </TabsContent>

        <TabsContent value="milestones" className="space-y-6">
          <MilestonesTab milestones={milestones} />
        </TabsContent>

        <TabsContent value="gantt" className="space-y-6">
          <GanttTab stages={stages} />
        </TabsContent>

        <TabsContent value="budget" className="space-y-6">
          <BudgetTab
            normalizedProject={p}
            costs={costs}
            documents={documents}
            budgetUtilization={budgetUtilization}
            onOpenAddMember={handleOpenAddMember}
          />
        </TabsContent>

        <TabsContent value="profit" className="space-y-6">
          <ProfitTab projectId={project.id} />
        </TabsContent>
      </Tabs>

      {/* 添加成员对话框 */}
      <AddMemberDialog
        open={showAddMemberDialog}
        onOpenChange={setShowAddMemberDialog}
        availableUsers={availableUsers}
        loadingUsers={loadingUsers}
        newMember={newMember}
        setNewMember={setNewMember}
        addingMember={addingMember}
        onAdd={handleAddMember}
      />
    </motion.div>
  );
}
