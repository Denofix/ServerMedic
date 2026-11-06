import { expect, test } from "@playwright/test";
import { readFile } from "node:fs/promises";
import path from "node:path";

test("sample → masked preview → analysis → evidence jump → Markdown", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Every log tells a story." }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Analyze log", exact: true }),
  ).toBeDisabled();
  await page
    .getByRole("button", { name: "Load PostgreSQL connection sample" })
    .click();
  await expect(page.getByTestId("log-line-3")).toBeVisible();
  await expect(
    page.getByRole("region", { name: "Processed log viewer" }),
  ).toContainText("[REDACTED]");
  await expect(page.locator("body")).not.toContainText("synthetic-password");
  await page.getByRole("button", { name: "Analyze log", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Analyzing log…" }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "PostgreSQL connection refused" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Go to line 4", exact: true }).click();
  await expect(page.getByTestId("log-line-4")).toHaveClass(/active/);
  await expect(page.getByTestId("log-line-4")).toBeFocused();
  const downloadEvent = page.waitForEvent("download");
  await page.getByRole("button", { name: "Download Markdown" }).click();
  const download = await downloadEvent;
  expect(download.suggestedFilename()).toBe("postgres-servermedic.md");
  const content = await readFile((await download.path())!, "utf8");
  expect(content).toContain("Line 4:");
  expect(content).toContain("ECONNREFUSED");
  expect(content).toContain("Hypothesis (unconfirmed)");
  expect(content).not.toContain("synthetic-password");
  expect(errors).toEqual([]);
});

for (const [sample, title] of [
  ["Missing configuration", "Required configuration is missing"],
  ["Port already in use", "HTTP port is already in use"],
] as const) {
  test(`${sample} sample uses the analysis endpoint`, async ({ page }) => {
    await page.goto("/");
    await page.getByRole("button", { name: `Load ${sample} sample` }).click();
    await expect(
      page.getByRole("button", { name: "Analyze log", exact: true }),
    ).toBeEnabled();
    await page
      .getByRole("button", { name: "Analyze log", exact: true })
      .click();
    await expect(page.getByRole("heading", { name: title })).toBeVisible();
  });
}

test("healthy sample has no findings and still exports", async ({ page }) => {
  await page.goto("/");
  await page
    .getByRole("button", { name: "Load Healthy startup sample" })
    .click();
  await expect(
    page.getByRole("button", { name: "Analyze log", exact: true }),
  ).toBeEnabled();
  await page.getByRole("button", { name: "Analyze log", exact: true }).click();
  await expect(
    page.getByText("No problems identified", { exact: true }),
  ).toBeVisible();
  await expect(page.locator(".finding")).toHaveCount(0);
  await expect(
    page.getByRole("button", { name: "Download Markdown" }),
  ).toBeEnabled();
});

test("local file upload also gets server redaction", async ({ page }) => {
  await page.goto("/");
  await page
    .getByLabel("Upload log file")
    .setInputFiles(path.resolve("../examples/postgres.log"));
  await expect(page.getByTestId("log-line-2")).toContainText("[REDACTED]");
  await expect(page.locator("body")).not.toContainText("synthetic-password");
  await page.getByRole("button", { name: "Analyze log", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "PostgreSQL connection refused" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Remove file" }).click();
  await expect(
    page.getByRole("heading", { name: "Every log tells a story." }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Download Markdown" }),
  ).toHaveCount(0);
});

test("invalid file and line limits produce useful errors", async ({ page }) => {
  await page.goto("/");
  const input = page.getByLabel("Upload log file");
  await input.setInputFiles({
    name: "wrong.csv",
    mimeType: "text/plain",
    buffer: Buffer.from("x"),
  });
  await expect(page.getByRole("alert")).toContainText(".log or .txt");
  await input.setInputFiles({
    name: "big.log",
    mimeType: "text/plain",
    buffer: Buffer.alloc(65537, "x"),
  });
  await expect(page.getByRole("alert")).toContainText("64 KiB");
  await input.setInputFiles({
    name: "lines.log",
    mimeType: "text/plain",
    buffer: Buffer.from("x\n".repeat(500)),
  });
  await expect(page.getByRole("alert")).toContainText("500 lines");
});

test("LLM error preserves preview and offers retry without a report", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByLabel("Upload log file").setInputFiles({
    name: "timeout.log",
    mimeType: "text/plain",
    buffer: Buffer.from("SERVERMEDIC_TEST_TIMEOUT"),
  });
  await expect(
    page.getByRole("button", { name: "Analyze log", exact: true }),
  ).toBeEnabled();
  await page.getByRole("button", { name: "Analyze log", exact: true }).click();
  await expect(page.getByRole("alert")).toContainText("Analysis timed out");
  await expect(page.getByTestId("log-line-1")).toContainText(
    "SERVERMEDIC_TEST_TIMEOUT",
  );
  await expect(
    page.getByRole("button", { name: "Try analysis again" }),
  ).toBeEnabled();
  await expect(
    page.getByRole("button", { name: "Download Markdown" }),
  ).toHaveCount(0);
});

test("mobile layout stays within viewport", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await page
    .getByRole("button", { name: "Load PostgreSQL connection sample" })
    .click();
  await expect(
    page.getByRole("button", { name: "Analyze log", exact: true }),
  ).toBeEnabled();
  await page.getByRole("button", { name: "Analyze log", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "PostgreSQL connection refused" }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
});
