import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

def test_viewer():
    out_dir = Path("scratch/screenshots")
    out_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # 1. Desktop viewport
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto("http://localhost:5173/", wait_until="networkidle")

        # Wait for grid to render
        page.wait_for_selector("text=People (189)")
        page.screenshot(path=str(out_dir / "desktop_unified_grid_all.png"), full_page=False)
        print("Captured desktop_unified_grid_all.png")

        # 2. Click toggle "Hide single-photo people"
        toggle = page.locator("button[role='switch']")
        toggle.click()
        page.wait_for_timeout(500)
        page.screenshot(path=str(out_dir / "desktop_unified_grid_hidden_singletons.png"), full_page=False)
        print("Captured desktop_unified_grid_hidden_singletons.png")

        # 3. Click first person card (p001)
        card_p001 = page.locator("text=P001").first
        card_p001.click()
        page.wait_for_timeout(500)
        page.screenshot(path=str(out_dir / "desktop_person_p001.png"), full_page=False)
        print("Captured desktop_person_p001.png")

        browser.close()

if __name__ == "__main__":
    test_viewer()
