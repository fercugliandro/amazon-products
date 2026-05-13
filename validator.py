"""Valida preços dos produtos do Mercado Livre já salvos em JSON."""
import re
import time
from urllib.parse import urlparse, urlunparse

import requests
from bs4 import BeautifulSoup

from config import ML_PRICE_INCREASE_TOLERANCE
from utils import log

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9",
}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)

_PRICE_RE = re.compile(
    r"Agora:\s*([\d.]+)\s*reais?(?:\s*com\s*(\d+)\s*centavos)?",
    re.IGNORECASE,
)


def _clean_url(product_url: str) -> str:
    parsed = urlparse(product_url)
    return urlunparse(parsed._replace(query="", fragment=""))


def _fetch_current_price(product_url: str) -> float | None:
    clean = _clean_url(product_url)
    try:
        resp = SESSION.get(clean, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        log(f"Não foi possível acessar {clean}: {e}", "ERROR")
        return None

    soup = BeautifulSoup(resp.text, "lxml")

    for tag in soup.select("[aria-label]"):
        aria = tag.get("aria-label", "")
        m = _PRICE_RE.search(aria)
        if m:
            reais = float(m.group(1).replace(".", ""))
            centavos = float(m.group(2) or 0) / 100
            return round(reais + centavos, 2)

    price_tag = soup.select_one(".andes-money-amount__fraction[aria-hidden='true']")
    if price_tag:
        cents_tag = soup.select_one(".andes-money-amount__cents[aria-hidden='true']")
        try:
            reais = float(price_tag.get_text(strip=True).replace(".", "").replace(",", "."))
            centavos = float((cents_tag.get_text(strip=True) if cents_tag else "0").replace(",", ".")) / 100
            return round(reais + centavos, 2)
        except ValueError:
            pass

    return None


def validate_prices(products: list[dict], delay: float = 1.0) -> list[dict]:
    """
    Verifica o preço atual de cada produto do ML.
    Remove produtos cujo preço subiu mais que ML_PRICE_INCREASE_TOLERANCE.
    Só processa produtos com source='mercadolivre' ou sem campo source.
    """
    ml_products = [p for p in products if p.get("source", "mercadolivre") == "mercadolivre"]
    other_products = [p for p in products if p.get("source") == "amazon"]

    if not ml_products:
        return products

    log(f"Validando preços de {len(ml_products)} produtos do Mercado Livre...", "STEP")

    valid: list[dict] = []
    total = len(ml_products)

    for i, product in enumerate(ml_products, 1):
        name_short = product["name"][:55]
        log(f"[{i}/{total}] {name_short}...")

        current_price = _fetch_current_price(product["productUrl"])

        if current_price is None:
            log("  Removido — não foi possível verificar preço.", "WARN")
            time.sleep(delay)
            continue

        stored_price = product["price"]
        increase = (current_price - stored_price) / stored_price if stored_price > 0 else 0

        if increase > ML_PRICE_INCREASE_TOLERANCE:
            log(
                f"  Removido — preço subiu de R${stored_price:.2f} "
                f"para R${current_price:.2f} (+{increase*100:.1f}%)",
                "WARN",
            )
        else:
            if current_price != stored_price:
                log(f"  Atualizado: R${stored_price:.2f} → R${current_price:.2f}", "OK")
                product["price"] = current_price
            else:
                log(f"  OK — R${current_price:.2f}", "OK")
            valid.append(product)

        time.sleep(delay)

    removed = total - len(valid)
    log(f"Validação concluída: {len(valid)} válidos, {removed} removidos.", "OK")

    return other_products + valid
