from playwright.sync_api import sync_playwright
import time


def BrowserButtonPress(
        url: str,
        button_name: str
):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        page.goto(url, wait_until="domcontentloaded")

        # kleine Wartezeit damit der Player sicher da ist
        page.wait_for_timeout(2000)

        # ersten Button automatisch klicken
        page.locator(button_name).first.click(timeout=5000)

        # 1 Sekunde kurz laufen lassen
        page.wait_for_timeout(1000)

        browser.close()