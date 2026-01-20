import { expect, test } from "playwright/test";

test("login page loads", async ({ page }) => {
  await page.goto("/login");
  await expect(page.getByPlaceholder("请输入用户名")).toBeVisible();
  await expect(page.getByPlaceholder("请输入密码")).toBeVisible();
  await expect(page.getByRole("heading", { name: "欢迎回来" })).toBeVisible();
});
