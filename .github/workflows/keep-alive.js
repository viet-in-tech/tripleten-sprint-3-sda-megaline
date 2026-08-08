const { chromium } = require("playwright");

const URL = "https://megaline-sda-dashboard.streamlit.app/";

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();

  await page.goto(URL, { waitUntil: "load", timeout: 60000 });
  await page.waitForTimeout(5000);

  const wakeButton = page.locator("button", { hasText: "get this app back up" });
  if (await wakeButton.count() > 0) {
    console.log("App was asleep — clicking wake button.");
    await wakeButton.click();
    await page.waitForTimeout(20000);
  } else {
    console.log("App was already awake — visit recorded.");
  }

  await browser.close();
})();
