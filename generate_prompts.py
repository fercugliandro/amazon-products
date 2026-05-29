import json
import os
import re

# Configurações de caminhos
CONSOLIDATED_JSON = r"C:\Users\ferna\development\amazon-products\output\produtos_consolidado.json"
AI_PROMPTS_JSON = r"C:\Users\ferna\development\amazon-products\output\ai_prompts.json"

def clean_product_name(name):
    # Remove termos de preços, voltagem ou descrições muito longas
    name = re.sub(r",?\s*(110v|220v|127v|Bivolt).*", "", name, flags=re.IGNORECASE)
    name = re.sub(r",?\s*Blister com \d+.*", "", name, flags=re.IGNORECASE)
    name = re.sub(r"\s*-\s*Preto.*", "", name, flags=re.IGNORECASE)
    name = re.sub(r"\s*-\s*Branco.*", "", name, flags=re.IGNORECASE)
    # Pega os primeiros termos mais representativos do produto
    parts = name.split(",")
    if parts:
        name = parts[0].strip()
    parts = name.split(" - ")
    if parts:
        name = parts[0].strip()
    return name

def translate_to_english(name, category):
    name_lower = name.lower()
    
    # Mapeamento manual de tradução para os top produtos identificados
    translations = {
        "pilha alcalina, elgin, palito aaa": "Elgin AAA alkaline batteries pack",
        "pilha alcalina": "AAA alkaline batteries pack",
        "celular samsung galaxy a17": "Samsung Galaxy A17 smartphone, sleek modern slate design",
        "celular samsung galaxy a07": "Samsung Galaxy A07 smartphone, modern design",
        "controle sem fio microsoft xbox": "Microsoft Xbox Wireless Controller, sleek white design",
        "havit headphone fone de ouvido h2002d": "Havit H2002d pro gaming headphone with microphone",
        "controle dualshock 4": "PlayStation 4 Dualshock 4 Wireless Controller",
        "l'oréal paris elseve óleo extraordinário finalizador capilar": "L'Oréal Paris Elseve Extraordinary Hair Oil premium gold glass bottle",
        "la roche-posay cicaplast baume b5+ cuidado multirreparador c": "La Roche-Posay Cicaplast Baume B5+ soothing skin cream tube",
        "nivea sabonete líquido óleo de banho 200ml": "Nivea Luxury Bath Oil Shower Gel bottle",
        "sanduicheira elétrica cadence click": "Cadence Click automatic sandwich maker toaster",
        "filtro/refil original de água acqua pure": "Acqua Pure water filter cartridge replacement",
        "mixer vertical turbo chef elgin 3 em 1 200w preto": "Elgin Turbo Chef 3-in-1 Hand Blender Mixer",
    }
    
    # Procura por correspondência exata ou aproximada
    for key, val in translations.items():
        if key in name_lower or name_lower in key:
            return val
            
    # Traduções simples genéricas
    if "samsung galaxy" in name_lower:
        return "Samsung Galaxy Smartphone"
    if "pilha" in name_lower:
        return "Alkaline batteries"
    if "fone de ouvido" in name_lower or "headphone" in name_lower:
        return "Premium gaming headphones"
    if "controle" in name_lower:
        return "Wireless gaming controller"
    if "óleo" in name_lower:
        return "Premium hair care oil bottle"
    if "sabonete" in name_lower:
        return "Skincare cosmetic wash bottle"
    if "sanduicheira" in name_lower:
        return "Electric kitchen sandwich toaster"
    if "mixer" in name_lower:
        return "Vertical food hand blender"
        
    return name

