import os
import sys
import json
import argparse
import glob
import time
from dotenv import load_dotenv
from instagrapi import Client
from instagrapi.types import StoryLink
from utils import log

# Carregar variáveis de ambiente (como INSTAGRAM_USERNAME e INSTAGRAM_PASSWORD)
load_dotenv()

SESSION_PATH = r"C:\Users\ferna\development\amazon-products\output\instagram_session.json"
CONSOLIDATED_JSON = r"C:\Users\ferna\development\amazon-products\output\produtos_consolidado.json"
BANNERS_DIR = r"C:\Users\ferna\development\amazon-products\output\banners"
VIDEOS_DIR = r"C:\Users\ferna\development\amazon-products\output\videos"

def login_instagram():
    cl = Client()
    
    # 1. Carregar sessão persistente anterior se existir
    if os.path.exists(SESSION_PATH):
        try:
            log("Carregando sessão persistente do Instagram...", "INFO")
            cl.load_settings(SESSION_PATH)
            
            # Tentar fazer login simples (valida a sessão)
            username = os.getenv("INSTAGRAM_USERNAME")
            password = os.getenv("INSTAGRAM_PASSWORD")
            cl.login(username, password)
            log("✓ Sessão carregada e validada com sucesso!", "OK")
            return cl
        except Exception as e:
            log(f"Aviso: Não foi possível reutilizar a sessão anterior: {e}. Iniciando novo login...", "WARN")
            cl = Client() # Reseta o cliente
            
    # 2. Novo login interativo se a sessão não existia ou expirou
    username = os.getenv("INSTAGRAM_USERNAME")
    password = os.getenv("INSTAGRAM_PASSWORD")
    
    if not username or not password:
        log("Credenciais não encontradas no arquivo .env.", "WARN")
        username = input("Digite seu Usuário do Instagram: ").strip()
        password = input("Digite sua Senha do Instagram: ").strip()

    log(f"Iniciando login no Instagram para o usuário: {username}...", "STEP")
    
    try:
        # Tenta o login básico
        cl.login(username, password)
        log("✓ Login efetuado com sucesso!", "OK")
    except Exception as e:
        err_msg = str(e)
        if "two_factor_required" in err_msg or "two-factor" in err_msg or "TwoFactorRequired" in err_msg:
            log("\n" + "="*60, "WARN")
            log("AUTENTICAÇÃO DE DOIS FATORES (2FA) DETECTADA!", "WARN")
            log("Verifique seu aplicativo autenticador ou SMS.", "WARN")
            log("="*60 + "\n", "WARN")
            
            verification_code = input("Digite o código 2FA/MFA de 6 dígitos: ").strip()
            try:
                # Tenta o login com o código fornecido
                cl.login(username, password, verification_code=verification_code)
                log("✓ Login com MFA efetuado com sucesso!", "OK")
            except Exception as ex:
                log(f"Erro ao efetuar login com MFA: {ex}", "ERROR")
                raise ex
        else:
            log(f"Erro crítico ao efetuar login: {e}", "ERROR")
            raise e

    # Salva as configurações de sessão para futuros logins sem MFA
    os.makedirs(os.path.dirname(SESSION_PATH), exist_ok=True)
    cl.dump_settings(SESSION_PATH)
    log(f"✓ Configurações de sessão salvas com sucesso em: {SESSION_PATH}", "OK")
    return cl

