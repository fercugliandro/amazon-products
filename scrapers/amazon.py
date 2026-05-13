"""Scraper de bestsellers da Amazon via Playwright (async)."""
import asyncio
import json
import os
import re

from playwright.async_api import async_playwright

from affiliate import amazon_affiliate_link
from config import (
    AMAZON_AFFILIATE_TAG,
    AMAZON_CATEGORIES,
    AMAZON_COOKIES_FILE,
    AMAZON_TOP_N,
)
from utils import log, parse_price, slugify


# ── Cookies ─────────────────────────────────────────────────────────────────────

async def save_cookies(context) -> None:
    cookies = await context.cookies()
    with open(AMAZON_COOKIES_FILE, "w", encoding="utf-8") as f:
        json.dump(cookies, f, ensure_ascii=False, indent=2)
    log(f"Cookies salvos em '{AMAZON_COOKIES_FILE}'.", "OK")


async def load_cookies(context) -> bool:
    if not os.path.exists(AMAZON_COOKIES_FILE):
        return False
    with open(AMAZON_COOKIES_FILE, "r", encoding="utf-8") as f:
        cookies = json.load(f)
    await context.add_cookies(cookies)
    log("Cookies carregados.", "OK")
    return True


async def ensure_logged_in(page, context) -> None:
    await page.goto("https://www.amazon.com.br", wait_until="domcontentloaded", timeout=30000)
    await page.wait_for_timeout(2000)

    stripe = page.locator("#amzn-ss-wrap, #nav-AssociateStripe")
    if await stripe.count() > 0:
        log("Logado no SiteStripe de afiliados.", "OK")
        return

    log("Não logado. Abrindo página de login...", "WARN")
    await page.goto("https://www.amazon.com.br/ap/signin", wait_until="domcontentloaded")
    input("\n>> Faça login na Amazon e pressione ENTER para continuar...\n")
    await save_cookies(context)
    log("Login realizado e cookies salvos.", "OK")


# ── SiteStripe — link curto ──────────────────────────────────────────────────────

async def get_short_link(page, asin: str) -> str:
    fallback = amazon_affiliate_link(asin)
    try:
        btn = page.locator("#amzn-ss-get-link-button")
        if await btn.count() == 0:
            return fallback

        await btn.click()
        textarea = page.locator("#amzn-ss-text-shortlink-textarea")
        await textarea.wait_for(timeout=8000)

        for _ in range(20):
            value = await textarea.input_value()
            if value and "amzn.to" in value:
                return value
            await asyncio.sleep(0.4)

    except Exception as e:
        log(f"Falha ao gerar link curto para {asin}: {e}", "WARN")

    return fallback


# ── Imagem ───────────────────────────────────────────────────────────────────────

async def get_best_image(page) -> str:
    try:
        img = page.locator("#landingImage, #imgTagWrapperId img").first
        dyn_data = await img.get_attribute("data-a-dynamic-image")
        if dyn_data:
            parsed = json.loads(dyn_data)
            return max(parsed, key=lambda u: parsed[u][0] * parsed[u][1])
        old_hires = await img.get_attribute("data-old-hires")
        if old_hires:
            return old_hires
        return await img.get_attribute("src") or ""
    except Exception:
        return ""


# ── Produto ──────────────────────────────────────────────────────────────────────

async def scrape_product(page, asin: str, rank: int, category: str) -> dict:
    await page.goto(
        f"https://www.amazon.com.br/dp/{asin}",
        wait_until="domcontentloaded",
        timeout=30000,
    )
    await page.wait_for_timeout(1500)

    try:
        title = (await page.locator("#productTitle").inner_text()).strip()
    except Exception:
        title = f"Produto {asin}"

    price = 0.0
    try:
        whole = (await page.locator(".a-price-whole").first.inner_text()).strip()
        frac = (await page.locator(".a-price-fraction").first.inner_text()).strip()
        price = parse_price(whole.replace(",", "").replace(".", "") + "." + frac)
    except Exception:
        pass

    original_price = 0.0
    try:
        orig = await page.locator(
            ".a-price.a-text-price[data-a-strike='true'] .a-offscreen"
        ).first.inner_text()
        original_price = parse_price(orig)
    except Exception:
        pass

    description = ""
    try:
        bullets = page.locator("#feature-bullets .a-list-item")
        for i in range(await bullets.count()):
            text = (await bullets.nth(i).inner_text()).strip()
            if len(text) > 15:
                description = text[:200]
                break
    except Exception:
        pass

    image = await get_best_image(page)
    product_url = await get_short_link(page, asin)

    return {
        "id": asin,
        "name": title,
        "slug": slugify(title),
        "price": price,
        "originalPrice": original_price if original_price > price else 0.0,
        "image": image,
        "productUrl": product_url,
        "source": "amazon",
        "category": category,
        "featured": rank <= 3,
        "bestSeller": True,
        "description": description,
    }


# ── ASINs ────────────────────────────────────────────────────────────────────────

async def get_top_asins(page, url: str, top_n: int) -> list[str]:
    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
    await page.wait_for_timeout(2000)

    items = page.locator(".zg-grid-general-faceout")
    count = await items.count()
    log(f"  {count} itens encontrados na página de mais vendidos.")

    asins: list[str] = []
    for i in range(min(top_n, count)):
        try:
            link = items.nth(i).locator("a.a-link-normal").first
            href = await link.get_attribute("href") or ""
            match = re.search(r"/dp/([A-Z0-9]{10})", href)
            if match:
                asins.append(match.group(1))
        except Exception:
            pass

    return asins


# ── Entry point ──────────────────────────────────────────────────────────────────

async def run(categories: dict | None = None, top_n: int = AMAZON_TOP_N) -> dict[str, list[dict]]:
    """
    Raspa os bestsellers da Amazon para cada categoria.
    Retorna {category_key: [product, ...]}.
    """
    if categories is None:
        categories = AMAZON_CATEGORIES

    log("Iniciando scraper Amazon Bestsellers", "STEP")

    all_data: dict[str, list[dict]] = {}

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=["--start-maximized"],
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

        await load_cookies(context)
        await ensure_logged_in(page, context)

        for category_key, category_info in categories.items():
            log(f"\nCategoria: {category_info['label']} ({category_key})", "STEP")

            asins = await get_top_asins(page, category_info["url"], top_n)
            log(f"  ASINs coletados: {asins}")

            products: list[dict] = []
            for rank, asin in enumerate(asins, start=1):
                try:
                    log(f"  Produto #{rank}/{len(asins)} — ASIN: {asin}")
                    product = await scrape_product(page, asin, rank, category_key)
                    products.append(product)
                    log(
                        f"  #{rank} ✓ {product['name'][:55]}... | "
                        f"R${product['price']} | {product['productUrl']}",
                        "OK",
                    )
                except Exception as e:
                    log(f"  Erro no produto #{rank} ({asin}): {e}", "ERROR")

                await asyncio.sleep(1.2)

            all_data[category_key] = products
            log(f"  {len(products)} produtos coletados para '{category_key}'.", "OK")
            await asyncio.sleep(2)

        await browser.close()

    log("Amazon scraper concluído.", "OK")
    return all_data
