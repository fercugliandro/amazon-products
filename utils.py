import json
import os
import re
import unicodedata
from datetime import datetime


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
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    try:
        return round(float(text), 2)
    except ValueError:
        return 0.0


def log(msg: str, level: str = "INFO") -> None:
    icons = {"INFO": "ℹ️", "OK": "✅", "WARN": "⚠️", "ERROR": "❌", "STEP": "🔷"}
    icon = icons.get(level, "▸")
    try:
        print(f"{icon} {msg}")
    except UnicodeEncodeError:
        import sys
        safe_icons = {"INFO": "[INFO]", "OK": "[OK]", "WARN": "[WARN]", "ERROR": "[ERROR]", "STEP": "[STEP]"}
        safe_icon = safe_icons.get(level, "[INFO]")
        encoding = sys.stdout.encoding or "utf-8"
        full_msg = f"{safe_icon} {msg}"
        try:
            print(full_msg.encode(encoding, errors="replace").decode(encoding))
        except Exception:
            try:
                print(full_msg.encode("ascii", errors="replace").decode("ascii"))
            except Exception:
                pass


def save_json(products: list[dict], path: str) -> None:
    dir_part = os.path.dirname(path)
    if dir_part:
        os.makedirs(dir_part, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
    log(f"{len(products)} produtos salvos em '{path}'.", "OK")


def save_produtos_js(products: list[dict], path: str) -> None:
    dir_part = os.path.dirname(path)
    if dir_part:
        os.makedirs(dir_part, exist_ok=True)
    content = "const PRODUTOS_DATA = " + json.dumps(products, ensure_ascii=False, indent=2) + ";\n"
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    log(f"'{path}' atualizado com {len(products)} produtos.", "OK")


def load_existing(path: str) -> tuple[list[dict], set[str]]:
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                ids = {p["id"] for p in data}
                return data, ids
            except (json.JSONDecodeError, KeyError):
                pass
    return [], set()


def save_amazon_output(data: dict, output_dir: str, top_n: int) -> list[dict]:
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    for category, products in data.items():
        path = os.path.join(output_dir, f"amazon_{category}_top{top_n}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(products, f, ensure_ascii=False, indent=2)
        log(f"Salvo: {path} ({len(products)} produtos)", "OK")

    all_products = [p for prods in data.values() for p in prods]
    consolidated = os.path.join(output_dir, f"amazon_all_{timestamp}.json")
    with open(consolidated, "w", encoding="utf-8") as f:
        json.dump(all_products, f, ensure_ascii=False, indent=2)
    
    # Também salva no arquivo estável sem timestamp para facilitar o merge
    stable_path = os.path.join(output_dir, "amazon_all.json")
    with open(stable_path, "w", encoding="utf-8") as f:
        json.dump(all_products, f, ensure_ascii=False, indent=2)
        
    log(f"Consolidado Amazon: {consolidated} e {stable_path} ({len(all_products)} produtos)", "OK")

    return all_products
