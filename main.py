"""
Scraper unificado — Amazon Bestsellers + Mercado Livre Ofertas Relâmpago.

Exemplos:
  python main.py                            # ambas as fontes
  python main.py --source amazon            # só Amazon
  python main.py --source mercadolivre      # só Mercado Livre
  python main.py --source mercadolivre --pages 10 --delay 2.0
  python main.py --source mercadolivre --validate-only
  python main.py --source mercadolivre --reset --skip-validation
  python main.py --top-n 5                  # top 5 produtos por categoria Amazon
"""
import argparse
import asyncio

import scrapers.amazon as amazon_scraper
import scrapers.mercadolivre as ml_scraper
from config import (
    AMAZON_TOP_N,
    ML_OUTPUT_FILE,
    ML_REQUEST_DELAY,
    OUTPUT_DIR,
    PRODUTOS_JS_PATH,
)
from utils import (
    load_existing,
    log,
    save_amazon_output,
    save_json,
    save_produtos_js,
)
from validator import validate_prices


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Scraper de afiliados — Amazon Bestsellers + ML Ofertas Relâmpago"
    )
    parser.add_argument(
        "--source",
        choices=["amazon", "mercadolivre", "all"],
        default="all",
        help="Fonte de dados (default: all)",
    )

    # ── Amazon ────────────────────────────────────────────────────────────────
    parser.add_argument(
        "--top-n",
        type=int,
        default=AMAZON_TOP_N,
        help=f"Produtos por categoria na Amazon (default: {AMAZON_TOP_N})",
    )

    # ── Mercado Livre ─────────────────────────────────────────────────────────
    parser.add_argument(
        "--pages",
        type=int,
        default=5,
        help="Páginas de ofertas relâmpago do ML (default: 5)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=ML_REQUEST_DELAY,
        help=f"Delay entre requisições ML em segundos (default: {ML_REQUEST_DELAY})",
    )
    parser.add_argument(
        "--output",
        default=ML_OUTPUT_FILE,
        help=f"JSON de saída do ML (default: {ML_OUTPUT_FILE})",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Ignora o JSON existente do ML e recomeça do zero",
    )
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Pula a validação de preços dos produtos ML existentes",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Só valida preços ML, sem buscar novos produtos",
    )

    return parser


async def run_amazon(top_n: int) -> list[dict]:
    data = await amazon_scraper.run(top_n=top_n)
    return save_amazon_output(data, OUTPUT_DIR, top_n)


def run_mercadolivre(args) -> list[dict]:
    if args.reset:
        existing_products, existing_ids = [], set()
        log("Modo reset: começando do zero.", "INFO")
    else:
        existing_products, existing_ids = load_existing(args.output)
        log(f"{len(existing_products)} produtos ML existentes carregados.")

    if existing_products and not args.skip_validation:
        existing_products = validate_prices(existing_products, delay=args.delay)
        existing_ids = {p["id"] for p in existing_products}

    if args.validate_only:
        all_products = existing_products
    else:
        log("Buscando novos produtos nas ofertas relâmpago do ML...")
        new_products = ml_scraper.run(
            max_pages=args.pages,
            delay=args.delay,
            existing_ids=existing_ids,
        )
        log(f"{len(new_products)} novos produtos ML encontrados.")
        all_products = existing_products + new_products

    log(f"Total ML: {len(all_products)} produtos.")
    save_json(all_products, args.output)
    save_produtos_js(all_products, PRODUTOS_JS_PATH)

    return all_products


async def main() -> None:
    args = build_parser().parse_args()

    amazon_products: list[dict] = []
    ml_products: list[dict] = []

    if args.source in ("amazon", "all"):
        amazon_products = await run_amazon(args.top_n)

    if args.source in ("mercadolivre", "all"):
        ml_products = run_mercadolivre(args)

    if args.source == "all":
        all_combined = amazon_products + ml_products
        log(f"\nTotal combinado: {len(all_combined)} produtos ({len(amazon_products)} Amazon + {len(ml_products)} ML).", "OK")

    log("Concluído!", "OK")


if __name__ == "__main__":
    asyncio.run(main())
