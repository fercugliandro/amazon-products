import os
import asyncio
from playwright.async_api import async_playwright
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import log

SESSION_PATH = r"C:\Users\ferna\development\amazon-products\output\meta_session.json"
BANNER_PATH = r"C:\Users\ferna\development\amazon-products\output\banners\achadinho_pilha-alcalina-elgin-palito-aaa-blister-com-4.png"
DEBUG_DIR = r"C:\Users\ferna\development\amazon-products\output\debug_screenshots"

async def test_edit():
    os.makedirs(DEBUG_DIR, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(storage_state=SESSION_PATH, viewport={"width": 1280, "height": 800})
        page = await context.new_page()
        
        await page.goto("https://business.facebook.com/latest/composer?media_type=stories")
        await page.wait_for_timeout(6000)
        
        log("Uploading image...", "INFO")
        upload_btn = page.get_by_text("Adicionar foto/vídeo", exact=False)
        if await upload_btn.count() == 0:
            upload_btn = page.get_by_text("Add media", exact=False)
            
        async with page.expect_file_chooser() as fc_info:
            await upload_btn.first.click()
        file_chooser = await fc_info.value
        await file_chooser.set_files(BANNER_PATH)
        
        log("Waiting for upload...", "INFO")
        await page.wait_for_timeout(8000)
        
        log("Clicking 'Editar' button...", "INFO")
        edit_btn = page.get_by_text("Editar", exact=True)
        if await edit_btn.count() == 0:
            edit_btn = page.get_by_text("Edit", exact=True)
            
        if await edit_btn.count() > 0:
            await edit_btn.first.click()
            log("Clicked 'Editar'. Waiting for edit dialog...", "OK")
            await page.wait_for_timeout(5000)
            await page.screenshot(path=os.path.join(DEBUG_DIR, "story_edit_loaded.png"))
            log("Screenshot saved.", "OK")
        else:
            log("Button 'Editar' not found.", "ERROR")
            await page.screenshot(path=os.path.join(DEBUG_DIR, "story_edit_not_found.png"))
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_edit())
