import asyncio
from playwright.async_api import async_playwright
import os
import json

async def main():
    async with async_playwright() as p:
        print("Launching browser...")
        browser = await p.chromium.launch(
            headless=True,  # Test with headless=True first
        )
        context = await browser.new_context(
            locale="pt-BR",
            viewport={"width": 1440, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        )
        page = await context.new_page()
        
        # Load cookies
        cookies_file = "amazon_cookies.json"
        if os.path.exists(cookies_file):
            print("Loading cookies...")
            with open(cookies_file, "r", encoding="utf-8") as f:
                cookies = json.load(f)
            await context.add_cookies(cookies)
            print("Cookies loaded.")
        
        print("Navigating to Amazon home...")
        await page.goto("https://www.amazon.com.br", wait_until="domcontentloaded", timeout=30000)
        print("Home loaded. Title:", await page.title())
        
        print("Navigating to bestsellers category...")
        try:
            await page.goto("https://www.amazon.com.br/gp/bestsellers/electronics/", wait_until="domcontentloaded", timeout=30000)
            print("Category loaded. Title:", await page.title())
            await page.wait_for_timeout(2000)
            print("Wait for timeout succeeded.")
        except Exception as e:
            print("Error during navigation/wait:", e)
            
        await browser.close()
        print("Browser closed.")

if __name__ == "__main__":
    asyncio.run(main())
