import os
import glob
import subprocess
import time
import argparse
import json
import re
from utils import log

# Configurações de caminhos
BANNERS_DIR = r"C:\Users\ferna\development\amazon-products\output\banners"
VIDEOS_DIR = r"C:\Users\ferna\development\amazon-products\output\videos"
CONSOLIDATED_JSON = r"C:\Users\ferna\development\amazon-products\output\produtos_consolidado.json"

def get_slug_category_map():
    """Retorna um mapeamento de slug para a categoria do produto."""
    if not os.path.exists(CONSOLIDATED_JSON):
        log(f"Arquivo consolidado {CONSOLIDATED_JSON} não encontrado. Usando categorias gerais.", "WARN")
        return {}
    try:
        with open(CONSOLIDATED_JSON, "r", encoding="utf-8") as f:
            products = json.load(f)
        return {p.get("slug"): p.get("category", "geral") for p in products if p.get("slug")}
    except Exception as e:
        log(f"Erro ao carregar mapa de categorias do catálogo: {e}", "WARN")
        return {}

def get_all_banners_list(shuffle_banners=False):
    """Retorna uma lista plana com todos os banners disponíveis."""
    pattern = os.path.join(BANNERS_DIR, "achadinho_*.png")
    banners = glob.glob(pattern)
    
    if not banners:
        log(f"Nenhum banner encontrado em {BANNERS_DIR}. Por favor, gere os banners primeiro.", "ERROR")
        return []
        
    log(f"Encontrados {len(banners)} banners em {BANNERS_DIR}.", "INFO")
    
    if shuffle_banners:
        import random
        random.shuffle(banners)
    else:
        banners.sort(key=os.path.getmtime, reverse=True)
        
    return banners

def get_banners_by_category(category_filter=None, shuffle_banners=False):
    """Agrupa banners por categoria com base nos slugs de arquivos de imagem."""
    pattern = os.path.join(BANNERS_DIR, "achadinho_*.png")
    banners = glob.glob(pattern)
    
    if not banners:
        log(f"Nenhum banner encontrado em {BANNERS_DIR}.", "ERROR")
        return {}
        
    slug_map = get_slug_category_map()
    
    # Agrupa banners por categoria
    categorized_banners = {}
    for banner in banners:
        filename = os.path.basename(banner)
        match = re.match(r"achadinho_(.+)\.png", filename)
        if match:
            slug = match.group(1)
            category = slug_map.get(slug, "geral")
        else:
            category = "geral"
            
        if category not in categorized_banners:
            categorized_banners[category] = []
        categorized_banners[category].append(banner)
        
    # Ordena/Embaralha os banners dentro de cada categoria
    for cat in list(categorized_banners.keys()):
        if shuffle_banners:
            import random
            random.shuffle(categorized_banners[cat])
        else:
            categorized_banners[cat].sort(key=os.path.getmtime, reverse=True)
            
    if category_filter:
        filtered_banners = []
        # Casamento flexível (busca por substring, ex: 'pets' bate com 'pets_cachorro' e 'pets_gato')
        for cat, items in categorized_banners.items():
            if category_filter.lower() in cat.lower():
                filtered_banners.extend(items)
        if not filtered_banners:
            log(f"Nenhum banner encontrado para o filtro de categoria '{category_filter}'.", "WARN")
            return {}
        log(f"Encontrados {len(filtered_banners)} banners correspondentes à categoria '{category_filter}'.", "INFO")
        return {category_filter: filtered_banners}
        
    return categorized_banners