def publish_reels(cl, limit):
    log("Buscando vídeos Reels compilados localmente...", "INFO")
    video_files = glob.glob(os.path.join(VIDEOS_DIR, "reels_*.mp4"))
    if not video_files:
        log("Nenhum vídeo Reel encontrado na pasta de vídeos. Gere vídeos primeiro.", "ERROR")
        return

    # Ordenar pelos mais recentes primeiro
    video_files.sort(key=os.path.getmtime, reverse=True)
    selected_videos = video_files[:limit]
    log(f"Selecionados {len(selected_videos)} vídeos Reels para publicação.", "INFO")

    caption = (
        "🔥 ACHADINHOS POR AÍ! 🔥\n"
        "Separamos as melhores ofertas do dia com descontos imperdíveis!\n\n"
        "👉 Todos os links oficiais e cupons estão disponíveis na nossa BIO! Aproveite! 🛒\n\n"
        "#achadinhos #ofertas #desconto #amazon #mercadolivre #compras #reels #shorts"
    )

    for idx, video_path in enumerate(selected_videos):
        log(f"\n--- Publicando Reel {idx+1}/{len(selected_videos)}: {os.path.basename(video_path)} ---", "STEP")
        try:
            log("Fazendo upload do arquivo de vídeo... (Isso pode levar alguns segundos)", "INFO")
            # Localizar um banner existente na pasta de banners para usar como thumbnail (capa do Reel)
            banners = glob.glob(os.path.join(BANNERS_DIR, "achadinho_*.png"))
            thumbnail_path = None
            if banners:
                # Usa o primeiro banner como capa do vídeo
                thumbnail_path = banners[0]
                log(f"Usando banner {os.path.basename(thumbnail_path)} como capa (thumbnail) do Reel...", "INFO")

            media = cl.clip_upload(
                path=video_path,
                caption=caption,
                thumbnail=thumbnail_path
            )
            log(f"✓ Reel {idx+1} publicado com sucesso! ID da Mídia: {media.id}", "OK")
            # Cortesia para evitar limites de taxa
            time.sleep(5)
        except Exception as e:
            log(f"Falha ao publicar Reel {idx+1}: {e}", "ERROR")

def publish_stories(cl, limit):
    log("Carregando catálogo para obter produtos em destaque...", "INFO")
    if not os.path.exists(CONSOLIDATED_JSON):
        log(f"Arquivo consolidado {CONSOLIDATED_JSON} não encontrado.", "ERROR")
        return

    with open(CONSOLIDATED_JSON, "r", encoding="utf-8") as f:
        products = json.load(f)

    # Filtra em destaque
    featured = [p for p in products if p.get("featured")]
    if not featured:
        log("Nenhum produto em destaque encontrado. Usando os primeiros da lista.", "WARN")
        featured = products

    selected_products = featured[:limit]
    log(f"Selecionados {len(selected_products)} produtos em destaque para postar Stories com Link Sticker.", "INFO")

    for idx, prod in enumerate(selected_products):
        slug = prod.get("slug")
        banner_path = os.path.join(BANNERS_DIR, f"achadinho_{slug}.png")
        affiliate_url = prod.get("productUrl", "")

        log(f"\n--- Publicando Story {idx+1}/{len(selected_products)}: {prod.get('name')[:35]}... ---", "STEP")

        if not os.path.exists(banner_path):
            log(f"Aviso: Banner não encontrado em {banner_path}. Pulando produto.", "WARN")
            continue

        if not affiliate_url:
            log("Aviso: Link de afiliado ausente. Pulando produto.", "WARN")
            continue

        try:
            # Define o Link Sticker oficial da API móvel do Instagram
            # Este sticker fica flutuando na tela, clicável!
            link_sticker = StoryLink(webUri=affiliate_url, link_text="VER PRODUTO 🛒")
            
            log(f"Fazendo upload da imagem do banner com o Link Sticker: {affiliate_url}...", "INFO")
            cl.photo_upload_to_story(
                path=banner_path,
                links=[link_sticker]
            )
            log(f"✓ Story {idx+1} publicado com sucesso com o Link Sticker!", "OK")
            # Atraso de segurança entre uploads
            time.sleep(5)
        except Exception as e:
            log(f"Falha ao publicar Story {idx+1}: {e}", "ERROR")

def main():
    parser = argparse.ArgumentParser(description="Instagram Direct API Publisher via instagrapi")
    parser.add_argument(
        "--type",
        choices=["reels", "stories"],
        required=True,
        help="Tipo de publicação: 'reels' ou 'stories'"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=15,
        help="Limite máximo de itens a publicar (padrão: 15)"
    )
    args = parser.parse_args()

    # Inicializar cliente e autenticar
    try:
        cl = login_instagram()
    except Exception as e:
        log(f"Falha na autenticação geral do Instagram: {e}", "ERROR")
        sys.exit(1)

    # Executar publicação
    if args.type == "reels":
        publish_reels(cl, args.limit)
    elif args.type == "stories":
        publish_stories(cl, args.limit)

if __name__ == "__main__":
    main()
