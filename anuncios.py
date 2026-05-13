import asyncio
import json
import re
import os
import unicodedata
from datetime import datetime
from playwright.async_api import async_playwright

# ============================================================
#  CONFIGURAÇÕES
# ============================================================
AFFILIATE_TAG = "fercugliandro-20"
OUTPUT_DIR = "output"
COOKIES_FILE = "amazon_cookies.json"

CATEGORIES = {
    "tech": {
        "label": "Eletrônicos",
        "url": "https://www.amazon.com.br/gp/bestsellers/electronics/",
    },
    "gaming": {
        "label": "Games e Consoles",
        "url": "https://www.amazon.com.br/gp/bestsellers/videogames/",
    },
    "beauty": {
        "label": "Beleza e Cuidados Pessoais",
        "url": "https://www.amazon.com.br/gp/bestsellers/beauty/",
    },
    "home": {
        "label": "Casa e Cozinha",
        "url": "https://www.amazon.com.br/gp/bestsellers/kitchen/",
    },
    "baby": {
        "label": "Bebês",
        "url": "https://www.amazon.com.br/gp/browse.html?node=17242603011&ref_=nav_em_br_sa_baby_all_0_2_11_2",
    },
    "fitness": {
        "label": "Esportes e Aventura",
        "url": "https://www.amazon.com.br/gp/bestsellers/sports/",
    },
    "automotive": {
        "label": "Automotivo",
        "url": "https://www.amazon.com.br/gp/bestsellers/automotive/",
    },
    "pets_cachorro": {
        "label": "Pet Shop - Cachorro",
        "url": "https://www.amazon.com.br/gp/bestsellers/pet-products/19653951011/ref=zg_bs_nav_pet-products_1",
    },
    "pets_gato": {
        "label": "Pet Shop - Gato",
        "url": "https://www.amazon.com.br/gp/bestsellers/pet-products/19653950011/ref=zg_bs_unv_pet-products_2_19653991011_1",
    },
    "perfurmaria_feminina": {
        "label": "Perfumaria Feminina",
        "url": "https://www.amazon.com.br/s?rh=n%3A16754378011&_encoding=UTF8&pf_rd_p=891c72cf-46f2-447f-9edb-96562eae7920&pf_rd_r=VV479K51DPKS5BXXMH0J&rd=1&ref=cct_cg_grid_1a1",
    },
    "perfumaria_masculina": {
        "label": "Perfumaria Masculina",
        "url": "https://www.amazon.com.br/s?rh=n%3A16754380011&_encoding=UTF8&pf_rd_p=891c72cf-46f2-447f-9edb-96562eae7920&pf_rd_r=1E3P54K23M595YTJ0DAQ&rd=1&ref=cct_cg_grid_1b1",
    },
    
}

TOP_N = 10  # Quantidade de produtos por categoria


# ============================================================
#  UTILITÁRIOS
# ============================================================
def slugify(text: str) -> str:
    text = text.lower().strip()
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text[:70]


def parse_price(text: str) -> float:
    if not text:
        return 0.0
    text = re.sub(r"[^\d,.]", "", text.replace("R$", "").strip())
    # Formato BR: 1.299,90 → 1299.90
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    try:
        return round(float(text), 2)
    except ValueError:
        return 0.0


def log(msg: str, level: str = "INFO"):
    icons = {"INFO": "ℹ️", "OK": "✅", "WARN": "⚠️", "ERROR": "❌", "STEP": "🔷"}
    print(f"{icons.get(level, '▸')} {msg}")


# ============================================================
#  COOKIES (login persistente)
# ============================================================
async def save_cookies(context):
    cookies = await context.cookies()
    with open(COOKIES_FILE, "w", encoding="utf-8") as f:
        json.dump(cookies, f, ensure_ascii=False, indent=2)
    log(f"Cookies salvos em '{COOKIES_FILE}'", "OK")


async def load_cookies(context) -> bool:
    if not os.path.exists(COOKIES_FILE):
        return False
    with open(COOKIES_FILE, "r", encoding="utf-8") as f:
        cookies = json.load(f)
    await context.add_cookies(cookies)
    log("Cookies carregados com sucesso.", "OK")
    return True


async def ensure_logged_in(page, context):
    """Verifica se está logado. Se não, abre o login e aguarda o usuário."""
    await page.goto("https://www.amazon.com.br", wait_until="domcontentloaded", timeout=30000)
    await page.wait_for_timeout(2000)

    # Verifica se o SiteStripe está visível (indica que está logado como afiliado)
    stripe = page.locator("#amzn-ss-wrap, #nav-AssociateStripe")
    is_logged = await stripe.count() > 0

    if is_logged:
        log("Já logado no SiteStripe de afiliados.", "OK")
        return

    log("Não logado. Abrindo página de login...", "WARN")
    await page.goto("https://www.amazon.com.br/ap/signin", wait_until="domcontentloaded")
    input("\n>> Faça login na Amazon e pressione ENTER para continuar...\n")
    await save_cookies(context)
    log("Login realizado e cookies salvos.", "OK")


