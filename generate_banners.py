import json
import os
import re
import asyncio
from playwright.async_api import async_playwright
from utils import log

# Configurações de caminhos
CONSOLIDATED_JSON = r"C:\Users\ferna\development\amazon-products\output\produtos_consolidado.json"
BANNERS_DIR = r"C:\Users\ferna\development\amazon-products\output\banners"
TEMP_HTML_DIR = r"C:\Users\ferna\development\amazon-products\output\temp_html"
AI_IMAGES_DIR = r"C:\Users\ferna\development\amazon-products\output\ai_images"

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Achadinho – {name_escaped}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}

  body {{
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    background: #111;
    font-family: 'Segoe UI', Arial, sans-serif;
  }}

  .card {{
    width: 540px;
    height: 960px;
    position: relative;
    overflow: hidden;
    background: linear-gradient(160deg, #e8f4ff 0%, #c8dff7 40%, #b0cff0 100%);
    border-radius: 0;
  }}

  /* ── Background blobs ── */
  .blob {{
    position: absolute;
    border-radius: 50%;
    filter: blur(60px);
    pointer-events: none;
  }}
  .blob-left  {{ width: 280px; height: 380px; background: rgba(0,90,220,.28); left: -80px; top: 140px; }}
  .blob-right {{ width: 300px; height: 380px; background: rgba(0,90,220,.24); right: -80px; top: 80px; }}
  .blob-bot   {{ width: 260px; height: 260px; background: rgba(0,110,240,.18); right: 20px; bottom: 160px; }}

  /* ── Tech rings ── */
  .ring {{
    position: absolute;
    border-radius: 50%;
    border: 1.5px solid rgba(0,120,255,.22);
    pointer-events: none;
  }}
  .r1 {{ width: 200px; height: 200px; left: -40px; top: 280px; }}
  .r2 {{ width: 260px; height: 260px; left: -70px; top: 250px; }}
  .r3 {{ width: 220px; height: 220px; right: -50px; top: 220px; }}
  .r4 {{ width: 280px; height: 280px; right: -80px; top: 190px; }}

  /* ── Shopping bags ── */
  .bag {{
    position: absolute;
    pointer-events: none;
    opacity: .85;
  }}
  .bag svg {{ display: block; }}
  .bag-left  {{ left: 14px; top: 310px; }}
  .bag-right {{ right: 18px; top: 90px; }}
  .bag-btm   {{ left: 10px; top: 580px; opacity: .55; }}

  /* ── ACHADINHO title ── */
  .title-wrap {{
    position: absolute;
    top: 18px;
    width: 100%;
    text-align: center;
  }}
  .title {{
    font-size: 44px;
    font-weight: 900;
    font-style: italic;
    letter-spacing: 1px;
    color: #ff9800;
    text-shadow:
      2.5px 2.5px 0 #b84a00,
      1.5px 1.5px 0 #c05500,
      0.5px 0.5px 0 #d06000,
      0 0 20px rgba(255,160,0,.6),
      0 0 40px rgba(255,120,0,.3);
    -webkit-text-stroke: 1px rgba(255,200,50,.4);
  }}

  /* ── Product card ── */
  .product-card {{
    position: absolute;
    left: 40px;
    top: 130px;
    width: 460px;
    height: 530px;
    background: #fff;
    border-radius: 24px;
    border: 3px solid #0064dc;
    box-shadow:
      0 0 0 1px rgba(255,180,0,.5),
      0 0 24px rgba(255,160,0,.35),
      0 8px 40px rgba(0,60,180,.25);
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: visible;
  }}

  .product-img {{
    width: 88%;
    height: 88%;
    object-fit: contain;
    border-radius: 16px;
  }}

  /* ── Discount badge ── */
  .badge {{
    position: absolute;
    top: -18px;
    right: -18px;
    width: 80px;
    height: 80px;
    background: radial-gradient(circle at 40% 35%, #ff5252, #cc0000);
    border-radius: 50%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    box-shadow: 0 0 20px rgba(220,0,0,.55);
    z-index: 10;
    display: {badge_display};
  }}
  .badge-pct  {{ font-size: 22px; font-weight: 900; color: #fff; line-height: 1.1; }}
  .badge-off  {{ font-size: 13px; font-weight: 800; color: #ffd0d0; letter-spacing: 1px; }}

  /* ── Price tag ── */
  .tag-wrap {{
    position: absolute;
    left: 50%;
    transform: translateX(-50%);
    bottom: 208px;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;
    z-index: 5;
  }}

  .tag {{
    width: 290px;
    height: 60px;
    background: linear-gradient(135deg, #ff8c00, #e65c00);
    border-radius: 30px;
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    box-shadow:
      0 0 0 2px rgba(255,180,0,.6),
      0 0 24px rgba(255,140,0,.7),
      0 4px 16px rgba(180,60,0,.4);
  }}
  .tag::before {{
    content: '';
    position: absolute;
    top: 5px; left: 5px; right: 5px;
    height: 40%;
    background: linear-gradient(to bottom, rgba(255,255,255,.22), transparent);
    border-radius: 30px 30px 60% 60%;
  }}
  .tag-hole {{
    width: 14px; height: 14px;
    background: rgba(140,50,0,.8);
    border-radius: 50%;
    margin-right: 14px;
    flex-shrink: 0;
  }}
  .tag-price {{
    font-size: 26px;
    font-weight: 900;
    color: #fff;
    text-shadow: 0 1px 4px rgba(0,0,0,.3);
    letter-spacing: .5px;
  }}

  .tag-original {{
    font-size: 15px;
    color: rgba(60,60,90,.65);
    text-decoration: line-through;
    text-decoration-color: rgba(80,80,110,.6);
    letter-spacing: .3px;
    display: {original_price_display};
  }}

  /* ── Name bar ── */
  .name-bar {{
    position: absolute;
    left: 28px;
    right: 28px;
    bottom: 80px;
    background: rgba(235,242,255,.9);
    border: 2px solid rgba(0,100,220,.25);
    border-radius: 28px;
    padding: 12px 20px 10px;
    text-align: center;
    backdrop-filter: blur(6px);
  }}
  .name-main {{ font-size: 17px; font-weight: 700; color: #0f1e50; }}
  .name-sub  {{ font-size: 12px; color: #3a5080; margin-top: 3px; }}

  /* ── Badges row ── */
  .badges-row {{
    position: absolute;
    bottom: 50px;
    width: 100%;
    display: flex;
    justify-content: center;
    gap: 8px;
  }}
  .pill {{
    background: rgba(0,80,200,.85);
    color: #fff;
    font-size: 11px;
    font-weight: 700;
    padding: 4px 14px;
    border-radius: 20px;
    letter-spacing: .5px;
  }}

  /* ── Handle ── */
  .handle {{
    position: absolute;
    bottom: 14px;
    width: 100%;
    text-align: center;
    font-size: 14px;
    color: rgba(50,60,90,.65);
    letter-spacing: .5px;
  }}

  /* ── Logo repeat small ── */
  .logo-small {{
    position: absolute;
    bottom: 168px;
    width: 100%;
    text-align: center;
    font-size: 18px;
    font-weight: 900;
    font-style: italic;
    color: rgba(200,80,0,.8);
    letter-spacing: 1px;
    text-shadow: 1px 1px 0 rgba(180,60,0,.4);
  }}
</style>
</head>
<body>
<div class="card">

  <!-- blobs -->
  <div class="blob blob-left"></div>
  <div class="blob blob-right"></div>
  <div class="blob blob-bot"></div>

  <!-- rings -->
  <div class="ring r1"></div>
  <div class="ring r2"></div>
  <div class="ring r3"></div>
  <div class="ring r4"></div>

  <!-- shopping bags -->
  <div class="bag bag-left">
    <svg width="52" height="58" viewBox="0 0 52 58" fill="none">
      <rect x="4" y="18" width="44" height="36" rx="6" fill="#ff9800"/>
      <path d="M16 18 C16 8 36 8 36 18" stroke="#ff9800" stroke-width="5" fill="none" stroke-linecap="round"/>
      <rect x="4" y="18" width="44" height="36" rx="6" fill="url(#bg1)" opacity=".3"/>
      <defs><linearGradient id="bg1" x1="26" y1="18" x2="26" y2="54" gradientUnits="userSpaceOnUse"><stop stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient></defs>
    </svg>
  </div>
  <div class="bag bag-right">
    <svg width="44" height="50" viewBox="0 0 44 50" fill="none">
      <rect x="3" y="16" width="38" height="30" rx="5" fill="#0064dc"/>
      <path d="M13 16 C13 7 31 7 31 16" stroke="#0064dc" stroke-width="4" fill="none" stroke-linecap="round"/>
      <rect x="3" y="16" width="38" height="30" rx="5" fill="url(#bg2)" opacity=".25"/>
      <defs><linearGradient id="bg2" x1="22" y1="16" x2="22" y2="46" gradientUnits="userSpaceOnUse"><stop stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient></defs>
    </svg>
  </div>
  <div class="bag bag-btm">
    <svg width="38" height="44" viewBox="0 0 38 44" fill="none">
      <rect x="2" y="14" width="34" height="27" rx="5" fill="#0064dc"/>
      <path d="M11 14 C11 6 27 6 27 14" stroke="#0064dc" stroke-width="4" fill="none" stroke-linecap="round"/>
    </svg>
  </div>

  <!-- Title -->
  <div class="title-wrap">
    <span class="title">ACHADINHOS POR AÍ</span>
  </div>

  <!-- Product card -->
  <div class="product-card">
    <div class="badge">
      <span class="badge-pct">{discount_pct}%</span>
      <span class="badge-off">OFF</span>
    </div>
    <img
      class="product-img"
      src="{image_url}"
      alt="{name_escaped}"
      onerror="this.style.display='none'; this.parentNode.innerHTML += '<div style=\\'text-align:center;color:#aaa;font-size:14px;padding:20px\\'>{name_escaped}</div>'"
    />
  </div>

  <!-- Price tag -->
  <div class="tag-wrap">
    <div class="tag">
      <div class="tag-hole"></div>
      <span class="tag-price">R$ {price_formatted}</span>
    </div>
    <span class="tag-original">de R$ {original_price_formatted}</span>
  </div>

  <!-- Product name bar -->
  <div class="name-bar">
    <div class="name-main">{name_truncated}</div>
    <div class="name-sub">{specs_formatted}</div>
  </div>

  <!-- Pill badges -->
  <div class="badges-row">
    {pills_html}
  </div>

  <!-- Small logo -->
  <div class="logo-small">&#127991; ACHADINHOS POR AÍ</div>

  <!-- Handle -->
  <div class="handle">@aachadinhosporaii_</div>

</div>
</body>
</html>
"""

def clean_html_entities(text: str) -> str:
    # Substituições básicas para evitar quebras em entidades HTML
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
    return text

def extract_specs(name: str, category: str) -> list:
    specs = []
    # Busca por especificações comuns no título
    gb_match = re.search(r"(\d+GB|\d+TB)", name, re.IGNORECASE)
    if gb_match:
        specs.append(gb_match.group(1).upper())
        
    ram_match = re.search(r"(\d+GB\s*RAM|\d+\s*GB\s*de\s*RAM)", name, re.IGNORECASE)
    if ram_match:
        specs.append(ram_match.group(1).upper())
    elif "RAM" in name.upper() and len(specs) < 2:
        # Tenta pegar antes da palavra RAM
        parts = re.search(r"(\d+\s*GB)\s*RAM", name, re.IGNORECASE)
        if parts:
            specs.append(f"{parts.group(1).strip()} RAM")

    # Resolução
    if "4K" in name.upper():
        specs.append("Resolução 4K")
    elif "SMART" in name.upper():
        specs.append("Smart TV")

    # Outros
    if "100% ALGODÃO" in name.upper() or "ALGODAO" in name.upper():
        specs.append("100% Algodão")

    # Fallbacks baseados na categoria
    if not specs:
        if category == "tech":
            specs = ["Tecnologia", "Alta Qualidade", "Mais Vendido"]
        elif category == "beauty":
            specs = ["Cuidados Pessoais", "Fragrância Premium", "Dermatologicamente Testado"]
        elif category == "home":
            specs = ["Utilidade Doméstica", "Design Moderno", "Resistente"]
        elif category == "sports":
            specs = ["Suplementação", "Alta Pureza", "Nutrição Esportiva"]
        else:
            specs = ["Super Oferta", "Qualidade Garantida", "Destaque"]

    return specs[:4]

def get_pills(specs: list, category: str) -> list:
    pills = []
    for spec in specs[:3]:
        pills.append(f"&#10022; {spec}")
    if not pills:
        pills = ["&#10022; Oferta", "&#10022; Destaque", "&#10022; Top"]
    return pills

async def generate_images(limit=None, only_featured=True, force=False):
    log("Iniciando geração de banners promocionais com Playwright...", "STEP")
    
    if not os.path.exists(CONSOLIDATED_JSON):
        log(f"Arquivo consolidado {CONSOLIDATED_JSON} não encontrado.", "ERROR")
        return

    with open(CONSOLIDATED_JSON, "r", encoding="utf-8") as f:
        products = json.load(f)

    # Filtrar produtos
    if only_featured:
        target_products = [p for p in products if p.get("featured")]
    else:
        target_products = products

    if limit is not None:
        target_products = target_products[:limit]

    if not target_products:
        log("Nenhum produto atendeu aos critérios de filtro. Usando os primeiros da lista.", "WARN")
        target_products = products
        if limit is not None:
            target_products = target_products[:limit]

    os.makedirs(BANNERS_DIR, exist_ok=True)
    os.makedirs(TEMP_HTML_DIR, exist_ok=True)

    log(f"Processando {len(target_products)} produtos...", "INFO")

    async with async_playwright() as p:
        # Lançar browser headless de alta fidelidade
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 540, "height": 960},
            device_scale_factor=2 # 2x scale para renderizar 1080x1920
        )
        page = await context.new_page()

        for idx, prod in enumerate(target_products):
            pid = prod.get("id", f"prod_{idx}")
            name = prod.get("name", "Produto")
            price = prod.get("price", 0.0)
            original_price = prod.get("originalPrice", 0.0)
            image_url = prod.get("image", "")
            category = prod.get("category", "geral")
            slug = prod.get("slug", f"produto-{idx}")

            # Verificar se existe imagem customizada gerada por IA localmente
            local_ai_image_path = os.path.join(AI_IMAGES_DIR, f"achadinho_{slug}.png")
            if os.path.exists(local_ai_image_path):
                # Utilizar esquema de URL de arquivo absoluto para o Playwright
                image_url = f"file:///{local_ai_image_path.replace(chr(92), '/')}"
                log(f"-> Carregando imagem gerada por IA: {slug}", "INFO")

            output_png_path = os.path.join(BANNERS_DIR, f"achadinho_{slug}.png")
            if os.path.exists(output_png_path) and not force:
                log(f"[{idx+1}/{len(target_products)}] [PULADO] Banner já existe para: {name[:40]}", "INFO")
                continue

            log(f"[{idx+1}/{len(target_products)}] Gerando banner para: {name[:40]}...")

            # Cálculo de desconto
            discount_pct = 0
            badge_display = "none"
            if original_price > price and original_price > 0:
                discount_pct = round((1 - price / original_price) * 100)
                badge_display = "flex"

            original_price_display = "inline" if original_price > price else "none"

            # Formatações de strings
            name_escaped = clean_html_entities(name)
            name_truncated = name_escaped if len(name_escaped) <= 45 else name_escaped[:42] + "..."
            
            price_formatted = f"{price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            original_price_formatted = f"{original_price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

            # Specs e Pills
            specs = extract_specs(name, category)
            specs_formatted = " &nbsp;&middot;&nbsp; ".join(specs)
            pills = get_pills(specs, category)
            pills_html = "\n    ".join([f'<span class="pill">{pill}</span>' for pill in pills])

            # Preencher template HTML
            html_content = HTML_TEMPLATE.format(
                name_escaped=name_escaped,
                name_truncated=name_truncated,
                discount_pct=discount_pct,
                badge_display=badge_display,
                image_url=image_url,
                price_formatted=price_formatted,
                original_price_formatted=original_price_formatted,
                original_price_display=original_price_display,
                specs_formatted=specs_formatted,
                pills_html=pills_html
            )

            # Salvar arquivo HTML temporário
            temp_html_path = os.path.join(TEMP_HTML_DIR, f"temp_{idx}.html")
            with open(temp_html_path, "w", encoding="utf-8") as tf:
                tf.write(html_content)

            # Carregar no Playwright
            await page.goto(f"file:///{temp_html_path.replace(chr(92), '/')}")
            # Pequeno delay para garantir que a imagem do produto baixou
            await page.wait_for_timeout(2500)

            # Tirar screenshot elemento .card
            card_element = page.locator(".card")
            await card_element.screenshot(path=output_png_path)
            
            log(f"✓ Banner salvo em: {output_png_path}", "OK")

            # Deletar arquivo temporário
            try:
                os.remove(temp_html_path)
            except Exception:
                pass

        await browser.close()

    log("✓ Geração de banners concluída com sucesso!", "OK")
    log(f"Todos os banners salvos na pasta: {BANNERS_DIR}", "OK")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Gerador de Banners Promocionais")
    parser.add_argument("--limit", type=int, default=None, help="Limite de produtos a processar")
    parser.add_argument("--all", action="store_true", help="Gera banners para todos os produtos (por padrão, gera apenas destacados)")
    parser.add_argument("--force", action="store_true", help="Força a geração do banner mesmo se já existir")
    
    args = parser.parse_args()
    
    # Se --all for passado, only_featured = False
    only_featured = not args.all
    
    # Se limit não for especificado e formos gerar apenas destacados, limita por padrão
    limit = args.limit
    if limit is None and only_featured:
        limit = 12
        
    asyncio.run(generate_images(limit=limit, only_featured=only_featured, force=args.force))