def compile_video_ffmpeg(banners, output_path, duration=3.0, trans_duration=0.5, transition_style="fade"):
    if len(banners) < 2:
        log("São necessários pelo menos 2 banners para criar um vídeo com transições.", "ERROR")
        return False
        
    cmd = ["ffmpeg", "-y"]
    
    for banner in banners:
        cmd.extend([
            "-loop", "1",
            "-t", f"{duration}",
            "-i", banner
        ])
        
    filter_complex = []
    last_label = "0:v"
    
    for i in range(1, len(banners)):
        next_input = f"{i}:v"
        offset = i * (duration - trans_duration)
        output_label = f"v{i}"
        
        expr = f"[{last_label}][{next_input}]xfade=transition={transition_style}:duration={trans_duration}:offset={offset:.2f}"
        
        if i == len(banners) - 1:
            expr += "[outv]"
        else:
            expr += f"[{output_label}]"
            
        filter_complex.append(expr)
        last_label = output_label
        
    filter_complex_str = ";".join(filter_complex)
    
    cmd.extend([
        "-filter_complex", filter_complex_str,
        "-map", "[outv]",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-r", "25",
        output_path
    ])
    
    total_duration = len(banners) * duration - (len(banners) - 1) * trans_duration
    log(f"Comando FFmpeg gerado. Duração prevista do vídeo: {total_duration:.1f} segundos.", "INFO")
    
    try:
        log("Executando FFmpeg... Por favor, aguarde.", "INFO")
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        log(f"✓ Vídeo Reels/Shorts compilado com sucesso!", "OK")
        log(f"Salvo em: {output_path}", "OK")
        return True
    except subprocess.CalledProcessError as e:
        log("Ocorreu um erro ao executar o FFmpeg:", "ERROR")
        err_msg = e.stderr if e.stderr else "Erro desconhecido no FFmpeg."
        log(err_msg, "ERROR")
        return False
    except Exception as ex:
        log(f"Ocorreu uma exceção inesperada: {str(ex)}", "ERROR")
        return False