def build_prompt(eng_name, category):
    if category == "tech":
        return (
            f"A professional commercial studio product photograph of a {eng_name}. "
            f"The item is positioned center, standing upright on a sleek black reflective mirror glass platform. "
            f"Electric blue and vibrant cyan circular neon rings glowing brightly behind it, dark metallic futuristic sci-fi studio background, "
            f"subtle volumetric smoky atmosphere, high-end high-tech luxury advertising, hyperrealistic, award-winning studio product photography, 8k, dramatic lighting."
        )
    elif category == "gaming":
        return (
            f"A high-fidelity commercial advertising photo of a {eng_name}. "
            f"The controller is centered on a glowing geometric podium with sharp neon lines. "
            f"Dark abstract background with glowing circuit board patterns, ambient purple and orange gaming studio lighting, "
            f"casting sleek specular reflections on the product surface, energetic gaming setup look, hyperrealistic, sharp focus, 8k."
        )
    elif category == "beauty":
        return (
            f"An elegant luxury commercial cosmetics product photograph of a {eng_name}. "
            f"The product bottle stands centered on a minimalist textured light beige travertine stone block podium. "
            f"Soft warm natural morning sunlight beam casting delicate, organic olive leaf shadows in the background. "
            f"Calm pastel pink and beige neutral background, delicate floating jasmine petals, tiny crystal-clear water droplets, "
            f"highly aesthetic, clean, serene, premium editorial skincare catalog photography, ultra high resolution."
        )
    elif category in ["home", "kitchen", "appliances"]:
        return (
            f"A professional interior design magazine product shot of a {eng_name}. "
            f"The product stands elegantly on a warm rustic oak wooden kitchen countertop. "
            f"Cozy modern Scandinavian kitchen background with soft morning sunlight streaming in from a side window, "
            f"subtle green house plants softly blurred in the background, elegant and inviting home atmosphere, "
            f"natural warm lighting, premium lifestyle catalog, sharp focus, 8k."
        )
    else:
        return (
            f"A premium commercial product advertising photograph of a {eng_name}. "
            f"The product is standing upright on a sleek, minimalist matte concrete cylindrical podium. "
            f"Elegant warm gray soft gradient studio backdrop, subtle dramatic studio spotlight, clean geometric shapes, "
            f"minimalist aesthetic, award-winning product catalog photography, sharp focus, highly detailed."
        )

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Gerador de Prompts de IA para Produtos")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Gera prompts para todos os produtos do catálogo"
    )
    parser.add_argument(
        "--featured",
        action="store_true",
        help="Gera prompts apenas para os produtos em destaque (padrão)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limite máximo de produtos a processar"
    )
    parser.add_argument(
        "--target-only",
        action="store_true",
        help="Gera apenas para os 6 produtos icônicos clássicos para teste rápido"
    )
    args = parser.parse_args()

    print("Iniciando geração de prompts de IA...")
    if not os.path.exists(CONSOLIDATED_JSON):
        print(f"Erro: Arquivo consolidado {CONSOLIDATED_JSON} não encontrado.")
        return

    with open(CONSOLIDATED_JSON, "r", encoding="utf-8") as f:
        products = json.load(f)

    # Determinar se processa todos ou apenas destacados por padrão
    # Se nem --all nem --target-only forem passados, o padrão é processar os em destaque (featured).
    only_featured = not args.all
    if args.target_only:
        only_featured = True

    featured_products = [p for p in products if p.get("featured")]
    
    if args.target_only:
        # Lógica original para os 6 produtos clássicos
        target_slugs = [
            "celular-samsung-galaxy-a17-256gb-8gb-50mp-tela-67-ip54-preto",
            "controle-sem-fio-microsoft-xbox-branco",
            "havit-headphone-fone-de-ouvido-h2002d-gamer-com-microfone",
            "loreal-paris-elseve-oleo-extraordinario-finalizador-capilar",
            "la roche-posay cicaplast baume b5+ cuidado multirreparador c",
            "sanduicheira-eletrica-cadence-click-127v"
        ]
        selected_products = []
        for prod in featured_products:
            slug = prod.get("slug", "")
            norm_slug = slug.lower().strip()
            is_target = False
            for ts in target_slugs:
                if ts in norm_slug or norm_slug in ts:
                    is_target = True
                    break
            if is_target and prod not in selected_products:
                selected_products.append(prod)

        categories_seen = {prod.get("category") for prod in selected_products}
        if len(selected_products) < 5:
            for prod in featured_products:
                cat = prod.get("category")
                if cat not in categories_seen and len(selected_products) < 6:
                    selected_products.append(prod)
                    categories_seen.add(cat)
        
        print(f"Modo target-only: Selecionados {len(selected_products)} produtos icônicos de teste.")
    
    else:
        # Novo fluxo flexível
        if only_featured:
            selected_products = featured_products
            print(f"Modo featured: Processando todos os {len(selected_products)} produtos em destaque.")
        else:
            selected_products = products
            print(f"Modo completo: Processando todos os {len(selected_products)} produtos do catálogo.")

    # Aplicar limite se houver
    if args.limit is not None:
        selected_products = selected_products[:args.limit]
        print(f"Aplicado limite de processamento: {args.limit} produtos.")

    print(f"Preparando prompts para {len(selected_products)} produtos...")
    
    ai_prompts = []
    for idx, prod in enumerate(selected_products):
        name = prod.get("name", "")
        clean_name = clean_product_name(name)
        category = prod.get("category", "other")
        
        # Ajuste específico de categoria de gaming
        if "xbox" in name.lower() or "headphone" in name.lower() or "dualshock" in name.lower():
            category = "gaming"
            
        eng_name = translate_to_english(clean_name, category)
        prompt = build_prompt(eng_name, category)
        
        prompt_item = {
            "id": prod.get("id"),
            "name": name,
            "slug": prod.get("slug"),
            "category": category,
            "eng_name": eng_name,
            "prompt": prompt,
            "original_image": prod.get("image")
        }
        ai_prompts.append(prompt_item)
        print(f"[{idx+1}] Slug: {prod.get('slug')} | Categoria: {category} -> English: {eng_name}")

    # Salvar prompts em JSON
    os.makedirs(os.path.dirname(AI_PROMPTS_JSON), exist_ok=True)
    with open(AI_PROMPTS_JSON, "w", encoding="utf-8") as out_f:
        json.dump(ai_prompts, out_f, indent=2, ensure_ascii=False)
        
    print(f"\nSuccess: Prompts gerados e salvos com sucesso em: {AI_PROMPTS_JSON}")

if __name__ == "__main__":
    main()
