import json
import os

def analyze():
    filepath = "output/produtos_consolidado.json"
    if not os.path.exists(filepath):
        print("Arquivo nao encontrado.")
        return

    with open(filepath, "r", encoding="utf-8") as f:
        products = json.load(f)

    print(f"Total de produtos: {len(products)}")

    # Contagem por fonte
    sources = {}
    # Contagem por categoria
    categories = {}
    # Contagem por faixa de preco
    # Faixas: Ate R$ 50, R$ 50 a R$ 200, R$ 200 a R$ 500, R$ 500 a R$ 1000, Acima de R$ 1000
    price_ranges = {
        "Ate R$ 50": 0,
        "De R$ 50 a R$ 200": 0,
        "De R$ 200 a R$ 500": 0,
        "De R$ 500 a R$ 1000": 0,
        "Acima de R$ 1000": 0
    }

    for p in products:
        src = p.get("source", "desconhecido")
        sources[src] = sources.get(src, 0) + 1

        cat = p.get("category", "sem categoria")
        categories[cat] = categories.get(cat, 0) + 1

        price = p.get("price", 0)
        if price <= 50:
            price_ranges["Ate R$ 50"] += 1
        elif price <= 200:
            price_ranges["De R$ 50 a R$ 200"] += 1
        elif price <= 500:
            price_ranges["De R$ 200 a R$ 500"] += 1
        elif price <= 1000:
            price_ranges["De R$ 500 a R$ 1000"] += 1
        else:
            price_ranges["Acima de R$ 1000"] += 1

    print("\n--- Estatisticas por Fonte ---")
    for s, qty in sources.items():
        print(f"  {s}: {qty}")

    print("\n--- Estatisticas por Categoria ---")
    for c, qty in categories.items():
        print(f"  {c}: {qty}")

    print("\n--- Estatisticas por Faixa de Preco ---")
    for r, qty in price_ranges.items():
        print(f"  {r}: {qty}")

if __name__ == "__main__":
    analyze()
