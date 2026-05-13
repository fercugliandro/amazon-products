"""
Corrige links de afiliado no JSON já gerado, sem raspar o site novamente.
Uso:
  python fix_links.py                     # corrige ML e Amazon no arquivo padrão
  python fix_links.py --input output/ml_produtos.json
"""
import argparse
import json
import re

from affiliate import amazon_affiliate_link, ml_affiliate_link
from config import ML_OUTPUT_FILE, PRODUTOS_JS_PATH
from utils import log, save_produtos_js

_SEC_RE = re.compile(r"https://mercadolivre\.com/sec/[^?]+\?redirect=(.+)")


def _fix_ml_url(url: str) -> str:
    m = _SEC_RE.match(url)
    clean = m.group(1) if m else url
    return ml_affiliate_link(clean)


def _fix_amazon_url(product: dict) -> str:
    asin = product.get("id", "")
    return amazon_affiliate_link(asin) if asin else product.get("productUrl", "")


def fix(path: str, sync_js: bool = True) -> None:
    with open(path, "r", encoding="utf-8") as f:
        products = json.load(f)

    for p in products:
        source = p.get("source", "mercadolivre")
        if source == "amazon":
            p["productUrl"] = _fix_amazon_url(p)
        else:
            p["productUrl"] = _fix_ml_url(p["productUrl"])

    with open(path, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

    log(f"{len(products)} links corrigidos em '{path}'.", "OK")
    if products:
        log(f"Exemplo: {products[0]['productUrl']}", "INFO")

    if sync_js:
        save_produtos_js(products, PRODUTOS_JS_PATH)


def main() -> None:
    parser = argparse.ArgumentParser(description="Corrige links de afiliado no JSON gerado.")
    parser.add_argument("--input", default=ML_OUTPUT_FILE, help="Arquivo JSON a corrigir.")
    parser.add_argument("--no-js", action="store_true", help="Não atualizar produtos.js.")
    args = parser.parse_args()

    fix(args.input, sync_js=not args.no_js)


if __name__ == "__main__":
    main()