# ============================================================
#  SITESTRIPE — Gerar link de afiliado curto
# ============================================================
async def get_short_link(page, asin: str) -> str:
    fallback = f"https://www.amazon.com.br/dp/{asin}?tag={AFFILIATE_TAG}"
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


# ============================================================
#  IMAGEM — Maior resolução disponível
# ============================================================
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


# ============================================================
#  SCRAPING — Dados de um produto
# ============================================================
async def scrape_product(page, asin: str, rank: int, category: str) -> dict:
    await page.goto(
        f"https://www.amazon.com.br/dp/{asin}",
        wait_until="domcontentloaded",
        timeout=30000,
    )
    await page.wait_for_timeout(1500)

    # Título
    try:
        title = (await page.locator("#productTitle").inner_text()).strip()
    except Exception:
        title = f"Produto {asin}"

    # Preço principal
    price = 0.0
    try:
        whole = (await page.locator(".a-price-whole").first.inner_text()).strip()
        frac = (await page.locator(".a-price-fraction").first.inner_text()).strip()
        price = parse_price(whole.replace(",", "").replace(".", "") + "." + frac)
    except Exception:
        pass

    # Preço original (tachado)
    original_price = 0.0
    try:
        orig = await page.locator(
            ".a-price.a-text-price[data-a-strike='true'] .a-offscreen"
        ).first.inner_text()
        original_price = parse_price(orig)
    except Exception:
        pass

    # Descrição (primeiro bullet relevante)
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
    amazon_url = await get_short_link(page, asin)

    return {
        "id": str(rank),
        "name": title,
        "slug": slugify(title),
        "price": price,
        "originalPrice": original_price if original_price > price else 0.0,
        "image": image,
        "amazonUrl": amazon_url,
        "category": category,
        "featured": rank <= 3,
        "bestSeller": True,
        "description": description,
    }


# ============================================================
#  SCRAPING — Top N ASINs de uma categoria
# ============================================================
async def get_top_asins(page, url: str, top_n: int) -> list[str]:
    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
    await page.wait_for_timeout(2000)

    items = page.locator(".zg-grid-general-faceout")
    count = await items.count()
    log(f"  {count} itens encontrados na página de mais vendidos.")

    asins = []
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


# ============================================================
#  SALVAR RESULTADO
# ============================================================
def save_output(data: dict):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Um JSON por categoria
    for category, products in data.items():
        path = os.path.join(OUTPUT_DIR, f"{category}_top{TOP_N}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(products, f, ensure_ascii=False, indent=2)
        log(f"Salvo: {path} ({len(products)} produtos)", "OK")

    # JSON consolidado com todas as categorias
    all_products = [p for prods in data.values() for p in prods]
    consolidated_path = os.path.join(OUTPUT_DIR, f"all_categories_{timestamp}.json")
    with open(consolidated_path, "w", encoding="utf-8") as f:
        json.dump(all_products, f, ensure_ascii=False, indent=2)
    log(f"Consolidado: {consolidated_path} ({len(all_products)} produtos no total)", "OK")


# ============================================================
#  MAIN
# ============================================================
async def main():
    log("Iniciando scraper Amazon Top Products", "STEP")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,  # Mude para True após confirmar que tudo funciona
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

        # ── Login ────────────────────────────────────────────
        cookies_loaded = await load_cookies(context)
        await ensure_logged_in(page, context)

        # ── Processar cada categoria ──────────────────────────
        all_data = {}

        for category_key, category_info in CATEGORIES.items():
            log(f"\nCategoria: {category_info['label']} ({category_key})", "STEP")

            asins = await get_top_asins(page, category_info["url"], TOP_N)
            log(f"  ASINs coletados: {asins}")

            products = []
            for rank, asin in enumerate(asins, start=1):
                try:
                    log(f"  Produto #{rank}/{len(asins)} — ASIN: {asin}")
                    product = await scrape_product(page, asin, rank, category_key)
                    products.append(product)
                    log(
                        f"  #{rank} ✓ {product['name'][:55]}... | "
                        f"R${product['price']} | {product['amazonUrl']}",
                        "OK",
                    )
                except Exception as e:
                    log(f"  Erro no produto #{rank} ({asin}): {e}", "ERROR")

                await asyncio.sleep(1.2)  # Pausa entre produtos

            all_data[category_key] = products
            log(f"  {len(products)} produtos coletados para '{category_key}'", "OK")
            await asyncio.sleep(2)  # Pausa entre categorias

        # ── Salvar resultados ─────────────────────────────────
        log("\nSalvando arquivos...", "STEP")
        save_output(all_data)

        log("\nConcluído!", "OK")
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())