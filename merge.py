import json
import os
from config import OUTPUT_DIR, PRODUTOS_JS_PATH
from utils import log, save_json, save_produtos_js

def main():
    log("Iniciando processo de unificação de catálogos...", "STEP")
    amazon_path = os.path.join(OUTPUT_DIR, "amazon_all.json")
    ml_path = os.path.join(OUTPUT_DIR, "ml_produtos.json")
    consolidated_json_path = os.path.join(OUTPUT_DIR, "produtos_consolidado.json")

    amazon_products = []
    if os.path.exists(amazon_path):
        try:
            with open(amazon_path, "r", encoding="utf-8") as f:
                amazon_products = json.load(f)
            log(f"Carregados {len(amazon_products)} produtos da Amazon.", "OK")
        except Exception as e:
            log(f"Erro ao carregar {amazon_path}: {e}", "ERROR")
    else:
        log(f"Arquivo da Amazon não encontrado em {amazon_path}. Ignorando.", "WARN")

    ml_products = []
    if os.path.exists(ml_path):
        try:
            with open(ml_path, "r", encoding="utf-8") as f:
                ml_products = json.load(f)
            log(f"Carregados {len(ml_products)} produtos do Mercado Livre.", "OK")
        except Exception as e:
            log(f"Erro ao carregar {ml_path}: {e}", "ERROR")
    else:
        log(f"Arquivo do Mercado Livre não encontrado em {ml_path}. Ignorando.", "WARN")

    # Unifica as listas
    combined = amazon_products + ml_products
    log(f"Total unificado: {len(combined)} produtos.", "OK")

    # Salva o JSON consolidado
    save_json(combined, consolidated_json_path)

    # Atualiza o produtos.js para exibição na web
    save_produtos_js(combined, PRODUTOS_JS_PATH)
    log("Exibição da web (produtos.js) atualizada com sucesso.", "OK")

if __name__ == "__main__":
    main()