def generate_video(duration=3.0, trans_duration=0.5, transition_style="fade", count=15, 
                   shuffle_banners=False, output_filename=None, all_banners=False, 
                   category=None, all_categories=False):
    log("Iniciando processo de geração de vídeo vertical Reels/Shorts...", "STEP")
    
    # Garante que a pasta de vídeos de saída existe
    os.makedirs(VIDEOS_DIR, exist_ok=True)
    
    # Obter os banners agrupados ou planos
    if all_categories:
        categorized_banners = get_banners_by_category(shuffle_banners=shuffle_banners)
    elif category:
        categorized_banners = get_banners_by_category(category_filter=category, shuffle_banners=shuffle_banners)
    else:
        # Modo global (padrão)
        banners = get_all_banners_list(shuffle_banners=shuffle_banners)
        categorized_banners = {"global": banners} if banners else {}

    if not categorized_banners:
        log("Nenhum banner elegível foi encontrado para compilação.", "ERROR")
        return None

    compiled_paths = []
    timestamp = time.strftime("%Y%m%d_%H%M%S")

    for cat_name, cat_banners in categorized_banners.items():
        if len(cat_banners) < 2:
            log(f"Categoria '{cat_name}' possui apenas {len(cat_banners)} banner(s). Pulando (são necessários no mínimo 2 para transição).", "WARN")
            continue

        log(f"\n==================================================", "INFO")
        log(f"Processando categoria: {cat_name.upper()} ({len(cat_banners)} banners)", "STEP")
        log(f"==================================================", "INFO")

        if all_banners or all_categories or category:
            # Compilar em lotes de 'count'
            chunks = [cat_banners[i:i + count] for i in range(0, len(cat_banners), count)]
            
            for idx, chunk in enumerate(chunks):
                # Garante transição no último lote de 1 elemento adicionando o banner final do anterior
                if len(chunk) < 2 and idx > 0:
                    chunk = [chunks[idx-1][-1]] + chunk
                    
                if len(chunk) < 2:
                    continue

                log(f"--- Compilando lote {idx+1}/{len(chunks)} da categoria '{cat_name}' ({len(chunk)} banners) ---", "STEP")
                
                if output_filename:
                    base_name, ext = os.path.splitext(output_filename)
                    if cat_name != "global":
                        part_filename = f"{base_name}_{cat_name}_part{idx+1}{ext}"
                    else:
                        part_filename = f"{base_name}_part{idx+1}{ext}"
                else:
                    if cat_name != "global":
                        part_filename = f"reels_{cat_name}_{transition_style}_part{idx+1}_{timestamp}.mp4"
                    else:
                        part_filename = f"reels_{transition_style}_part{idx+1}_{timestamp}.mp4"
                    
                output_path = os.path.join(VIDEOS_DIR, part_filename)
                success = compile_video_ffmpeg(chunk, output_path, duration, trans_duration, transition_style)
                if success:
                    compiled_paths.append(output_path)
        else:
            # Modo padrão: apenas um vídeo com os primeiros 'count' banners
            selected_banners = cat_banners[:count]
            log(f"Selecionados os {len(selected_banners)} primeiros banners da categoria '{cat_name}'.", "INFO")
            
            if output_filename:
                base_name, ext = os.path.splitext(output_filename)
                if cat_name != "global":
                    out_name = f"{base_name}_{cat_name}{ext}"
                else:
                    out_name = f"{base_name}{ext}"
            else:
                if cat_name != "global":
                    out_name = f"reels_{cat_name}_{transition_style}_{timestamp}.mp4"
                else:
                    out_name = f"reels_{transition_style}_{timestamp}.mp4"
                    
            output_path = os.path.join(VIDEOS_DIR, out_name)
            success = compile_video_ffmpeg(selected_banners, output_path, duration, trans_duration, transition_style)
            if success:
                compiled_paths.append(output_path)
                
    if compiled_paths:
        log(f"\n[OK] Processamento concluído. {len(compiled_paths)} vídeos gerados com sucesso na pasta: {VIDEOS_DIR}", "OK")
    else:
        log("\n[WARN] Nenhum vídeo pôde ser compilado (verifique se as categorias possuem banners suficientes).", "WARN")
        
    return compiled_paths

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compilador de Vídeos Reels/Shorts a partir de Banners Promocionais")
    parser.add_argument("--limit", "-l", type=int, default=15, help="Quantidade de banners por vídeo (lote) (padrão: 15)")
    parser.add_argument("--duration", "-d", type=float, default=3.0, help="Duração de exibição de cada banner em segundos (padrão: 3.0)")
    parser.add_argument("--trans-duration", "-t", type=float, default=0.5, help="Duração do efeito de transição em segundos (padrão: 0.5)")
    parser.add_argument("--transition", "-s", type=str, default="fade", 
                         choices=["fade", "slideleft", "slideright", "slideup", "slidedown", 
                                  "wipeleft", "wiperight", "wipeup", "wipedown", "circlecrop", 
                                  "rectcrop", "dissolve"], 
                         help="Estilo de transição entre os banners (padrão: fade)")
    parser.add_argument("--random", "-r", action="store_true", help="Embaralhar ordem dos banners")
    parser.add_argument("--output", "-o", type=str, default=None, help="Nome personalizado para o arquivo de saída MP4 (ou prefixo em lote)")
    parser.add_argument("--all", "-a", action="store_true", help="Gera múltiplos vídeos abrangendo todo o catálogo de imagens")
    parser.add_argument("--category", "-c", type=str, default=None, help="Filtrar e compilar vídeos apenas para esta categoria específica (ex: tech, pets, home)")
    parser.add_argument("--all-categories", action="store_true", help="Agrupa e gera vídeos separados automaticamente para todas as categorias disponíveis")
    
    args = parser.parse_args()
    
    if args.trans_duration >= args.duration:
        log("Erro: A duração da transição (--trans-duration) deve ser estritamente menor que a duração de exibição (--duration).", "ERROR")
        exit(1)
        
    generate_video(
        duration=args.duration,
        trans_duration=args.trans_duration,
        transition_style=args.transition,
        count=args.limit,
        shuffle_banners=args.random,
        output_filename=args.output,
        all_banners=args.all,
        category=args.category,
        all_categories=args.all_categories
    )
