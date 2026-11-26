"""Browser acceptance checks for the local FastAPI workspace."""
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "preview"
OUT.mkdir(exist_ok=True)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        errors = []
        page.on("pageerror", lambda exc: errors.append(str(exc)))
        page.goto("http://127.0.0.1:8000/", wait_until="networkidle")
        page.get_by_text("FastAPI подключён", exact=False).wait_for()
        page.get_by_role("heading", name="Обзор рынка").wait_for()
        assert page.get_by_text("11 990", exact=False).count() > 0 or page.get_by_text("Time Team", exact=False).count() > 0
        page.screenshot(path=OUT / "01-overview.png", full_page=True)
        page.locator('nav [data-page="market"]').click()
        page.locator("#q").fill("Raspberry")
        assert page.get_by_text("Robocraze").count() == 1
        assert page.get_by_text("Time Team").count() == 0
        page.get_by_role("button", name="Сценарии", exact=True).click()
        page.locator("#minMargin").fill("0")
        page.locator("[data-save=d1]").click()
        page.screenshot(path=OUT / "02-deals.png", full_page=True)
        page.locator('nav [data-page="saved"]').click()
        page.locator("#view").get_by_text("Seiko 5 Sports", exact=True).wait_for()
        page.locator("[data-reserve=d1]").click()
        page.locator("#days").fill("14")
        page.locator("#confirm").click()
        page.get_by_role("heading", name="Бронирования").wait_for()
        page.locator("#view").get_by_text("Seiko 5 Sports", exact=True).wait_for()
        page.locator('nav [data-page="calculator"]').click()
        page.get_by_text("Расчёт FastAPI").wait_for()
        page.locator("#discount").fill("0")
        page.wait_for_function("document.querySelector('#calcResult').innerText.includes('20.5%')")
        page.screenshot(path=OUT / "03-calculator.png", full_page=True)
        page.locator('nav [data-page="calendar"]').click()
        page.locator("[data-day=27]").click()
        page.locator("#events").get_by_text("Black Friday", exact=True).wait_for()
        with page.expect_download() as download:
            page.locator("#ics").click()
        assert download.value.suggested_filename.endswith(".ics")
        page.screenshot(path=OUT / "04-calendar.png", full_page=True)
        page.locator('nav [data-page="finance"]').click()
        page.locator('[name="name"]').fill("Browser test")
        page.locator('[name="sale"]').fill("10000")
        page.locator('[name="cost"]').fill("6000")
        page.locator('[name="fee"]').fill("500")
        page.locator("#saleForm button").click()
        page.get_by_text("Browser test", exact=True).wait_for()
        page.reload(wait_until="networkidle")
        page.locator('nav [data-page="finance"]').click()
        page.get_by_text("Browser test", exact=True).wait_for()
        page.locator('nav [data-page="admin"]').click()
        page.get_by_text("Amazon India", exact=True).wait_for()
        page.screenshot(path=OUT / "05-diagnostics.png", full_page=True)
        assert not errors, errors
        mobile = browser.new_page(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
        mobile.goto("http://127.0.0.1:8000/", wait_until="networkidle")
        mobile.get_by_role("heading", name="Обзор рынка").wait_for()
        mobile.screenshot(path=OUT / "06-mobile.png", full_page=True)
        browser.close()
    print("Browser acceptance: overview, filters, scenarios, favorites, booking, API calculation, calendar export, persistence, diagnostics and mobile passed")


if __name__ == "__main__":
    main()
