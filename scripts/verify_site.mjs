#!/usr/bin/env node
import path from "path";
import { fileURLToPath } from "url";
import { chromium } from "playwright";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const root = path.resolve(__dirname, "..");
const indexPath = "file://" + path.join(root, "site", "index.html");
const screenshotPath = path.join(root, "media", "site-screenshot.png");
const chromePath = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";

(async () => {
  const launchOptions = { headless: true };
  if (process.platform === "darwin") {
    launchOptions.executablePath = chromePath;
  }
  const browser = await chromium.launch(launchOptions);
  const page = await browser.newPage({ viewport: { width: 1440, height: 980 }, deviceScaleFactor: 1 });
  await page.goto(indexPath, { waitUntil: "networkidle" });
  await page.waitForSelector("[data-testid='speedup']");

  const checks = await page.evaluate(() => {
    const speedup = document.querySelector("[data-testid='speedup']")?.textContent || "";
    const cards = Array.from(document.querySelectorAll(".metric"));
    const overflowing = cards.filter((card) => card.scrollWidth > card.clientWidth + 1).length;
    const title = document.querySelector("h1")?.textContent || "";
    const bodyText = document.body.innerText;
    return {
      speedup,
      cardCount: cards.length,
      overflowing,
      title,
      hasBoundary: bodyText.includes("Not medical diagnosis"),
      bodyLength: bodyText.length,
    };
  });

  if (!/x/.test(checks.speedup)) throw new Error("speedup not rendered");
  if (checks.cardCount < 5) throw new Error("not enough metric cards rendered");
  if (checks.overflowing !== 0) throw new Error("metric card overflow detected");
  if (!checks.title.includes("ArmCare")) throw new Error("title missing");
  if (!checks.hasBoundary) throw new Error("claim boundary missing");
  if (checks.bodyLength < 500) throw new Error("dashboard body too small");

  await page.screenshot({ path: screenshotPath, fullPage: true });
  await browser.close();
  console.log(`verified site screenshot: ${screenshotPath}`);
})().catch(async (error) => {
  console.error(error);
  process.exit(1);
});
