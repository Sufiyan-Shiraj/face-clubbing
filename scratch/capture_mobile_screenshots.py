"""Capture high-resolution mobile screenshots (phone width ~400px) of all 6 required viewer states."""

import os
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

def main():
    art_dir = Path(r"C:\Users\DELL\.gemini\antigravity-ide\brain\5143c8b1-6da6-4075-bef4-ead0a6fb5c12")
    art_dir.mkdir(parents=True, exist_ok=True)
    local_dir = Path("scratch/screenshots")
    local_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        # Launch Chromium at phone width (400 x 844 px, device_scale_factor=2)
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 400, "height": 844},
            device_scale_factor=2,
            is_mobile=True,
            has_touch=True,
        )
        page = context.new_page()

        # -------------------------------------------------------------
        # 1. Top of the page
        # -------------------------------------------------------------
        print("Capturing 1: Top of the page...")
        page.goto("http://localhost:5173/#", wait_until="networkidle")
        page.wait_for_timeout(1000)

        # Ensure page is scrolled to top
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(500)

        path_1 = art_dir / "01_top_of_page.png"
        path_1_local = local_dir / "01_top_of_page.png"
        page.screenshot(path=str(path_1))
        page.screenshot(path=str(path_1_local))
        print(f"Saved: {path_1}")

        # -------------------------------------------------------------
        # 2. Collapsed single-photo section opened
        # -------------------------------------------------------------
        print("Capturing 2: Collapsed single-photo section opened...")
        # Find the expand button containing "Appears in 1 photo"
        single_photo_btn = page.locator("button:has-text('Appears in 1 photo')")
        single_photo_btn.scroll_into_view_if_needed()
        page.wait_for_timeout(500)
        single_photo_btn.click()
        page.wait_for_timeout(800)

        # Scroll so the header and some cards are visible
        single_photo_btn.scroll_into_view_if_needed()
        page.wait_for_timeout(500)

        path_2 = art_dir / "02_single_photo_section_opened.png"
        path_2_local = local_dir / "02_single_photo_section_opened.png"
        page.screenshot(path=str(path_2))
        page.screenshot(path=str(path_2_local))
        print(f"Saved: {path_2}")

        # -------------------------------------------------------------
        # 3. Unrecognized section
        # -------------------------------------------------------------
        print("Capturing 3: Unrecognized section...")
        page.goto("http://localhost:5173/#unrecognized", wait_until="networkidle")
        page.wait_for_timeout(1000)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(500)

        path_3 = art_dir / "03_unrecognized_section.png"
        path_3_local = local_dir / "03_unrecognized_section.png"
        page.screenshot(path=str(path_3))
        page.screenshot(path=str(path_3_local))
        print(f"Saved: {path_3}")

        # Also capture scrolled view of the "Photos With No Detected Face" small list
        no_face_section = page.locator("text=Photos With No Detected Face")
        if no_face_section.count() > 0:
            no_face_section.scroll_into_view_if_needed()
            page.wait_for_timeout(500)
            path_3b = art_dir / "03b_unrecognized_no_face_list.png"
            path_3b_local = local_dir / "03b_unrecognized_no_face_list.png"
            page.screenshot(path=str(path_3b))
            page.screenshot(path=str(path_3b_local))
            print(f"Saved: {path_3b}")

        # -------------------------------------------------------------
        # 4. Person's gallery (e.g. p001)
        # -------------------------------------------------------------
        print("Capturing 4: Person's gallery...")
        page.goto("http://localhost:5173/#p001", wait_until="networkidle")
        page.wait_for_timeout(1000)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(500)

        path_4 = art_dir / "04_person_gallery.png"
        path_4_local = local_dir / "04_person_gallery.png"
        page.screenshot(path=str(path_4))
        page.screenshot(path=str(path_4_local))
        print(f"Saved: {path_4}")

        # -------------------------------------------------------------
        # 5. Full-size photo preview with its download button
        # -------------------------------------------------------------
        print("Capturing 5: Full-size photo preview with download button (p001)...")
        # In p001's gallery, click the first photo thumbnail to open the modal
        page.wait_for_selector(".grid img")
        first_photo = page.locator(".grid img").first
        first_photo.click()
        page.wait_for_timeout(800)

        # Verify Download button is visible
        dl_btn = page.locator("a:has-text('Download')")
        assert dl_btn.is_visible(), "Download button should be visible for p001 photo"

        path_5 = art_dir / "05_full_size_preview_with_download.png"
        path_5_local = local_dir / "05_full_size_preview_with_download.png"
        page.screenshot(path=str(path_5))
        page.screenshot(path=str(path_5_local))
        print(f"Saved: {path_5}")

        # Close modal
        close_btn = page.locator("button[title='Close (Esc)']")
        if close_btn.is_visible():
            close_btn.click()
            page.wait_for_timeout(500)

        # -------------------------------------------------------------
        # 6. Person whose photos have no Drive link (download button hidden)
        # -------------------------------------------------------------
        print("Capturing 6: Person without Drive link (p002)...")
        page.goto("http://localhost:5173/#p002", wait_until="networkidle")
        page.wait_for_timeout(1000)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(500)

        # Open the first photo in p002's gallery
        page.wait_for_selector(".grid img")
        photo_p002 = page.locator(".grid img").first
        photo_p002.click()
        page.wait_for_timeout(800)

        # Verify Download button is HIDDEN
        dl_btn_p002 = page.locator("a:has-text('Download')")
        assert not dl_btn_p002.is_visible(), "Download button should NOT be visible for p002 photo"

        path_6 = art_dir / "06_person_without_drive_link.png"
        path_6_local = local_dir / "06_person_without_drive_link.png"
        page.screenshot(path=str(path_6))
        page.screenshot(path=str(path_6_local))
        print(f"Saved: {path_6}")

        browser.close()
        print("\nAll 6 mobile screenshots captured successfully!")

if __name__ == "__main__":
    main()
