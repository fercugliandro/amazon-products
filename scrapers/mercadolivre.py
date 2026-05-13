"""Scraper de ofertas relâmpago do Mercado Livre via requests (sync)."""
import re
import time
from typing import Generator
from urllib.parse import urlparse, urlunparse

import requests
from bs4 import BeautifulSoup

from affiliate import ml_affiliate_link
from config import (
    ML_DEFAULT_CATEGORY,
    ML_KEYWORD_CATEGORY_MAP,
    ML_OFFERS_URL,
    ML_PAGE_SIZE,
    ML_REQUEST_DELAY,
)
from utils import log, slugify

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)

_PRICE_RE = re.compile(
    r"(?:Agora|Antes):\s*([\d.]+)\s*reais?(?:\s*com\s*(\d+)\s*centavos)?",
    re.IGNORECASE,
)
_WID_RE = re.compile(r"wid=(MLB\d+)")
_MLB_ID_RE = re.compile(r"/(p/)?(MLB\d+)")


# ── Helpers ──────────────────────────────────────────────────────────────────────

def _parse_price(aria: str) -> float:
    m = _PRICE_RE.search(aria)
    if not m:
        return 0.0
    reais = float(m.group(1).replace(".", ""))
    centavos = float(m.group(2) or 0) / 100
    return round(reais + centavos, 2)


def _infer_category(title: str) -> str:
    title_lower = title.lower()
    for category, keywords in ML_KEYWORD_CATEGORY_MAP.items():
        for kw in keywords:
            if kw in title_lower:
                return category
    return ML_DEFAULT_CATEGORY


def _extract_id(url: str) -> str:
    m = _WID_RE.search(url)
    if m:
        return m.group(1)
    m = _MLB_ID_RE.search(url)
    if m:
        return m.group(2)
    return url.split("?")[0].rstrip("/").split("/")[-1]


def _clean_url(url: str) -> str:
    parsed = urlparse(url)
    return urlunparse(parsed._replace(query="", fragment=""))


# ── Parser de card ───────────────────────────────────────────────────────────────

def _parse_card(card, position: int) -> dict | None:
    title_tag = card.select_one(".poly-component__title")
    if not title_tag:
        return None
    title = title_tag.get_text(strip=True)

    link_tag = card.select_one("a[href*='mercadolivre.com.br']")
    if not link_tag:
        link_tag = card.select_one("a[href*='mercadolibre.com']")
    if not link_tag:
        return None
    raw_url = link_tag.get("href", "")
    product_url = _clean_url(raw_url)
    product_id = _extract_id(raw_url)

    img_tag = card.select_one("img.poly-component__picture")
    image = img_tag.get("src", "") if img_tag else ""

    current_price = 0.0
    original_price = 0.0
    for tag in card.select("[aria-label]"):
        aria = tag.get("aria-label", "")
        if "Agora" in aria:
            current_price = _parse_price(aria)
        elif "Antes" in aria:
            original_price = _parse_price(aria)

    category = _infer_category(title)
    discount_pct = 0
    if original_price > 0 and current_price > 0:
        discount_pct = round((1 - current_price / original_price) * 100)

    description = (
        f"Oferta relâmpago no Mercado Livre. "
        f"{f'Desconto de {discount_pct}% sobre o preço original.' if discount_pct > 0 else ''}"
    ).strip()

    return {
        "id": product_id,
        "name": title,
        "slug": slugify(title),
        "price": current_price,
        "originalPrice": original_price,
        "image": image,
        "productUrl": ml_affiliate_link(product_url),
        "source": "mercadolivre",
        "category": category,
        "featured": discount_pct >= 30,
        "bestSeller": False,
        "description": description,
    }


# ── Paginação ────────────────────────────────────────────────────────────────────

def _fetch_page(page: int) -> list[dict]:
    url = f"{ML_OFFERS_URL}?page={page}"
    try:
        resp = SESSION.get(url, timeout=20)
        resp.raise_for_status()
    except requests.RequestException as e:
        log(f"Falha ao buscar página {page}: {e}", "ERROR")
        return []

    soup = BeautifulSoup(resp.text, "lxml")
    cards = soup.select(".poly-card") or soup.select("[class*='poly-card']")

    products: list[dict] = []
    for i, card in enumerate(cards):
        product = _parse_card(card, i)
        if product:
            products.append(product)

    return products


def fetch_all_flash_deals(
    max_pages: int = 5,
    delay: float = ML_REQUEST_DELAY,
) -> Generator[dict, None, None]:
    """Gera produtos únicos das ofertas relâmpago (~20 por página)."""
    seen_ids: set[str] = set()

    for page in range(max_pages):
        log(f"Buscando página {page} ({ML_OFFERS_URL}?page={page})...")
        products = _fetch_page(page)

        if not products:
            log(f"Nenhum produto na página {page}. Encerrando.", "WARN")
            break

        new_count = 0
        for product in products:
            pid = product["id"]
            if pid in seen_ids:
                continue
            seen_ids.add(pid)
            new_count += 1
            yield product

        log(f"{new_count} novos produtos na página {page} ({len(products)} extraídos).")

        if len(products) < ML_PAGE_SIZE:
            log("Página com menos de 20 produtos — possível última página.", "WARN")
            break

        time.sleep(delay)


# ── Entry point ──────────────────────────────────────────────────────────────────

def run(
    max_pages: int = 5,
    delay: float = ML_REQUEST_DELAY,
    existing_ids: set[str] | None = None,
) -> list[dict]:
    """
    Raspa as ofertas relâmpago do Mercado Livre.
    Retorna lista de novos produtos (excluindo IDs já existentes).
    """
    if existing_ids is None:
        existing_ids = set()

    log("Iniciando scraper Mercado Livre Ofertas Relâmpago", "STEP")

    new_products: list[dict] = []
    for product in fetch_all_flash_deals(max_pages=max_pages, delay=delay):
        if product["id"] in existing_ids:
            continue
        existing_ids.add(product["id"])
        new_products.append(product)

    log(f"{len(new_products)} novos produtos encontrados no Mercado Livre.", "OK")
    return new_products
