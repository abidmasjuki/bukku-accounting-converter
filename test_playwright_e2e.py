import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 1200})
        page = await context.new_page()

        index_path = Path("index.html").resolve().as_uri()
        test_csv = Path(r"G:\My Drive\RPWP HEALTHCARE MASTER FOLDER\HEARING CENTRE\ACCOUNTING\BUKKU\Ogos 2026 transaction_history (2).csv").resolve()

        print(f"Navigating to {index_path}...")
        await page.goto(index_path)

        # 1. Verify initial zero state
        assert await page.is_hidden("#resultsSection"), "Results section should be hidden initially"
        assert await page.is_disabled("#btnConvert"), "Convert button should be disabled initially"
        print("[OK] Initial authentic zero-state verified.")

        # 2. Upload file via fileInput
        print(f"Setting input file: {test_csv}...")
        file_input = page.locator("#fileInput")
        await file_input.set_input_files(str(test_csv))

        # Wait for results section to be visible
        await page.wait_for_selector("#resultsSection:not(.hidden)", timeout=5000)
        print("[OK] Results section appeared automatically after file load.")

        # 3. Verify metrics
        txn_count = await page.inner_text("#statTxnCount")
        spent = await page.inner_text("#statSpent")
        received = await page.inner_text("#statReceived")
        closing = await page.inner_text("#statClosing")
        period = await page.inner_text("#statPeriod")
        bank = await page.inner_text("#bankTitle")

        print(f"Bank: {bank}")
        print(f"Period: {period}")
        print(f"Txn Count: {txn_count}")
        print(f"Spent: {spent}")
        print(f"Received: {received}")
        print(f"Closing: {closing}")

        assert txn_count == "43", f"Expected 43 transactions, got {txn_count}"
        assert spent == "RM 20,967.04", f"Expected RM 20,967.04 spent, got {spent}"
        assert received == "RM 58,108.93", f"Expected RM 58,108.93 received, got {received}"
        assert closing == "RM 89,069.17", f"Expected RM 89,069.17 closing, got {closing}"
        print("[OK] All financial reconciliation metrics verified exactly!")

        # 4. Check first row date format is YYYY-MM-DD
        first_date = await page.locator("#previewTbody tr:first-child td:first-child").inner_text()
        print(f"First row date: {first_date}")
        assert first_date == "2026-08-03", f"Expected 2026-08-03, got {first_date}"
        print("[OK] Date format strictly verified as YYYY-MM-DD (Bukku Y-m-d).")

        # 5. Test manual button click for 0ms response and re-render
        print("Testing manual button click...")
        convert_btn = page.locator("#btnConvert")
        await convert_btn.click()
        await page.wait_for_timeout(300)
        txn_count_after = await page.inner_text("#statTxnCount")
        assert txn_count_after == "43"
        print("[OK] Process & Preview button click verified.")

        # 6. Take audit screenshot and save to artifacts directory
        artifact_dir = Path(r"C:\Users\RH-Abid\.gemini\antigravity\brain\c88f4699-8296-4e3d-8a9b-9a2083820edb")
        screenshot_path = artifact_dir / "bukku_converter_verification.png"
        await page.screenshot(path=str(screenshot_path), full_page=True)
        print(f"[OK] Full page screenshot saved to {screenshot_path}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
