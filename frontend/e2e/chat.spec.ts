import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

test("a one-time link opens the chat, which streams the answer", async ({
  page,
  request,
  baseURL,
}) => {
  // ivlia is local: the page must not reach any other origin, nor break
  // its Content-Security-Policy.
  const foreign: string[] = [];
  page.on("request", (r) => {
    if (new URL(r.url()).origin !== baseURL) foreign.push(r.url());
  });
  await page.addInitScript(() => {
    const seen: string[] = [];
    Object.assign(window, { cspViolations: seen });
    document.addEventListener("securitypolicyviolation", (event) => {
      seen.push(`${event.violatedDirective} ${event.blockedURI}`);
    });
  });

  const response = await request.post("/api/session/link", {
    headers: { Authorization: `Bearer ${process.env.IVLIA_E2E_TOKEN ?? ""}` },
  });
  expect(response.ok()).toBe(true);
  const { url } = (await response.json()) as { url: string };

  await page.goto(url);
  await expect(page.getByText("API ok")).toBeVisible();
  await page.getByRole("textbox", { name: "Message" }).fill("hello");
  await page.getByRole("button", { name: "Send" }).click();
  await expect(page.getByText("Hello, world!")).toBeVisible();

  const results = await new AxeBuilder({ page }).analyze();
  expect(results.violations).toEqual([]);
  expect(foreign).toEqual([]);
  const violations = await page.evaluate(
    () => (window as unknown as { cspViolations: string[] }).cspViolations,
  );
  expect(violations).toEqual([]);
});
