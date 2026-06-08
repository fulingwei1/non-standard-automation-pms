import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { PageHeader } from "../PageHeader";

describe("PageHeader", () => {
  it("renders breadcrumb links from href, to, or path", () => {
    render(
      <MemoryRouter>
        <PageHeader
          title="详情页"
          breadcrumbs={[
            { label: "首页", href: "/" },
            { label: "销售管理", path: "/sales" },
            { label: "线索管理", to: "/sales/leads" },
            { label: "详情", path: "" },
          ]}
        />
      </MemoryRouter>,
    );

    expect(screen.getByRole("link", { name: "首页" })).toHaveAttribute("href", "/");
    expect(screen.getByRole("link", { name: "销售管理" })).toHaveAttribute("href", "/sales");
    expect(screen.getByRole("link", { name: "线索管理" })).toHaveAttribute(
      "href",
      "/sales/leads",
    );
    expect(screen.getByText("详情")).not.toHaveAttribute("href");
  });
});
