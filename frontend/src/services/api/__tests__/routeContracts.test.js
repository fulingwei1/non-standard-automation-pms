import { describe, expect, it, beforeEach, afterEach } from "vitest";
import { setupApiTest, teardownApiTest } from "./_test-setup.js";

describe("frontend API route contracts", () => {
  let mock;

  beforeEach(async () => {
    const setup = await setupApiTest();
    mock = setup.mock;
  });

  afterEach(() => {
    teardownApiTest(mock);
  });

  it("uses the production-prefixed material requisition routes registered by the backend", async () => {
    const { productionApi } = await import("../production.js");
    mock.onGet("/api/v1/production/material-requisitions").reply(200, {
      items: [],
      total: 0,
      page: 1,
      page_size: 20,
    });

    await productionApi.materialRequisitions.list({ page: 1, page_size: 20 });

    expect(mock.history.get[0].url).toBe("/production/material-requisitions");
    expect(mock.history.get[0].params).toEqual({ page: 1, page_size: 20 });
  });

  it("uses the business-support-orders delivery routes registered by the backend", async () => {
    const { businessSupportApi } = await import("../businessSupport.js");
    mock.onGet("/api/v1/business-support-orders/delivery-orders").reply(200, {
      code: 200,
      data: { items: [], total: 0 },
    });
    mock.onGet("/api/v1/business-support-orders/delivery-orders/statistics").reply(200, {
      code: 200,
      data: { total_orders: 0 },
    });

    await businessSupportApi.deliveryOrders.list({ page: 1 });
    await businessSupportApi.deliveryOrders.statistics();

    expect(mock.history.get[0].url).toBe("/business-support-orders/delivery-orders");
    expect(mock.history.get[1].url).toBe("/business-support-orders/delivery-orders/statistics");
  });

  it("uses non-redirecting performance contract routes", async () => {
    const { performanceContractApi } = await import("../performanceContract.js");
    mock.onGet("/api/v1/performance-contract").reply(200, {
      code: 200,
      data: { items: [], total: 0 },
    });
    mock.onPost("/api/v1/performance-contract").reply(200, {
      code: 200,
      data: { id: 1 },
    });

    await performanceContractApi.list({ page: 1 });
    await performanceContractApi.create({ user_id: 1 });

    expect(mock.history.get[0].url).toBe("/performance-contract");
    expect(mock.history.post[0].url).toBe("/performance-contract");
  });

  it("uses role and permission workflow routes with backend-compatible payloads", async () => {
    const { roleApi, permissionApi, userApi } = await import("../auth.js");
    mock.onPut("/api/v1/roles/7/nav-groups").reply(200, { code: 200, data: [] });
    mock.onPost("/api/v1/roles/compare").reply(200, { code: 200, data: {} });
    mock.onPut("/api/v1/roles/7/permissions").reply(200, { code: 200, data: {} });
    mock.onGet("/api/v1/permissions/roles/7").reply(200, { code: 200, data: {} });
    mock.onPut("/api/v1/users/9/roles").reply(200, { code: 200, data: null });

    await roleApi.updateNavGroups(7, [{ key: "system" }]);
    await roleApi.compare([7, 8]);
    await roleApi.assignPermissions(7, [1, 2]);
    await permissionApi.getByRole(7);
    await userApi.assignRoles(9, [7]);

    expect(mock.history.put[0].url).toBe("/roles/7/nav-groups");
    expect(JSON.parse(mock.history.put[0].data)).toEqual([{ key: "system" }]);
    expect(mock.history.post[0].url).toBe("/roles/compare");
    expect(JSON.parse(mock.history.post[0].data)).toEqual([7, 8]);
    expect(mock.history.put[1].url).toBe("/roles/7/permissions");
    expect(JSON.parse(mock.history.put[1].data)).toEqual({ permission_ids: [1, 2] });
    expect(mock.history.get[0].url).toBe("/permissions/roles/7");
    expect(mock.history.get[0].params).toEqual({ include_inherited: true });
    expect(mock.history.put[2].url).toBe("/users/9/roles");
    expect(JSON.parse(mock.history.put[2].data)).toEqual({ role_ids: [7] });
  });

  it("uses lightweight user options for assignment dropdowns instead of the user management list", async () => {
    const { userApi } = await import("../auth.js");
    mock.onGet("/api/v1/users/options").reply(200, {
      items: [],
      total: 0,
      page: 1,
      page_size: 100,
    });

    await userApi.options({ page: 1, page_size: 100, is_active: true });

    expect(mock.history.get[0].url).toBe("/users/options");
    expect(mock.history.get[0].params).toEqual({ page: 1, page_size: 100, is_active: true });
  });

  it("uses role template workflow routes registered by the backend", async () => {
    const { roleApi } = await import("../auth.js");
    mock.onGet("/api/v1/roles/templates").reply(200, { code: 200, data: [] });
    mock.onGet("/api/v1/roles/templates/3").reply(200, { code: 200, data: {} });
    mock.onPost("/api/v1/roles/templates/").reply(201, { code: 201, data: { id: 3 } });
    mock.onPut("/api/v1/roles/templates/3").reply(200, { code: 200, data: { id: 3 } });
    mock.onDelete("/api/v1/roles/templates/3").reply(200, { code: 200, data: { id: 3 } });
    mock
      .onPost("/api/v1/roles/templates/3/create-role")
      .reply(201, { code: 201, data: { id: 8 } });
    mock
      .onPost("/api/v1/roles/7/save-as-template")
      .reply(201, { code: 201, data: { id: 4 } });

    await roleApi.listTemplates({ is_active: true });
    await roleApi.getTemplate(3);
    await roleApi.createTemplate({ template_code: "QA", template_name: "模板" });
    await roleApi.updateTemplate(3, { template_name: "模板2" });
    await roleApi.deleteTemplate(3);
    await roleApi.createFromTemplate(3, { role_code: "QA_ROLE", role_name: "角色" });
    await roleApi.saveAsTemplate(7, { template_code: "QA_SAVE", template_name: "另存模板" });

    expect(mock.history.get[0].url).toBe("/roles/templates");
    expect(mock.history.get[0].params).toEqual({ is_active: true });
    expect(mock.history.get[1].url).toBe("/roles/templates/3");
    expect(mock.history.post[0].url).toBe("/roles/templates/");
    expect(JSON.parse(mock.history.post[0].data)).toEqual({
      template_code: "QA",
      template_name: "模板",
    });
    expect(mock.history.put[0].url).toBe("/roles/templates/3");
    expect(JSON.parse(mock.history.put[0].data)).toEqual({ template_name: "模板2" });
    expect(mock.history.delete[0].url).toBe("/roles/templates/3");
    expect(mock.history.post[1].url).toBe("/roles/templates/3/create-role");
    expect(JSON.parse(mock.history.post[1].data)).toEqual({
      role_code: "QA_ROLE",
      role_name: "角色",
    });
    expect(mock.history.post[2].url).toBe("/roles/7/save-as-template");
    expect(JSON.parse(mock.history.post[2].data)).toEqual({
      template_code: "QA_SAVE",
      template_name: "另存模板",
    });
  });

  it("uses report and payment routes registered by the backend", async () => {
    const { reportCenterApi } = await import("../admin.js");
    const { paymentApi } = await import("../sales.js");
    mock.onGet("/api/v1/report/archives").reply(200, {
      code: 200,
      data: { items: [], total: 0 },
    });
    mock.onGet("/api/v1/report/archives/1/download").reply(200, {});
    mock.onGet("/api/v1/sales/payments/records").reply(200, {
      items: [],
      total: 0,
    });

    await reportCenterApi.getArchives({ page: 1 });
    await reportCenterApi.downloadArchive(1);
    await paymentApi.list({ page: 1 });

    expect(mock.history.get[0].url).toBe("/report/archives");
    expect(mock.history.get[1].url).toBe("/report/archives/1/download");
    expect(mock.history.get[2].url).toBe("/sales/payments/records");
  });

  it("uses production routes registered under the production prefix", async () => {
    const { productionApi, materialDemandApi } = await import("../production.js");
    mock.onGet("/api/v1/production/workers").reply(200, { items: [], total: 0 });
    mock.onGet("/api/v1/production/exceptions").reply(200, { items: [], total: 0 });
    mock.onGet("/api/v1/material-demands/").reply(200, { items: [], total: 0 });

    await productionApi.workers.list({ page_size: 1000 });
    await productionApi.exceptions.list({ page: 1 });
    await materialDemandApi.list({ page: 1 });

    expect(mock.history.get[0].url).toBe("/production/workers");
    expect(mock.history.get[1].url).toBe("/production/exceptions");
    expect(mock.history.get[2].url).toBe("/material-demands/");
  });

  it("uses shortage detection summary route registered by the backend", async () => {
    const { shortageAlertApi } = await import("../production.js");
    mock.onGet("/api/v1/shortage/detection/alerts/summary").reply(200, {
      code: 200,
      data: {
        pending_count: 0,
        processing_count: 0,
        resolved_count: 0,
        total_count: 0,
      },
    });

    await shortageAlertApi.getSummary();

    expect(mock.history.get[0].url).toBe("/shortage/detection/alerts/summary");
  });

  it("uses timesheet routes registered under the timesheet prefix", async () => {
    const { timesheetApi } = await import("../hr.js");
    mock.onGet("/api/v1/timesheet/records").reply(200, {
      items: [],
      total: 0,
    });
    mock.onGet("/api/v1/timesheet/anomalies").reply(200, {
      code: 200,
      data: [],
    });

    await timesheetApi.list({ status: "PENDING" });
    await timesheetApi.detectAnomalies({ start_date: "2026-06-01" });

    expect(mock.history.get[0].url).toBe("/timesheet/records");
    expect(mock.history.get[1].url).toBe("/timesheet/anomalies");
  });

  it("uses template config and workload compatibility routes registered by the backend", async () => {
    const { templateConfigApi } = await import("../templateConfig.js");
    const { workloadApi } = await import("../workload.js");
    mock.onGet("/api/v1/template-configs/configs").reply(200, {
      items: [],
      total: 0,
    });
    mock.onGet("/api/v1/workload/dashboard").reply(200, {
      summary: { total_users: 0 },
      team_workload: [],
    });
    mock.onGet("/api/v1/workload/team").reply(200, { items: [] });

    await templateConfigApi.list({ page: 1 });
    await workloadApi.dashboard({ start_date: "2026-06-01" });
    await workloadApi.team({ start_date: "2026-06-01" });

    expect(mock.history.get[0].url).toBe("/template-configs/configs");
    expect(mock.history.get[1].url).toBe("/workload/dashboard");
    expect(mock.history.get[2].url).toBe("/workload/team");
  });

  it("uses assembly-kit routes registered by the backend", async () => {
    const { assemblyKitApi, kitCheckApi } = await import("../production.js");
    mock.onGet("/api/v1/assembly-kit/dashboard").reply(200, { data: {} });
    mock.onGet("/api/v1/assembly-kit/stages").reply(200, { data: [] });
    mock.onGet("/api/v1/assembly-kit/shortage-alerts").reply(200, {
      data: { items: [] },
    });
    mock.onGet("/api/v1/assembly-kit/templates").reply(200, { data: [] });
    mock.onPost("/api/v1/assembly-kit/scheduling/suggestions/generate").reply(200, {
      data: { suggestions: [] },
    });
    mock.onGet("/api/v1/assembly-kit/scheduling/suggestions").reply(200, {
      data: { items: [] },
    });
    mock.onPost("/api/v1/assembly-kit/scheduling/suggestions/7/accept").reply(200, {
      data: {},
    });
    mock.onPost("/api/v1/assembly-kit/scheduling/suggestions/7/reject").reply(200, {
      data: {},
    });
    mock.onGet("/api/v1/kit-check/work-orders").reply(200, {
      code: 200,
      data: { work_orders: [] },
    });

    await assemblyKitApi.dashboard();
    await assemblyKitApi.getStages();
    await assemblyKitApi.getShortageAlerts({ page_size: 20 });
    await assemblyKitApi.getTemplates();
    await assemblyKitApi.generateSuggestions({ scope: "WEEKLY" });
    await assemblyKitApi.getSuggestions({ status: "PENDING" });
    await assemblyKitApi.acceptSuggestion(7, {});
    await assemblyKitApi.rejectSuggestion(7, { reason: "测试" });
    await kitCheckApi.workOrders.list({ page: 1 });

    expect(mock.history.get[0].url).toBe("/assembly-kit/dashboard");
    expect(mock.history.get[1].url).toBe("/assembly-kit/stages");
    expect(mock.history.get[2].url).toBe("/assembly-kit/shortage-alerts");
    expect(mock.history.get[3].url).toBe("/assembly-kit/templates");
    expect(mock.history.post[0].url).toBe("/assembly-kit/scheduling/suggestions/generate");
    expect(mock.history.get[4].url).toBe("/assembly-kit/scheduling/suggestions");
    expect(mock.history.post[1].url).toBe("/assembly-kit/scheduling/suggestions/7/accept");
    expect(mock.history.post[2].url).toBe("/assembly-kit/scheduling/suggestions/7/reject");
    expect(mock.history.get[5].url).toBe("/kit-check/work-orders");
  });

  it("uses management-rhythm routes for meeting map and reports", async () => {
    const { managementRhythmApi } = await import("../admin.js");
    mock.onGet("/api/v1/management-rhythm/meeting-map/").reply(200, { items: [] });
    mock.onGet("/api/v1/management-rhythm/meeting-reports").reply(200, {
      items: [],
      total: 0,
    });

    await managementRhythmApi.meetingMap.get({ rhythm_level: "company" });
    await managementRhythmApi.reports.list({ page: 1 });

    expect(mock.history.get[0].url).toBe("/management-rhythm/meeting-map/");
    expect(mock.history.get[1].url).toBe("/management-rhythm/meeting-reports");
  });

  it("uses management-rhythm routes for strategic meetings", async () => {
    const { managementRhythmApi } = await import("../admin.js");
    mock.onGet("/api/v1/management-rhythm/meetings/strategic-meetings").reply(200, {
      items: [],
      total: 0,
    });
    mock.onGet("/api/v1/management-rhythm/meetings/strategic-meetings/7").reply(200, {
      id: 7,
    });
    mock
      .onPut("/api/v1/management-rhythm/meetings/strategic-meetings/7/minutes")
      .reply(200, { id: 7 });
    mock
      .onGet("/api/v1/management-rhythm/action-items/strategic-meetings/7/action-items")
      .reply(200, []);

    await managementRhythmApi.meetings.list({ page: 1 });
    await managementRhythmApi.meetings.get(7);
    await managementRhythmApi.meetings.updateMinutes(7, { minutes: "纪要" });
    await managementRhythmApi.actionItems.list(7, { status: "OPEN" });

    expect(mock.history.get[0].url).toBe(
      "/management-rhythm/meetings/strategic-meetings",
    );
    expect(mock.history.get[1].url).toBe(
      "/management-rhythm/meetings/strategic-meetings/7",
    );
    expect(mock.history.put[0].url).toBe(
      "/management-rhythm/meetings/strategic-meetings/7/minutes",
    );
    expect(mock.history.get[2].url).toBe(
      "/management-rhythm/action-items/strategic-meetings/7/action-items",
    );
  });

  it("uses non-redirecting project review collection route", async () => {
    const { projectReviewApi } = await import("../engineering.js");
    mock.onGet("/api/v1/project-reviews/").reply(200, {
      items: [],
      total: 0,
    });

    await projectReviewApi.list({ page: 1, page_size: 20 });

    expect(mock.history.get[0].url).toBe("/project-reviews/");
    expect(mock.history.get[0].params).toEqual({ page: 1, page_size: 20 });
  });

  it("uses project material-progress routes registered under projects", async () => {
    const { projectApi } = await import("../projects.js");
    mock.onGet("/api/v1/projects/42/material-progress").reply(200, {
      code: 200,
      data: { kitting_rate: 0, critical_materials: [] },
    });
    mock.onGet("/api/v1/projects/42/bom-progress").reply(200, {
      code: 200,
      data: { items: [] },
    });
    mock.onGet("/api/v1/projects/42/shortage-tracker").reply(200, {
      code: 200,
      data: { shortage_items: [] },
    });
    mock.onPost("/api/v1/projects/42/material-progress/subscribe").reply(200, {
      code: 200,
      data: {},
    });

    await projectApi.getMaterialProgress(42);
    await projectApi.getBomProgress(42);
    await projectApi.getShortageTracker(42);
    await projectApi.subscribeMaterialProgress(42, { shortage_alert: true });

    expect(mock.history.get[0].url).toBe("/projects/42/material-progress");
    expect(mock.history.get[1].url).toBe("/projects/42/bom-progress");
    expect(mock.history.get[2].url).toBe("/projects/42/shortage-tracker");
    expect(mock.history.post[0].url).toBe(
      "/projects/42/material-progress/subscribe",
    );
  });

  it("uses progress auto-preview route with backend snake_case query params", async () => {
    const { progressApi } = await import("../progress.js");
    mock.onGet("/api/v1/progress/projects/42/auto-preview").reply(200, {
      project_id: 42,
      success: true,
    });

    await progressApi.autoProcess.preview(42, {
      auto_block: true,
      delay_threshold: 12,
    });

    expect(mock.history.get[0].url).toBe("/progress/projects/42/auto-preview");
    expect(mock.history.get[0].params).toEqual({
      auto_block: true,
      delay_threshold: 12,
    });
  });

  it("uses non-redirecting stage template collection route for project creation", async () => {
    const { stageViewsApi } = await import("../stageViews.js");
    mock.onGet("/api/v1/stage-templates/").reply(200, {
      items: [],
      total: 0,
    });

    await stageViewsApi.templates.list({ is_active: true });

    expect(mock.history.get[0].url).toBe("/stage-templates/");
    expect(mock.history.get[0].params).toEqual({ is_active: true });
  });

  it("adds project members through the current project-scoped member route", async () => {
    const { memberApi } = await import("../projects.js");
    mock.onPost("/api/v1/projects/42/members/").reply(201, {
      id: 7,
      project_id: 42,
      user_id: 9,
      role_code: "member",
    });

    await memberApi.add({
      project_id: 42,
      user_id: 9,
      role: "member",
      status: "active",
    });

    expect(mock.history.post[0].url).toBe("/projects/42/members/");
    expect(JSON.parse(mock.history.post[0].data)).toEqual({
      user_id: 9,
      role_code: "member",
    });
  });

  it("uses project review lesson and practice list routes", async () => {
    const { projectReviewApi } = await import("../engineering.js");
    mock.onGet("/api/v1/project-reviews/lessons").reply(200, {
      results: [],
    });
    mock.onGet("/api/v1/projects/best-practices").reply(200, {
      code: 200,
      data: { items: [], total: 0 },
    });

    await projectReviewApi.lessons.list({ review: 7 });
    await projectReviewApi.practices.list({ review: 7 });

    expect(mock.history.get[0].url).toBe("/project-reviews/lessons");
    expect(mock.history.get[0].params).toEqual({ review_id: 7 });
    expect(mock.history.get[1].url).toBe("/projects/best-practices");
    expect(mock.history.get[1].params).toEqual({ review_id: 7 });
  });

  it("uses the registered kit-rate route for time-based project readiness", async () => {
    const { assemblyKitApi } = await import("../production.js");
    mock.onGet("/api/v1/kit-rate/project/42/time-based-kit-rate").reply(200, {
      summary: {},
      stage_analysis: [],
    });

    await assemblyKitApi.getTimeBasedKitRate(42, {
      planned_start_date: "2026-06-26",
    });

    expect(mock.history.get[0].url).toBe(
      "/kit-rate/project/42/time-based-kit-rate",
    );
    expect(mock.history.get[0].params).toEqual({
      planned_start_date: "2026-06-26",
    });
  });

  it("uses ECN detail and impact-analysis routes registered by the backend", async () => {
    const { ecnApi } = await import("../ecn.js");
    mock.onGet("/api/v1/ecns/1").reply(200, { id: 1 });
    mock.onPost("/api/v1/ecns/1/cost-impact-analysis").reply(200, {});
    mock.onGet("/api/v1/ecns/1/cost-tracking").reply(200, {});
    mock.onGet("/api/v1/ecns/1/cost-records").reply(200, { items: [] });
    mock.onPost("/api/v1/ecns/1/material-impact-analysis").reply(200, {});
    mock.onGet("/api/v1/ecns/1/execution-progress").reply(200, {});
    mock.onGet("/api/v1/ecns/1/stakeholders").reply(200, []);

    await ecnApi.getDetail(1);
    await ecnApi.analyzeCostImpact(1);
    await ecnApi.getCostTracking(1);
    await ecnApi.getCostRecords(1, { page: 1 });
    await ecnApi.analyzeMaterialImpact(1);
    await ecnApi.getExecutionProgress(1);
    await ecnApi.getStakeholders(1);

    expect(mock.history.get[0].url).toBe("/ecns/1");
    expect(mock.history.post[0].url).toBe("/ecns/1/cost-impact-analysis");
    expect(mock.history.get[1].url).toBe("/ecns/1/cost-tracking");
    expect(mock.history.get[2].url).toBe("/ecns/1/cost-records");
    expect(mock.history.get[2].params).toEqual({ page: 1 });
    expect(mock.history.post[1].url).toBe("/ecns/1/material-impact-analysis");
    expect(mock.history.get[3].url).toBe("/ecns/1/execution-progress");
    expect(mock.history.get[4].url).toBe("/ecns/1/stakeholders");
  });

  it("uses project best-practice recommendation routes backed by best-practices search", async () => {
    const { projectReviewApi } = await import("../engineering.js");
    mock.onGet("/api/v1/projects/best-practices").reply(200, {
      code: 200,
      data: { items: [], total: 0 },
    });

    await projectReviewApi.getProjectBestPracticeRecommendations(42, 20);
    await projectReviewApi.recommendBestPractices({
      project_type: "AUTOMATION",
      current_stage: "S2",
      limit: 20,
    });

    expect(mock.history.get[0].url).toBe("/projects/best-practices");
    expect(mock.history.get[0].params).toEqual({
      project_id: 42,
      page_size: 20,
    });
    expect(mock.history.get[1].url).toBe("/projects/best-practices");
    expect(mock.history.get[1].params).toEqual({
      project_type: "AUTOMATION",
      current_stage: "S2",
      limit: 20,
    });
  });

  it("uses engineer-scheduling report and warning routes registered by the backend", async () => {
    const { engineerSchedulingApi } = await import("../engineerScheduling.js");
    mock.onGet("/api/v1/engineer-scheduling/projects/42/scheduling-report").reply(200, {
      total_tasks: 0,
    });
    mock.onPost("/api/v1/engineer-scheduling/warnings/generate").reply(200, {
      warnings: [],
    });

    await engineerSchedulingApi.getSchedulingReport(42);
    await engineerSchedulingApi.generateWarnings({ project_id: 42 });

    expect(mock.history.get[0].url).toBe(
      "/engineer-scheduling/projects/42/scheduling-report",
    );
    expect(mock.history.post[0].url).toBe("/engineer-scheduling/warnings/generate");
    expect(mock.history.post[0].params).toEqual({ project_id: 42 });
  });
});
