import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import PresalesWorkbench from "../PresalesWorkbench";

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return actual;
});

function renderPage(initialEntry = "/presales/workbench") {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <Routes>
        <Route path="/presales/workbench" element={<PresalesWorkbench />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("PresalesWorkbench", () => {
  it("preserves sales support context when entering role workbenches and assets", () => {
    renderPage(
      "/presales/workbench?lead_id=2026&opportunity_id=2&ticket_id=501&project_id=42",
    );

    const enterLinks = screen.getAllByRole("link", { name: "进入" });
    expect(enterLinks.map((link) => link.getAttribute("href"))).toEqual([
      "/presales/workbench/sales?lead_id=2026&opportunity_id=2&ticket_id=501&project_id=42",
      "/presales/workbench/execution?lead_id=2026&opportunity_id=2&ticket_id=501&project_id=42",
      "/presales/workbench/manager?lead_id=2026&opportunity_id=2&ticket_id=501&project_id=42",
    ]);

    expect(screen.getByRole("link", { name: /技术方案/ })).toHaveAttribute(
      "href",
      "/presales/technical-solutions?tab=solutions&lead_id=2026&opportunity_id=2&ticket_id=501&project_id=42",
    );
    expect(screen.getByRole("link", { name: /成本估算/ })).toHaveAttribute(
      "href",
      "/presales/technical-solutions?tab=cost&lead_id=2026&opportunity_id=2&ticket_id=501&project_id=42",
    );
    expect(screen.getByRole("link", { name: /技术参数/ })).toHaveAttribute(
      "href",
      "/presales/technical-solutions?tab=parameters&lead_id=2026&opportunity_id=2&ticket_id=501&project_id=42",
    );
  });
});
