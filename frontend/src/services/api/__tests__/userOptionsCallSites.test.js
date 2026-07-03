import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { describe, expect, it } from "vitest";

const businessUserChoiceFiles = [
  "pages/CustomerCommunication/index.jsx",
  "pages/ProjectRoles.jsx",
  "pages/SalesFunnel/index.jsx",
  "components/project/ProjectLeadsPanel.jsx",
  "pages/OpportunityManagement/index.jsx",
  "pages/InstallationDispatchManagement.jsx",
  "pages/WorkshopManagement/hooks/useWorkshopManagement.js",
];

const managementUserListFiles = [
  "pages/UserManagement/index.jsx",
  "pages/UserManagement/hooks/useUserManagement.js",
];

function readFrontendSource(relativePath) {
  return readFileSync(resolve(process.cwd(), "src", relativePath), "utf8");
}

describe("business user choice call sites", () => {
  it.each(businessUserChoiceFiles)(
    "%s uses lightweight user options instead of the management user list",
    (relativePath) => {
      const source = readFrontendSource(relativePath);

      expect(source).toMatch(/userApi\.options\s*\(/);
      expect(source).not.toMatch(/userApi\.list\s*\(/);
    }
  );

  it.each(managementUserListFiles)("%s still uses the management user list", (relativePath) => {
    const source = readFrontendSource(relativePath);

    expect(source).toMatch(/userApi\.list\s*\(/);
  });
});
