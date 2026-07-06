import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Routes } from "react-router-dom";
import { allMenuGroups } from "../../../lib/allMenuItems";
import { FinanceRoutes } from "../financeRoutes";
import { HRRoutes } from "../hrRoutes";
import { SystemRoutes } from "../systemRoutes";

let grantedPermissions = [];

vi.mock("../../../lib/permission", () => ({
  ModuleProtectedRoute: ({ children, permission, permissions, moduleName }) => {
    const required = permission ? [permission] : permissions || [];
    const hasAccess = required.some((code) => grantedPermissions.includes(code));
    if (!hasAccess) {
      return <div>路由无权限 {moduleName || required.join(",")}</div>;
    }
    return children;
  },
}));

vi.mock("../../../pages/TemplateCenter", () => ({
  default: () => <div>模板中心页面</div>,
}));

vi.mock("../../../pages/PermissionDebug", () => ({
  default: () => <div>权限调试页面</div>,
}));

vi.mock("../../../pages/CustomerManagement", () => ({
  default: () => <div>客户主数据页面</div>,
}));

vi.mock("../../../pages/SupplierManagementData", () => ({
  default: () => <div>供应商主数据页面</div>,
}));

vi.mock("../../../pages/ProjectRoles", () => ({
  default: () => <div>项目角色页面</div>,
}));

vi.mock("../../../pages/PerformanceCenter", () => ({
  default: () => <div>绩效中心页面</div>,
}));

vi.mock("../../../pages/FinanceCostCenter", () => ({
  default: () => <div>成本中心页面</div>,
}));

function renderRoute(entry, routes) {
  return render(
    <MemoryRouter initialEntries={[entry]}>
      <Routes>{routes}</Routes>
    </MemoryRouter>,
  );
}

function flattenMenuItems(groups) {
  return groups.flatMap((group) => group.items || []);
}

describe("PERM-22 route-level permission guards", () => {
  it("blocks direct system route access without permission", async () => {
    grantedPermissions = [];
    renderRoute("/system/template-center", SystemRoutes());

    expect(await screen.findByText(/路由无权限/)).toBeInTheDocument();
    expect(screen.queryByText("模板中心页面")).not.toBeInTheDocument();
  });

  it("allows system route access with its permission", async () => {
    grantedPermissions = ["system:template:manage"];
    renderRoute("/system/template-center", SystemRoutes());

    expect(await screen.findByText("模板中心页面")).toBeInTheDocument();
  });

  it("blocks direct HR route access without permission", async () => {
    grantedPermissions = [];
    renderRoute("/hr/performance-center", HRRoutes());

    expect(await screen.findByText(/路由无权限/)).toBeInTheDocument();
    expect(screen.queryByText("绩效中心页面")).not.toBeInTheDocument();
  });

  it("blocks direct finance route access without permission", async () => {
    grantedPermissions = [];
    renderRoute("/finance/cost-center", FinanceRoutes());

    expect(await screen.findByText(/路由无权限/)).toBeInTheDocument();
    expect(screen.queryByText("成本中心页面")).not.toBeInTheDocument();
  });

  it("blocks legacy system admin direct routes without permission", async () => {
    grantedPermissions = [];

    const cases = [
      ["/debug/permissions", "权限调试页面"],
      ["/customer-management", "客户主数据页面"],
      ["/supplier-management-data", "供应商主数据页面"],
      ["/projects/42/roles", "项目角色页面"],
    ];

    for (const [entry, pageText] of cases) {
      const view = renderRoute(entry, SystemRoutes());

      expect(await screen.findByText(/路由无权限/)).toBeInTheDocument();
      expect(screen.queryByText(pageText)).not.toBeInTheDocument();

      view.unmount();
    }
  });

  it("keeps legacy system menu candidates permission-scoped", () => {
    const itemsByPath = new Map(flattenMenuItems(allMenuGroups).map((item) => [item.path, item]));

    expect(itemsByPath.get("/user-management")).toMatchObject({ permission: "USER_VIEW" });
    expect(itemsByPath.get("/role-management")).toMatchObject({ permission: "ROLE_VIEW" });
    expect(itemsByPath.get("/customer-management")).toMatchObject({ permission: "customer:read" });
    expect(itemsByPath.get("/supplier-management-data")).toMatchObject({ permission: "supplier:read" });
    expect(itemsByPath.get("/department-management")).toMatchObject({
      permissionAny: ["system:org:manage", "system:position:manage"],
    });
  });
});
