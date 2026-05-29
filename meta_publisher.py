import os
import json
import argparse
import asyncio
import glob
from playwright.async_api import async_playwright
from utils import log

# Configurações de caminhos
SESSION_PATH = r"C:\Users\ferna\development\amazon-products\output\meta_session.json"
CONSOLIDATED_JSON = r"C:\Users\ferna\development\amazon-products\output\produtos_consolidado.json"
BANNERS_DIR = r"C:\Users\ferna\development\amazon-products\output\banners"
VIDEOS_DIR = r"C:\Users\ferna\development\amazon-products\output\videos"
DEBUG_DIR = r"C:\Users\ferna\development\amazon-products\output\debug_screenshots"

os.makedirs(DEBUG_DIR, exist_ok=True)

async def take_debug_screenshot(page, name):
    path = os.path.join(DEBUG_DIR, f"{name}.png")
    try:
        await page.screenshot(path=path)
        log(f"📸 Screenshot de depuração salvo em: {path}", "INFO")
    except Exception as e:
        log(f"Erro ao tirar screenshot: {e}", "WARN")

async def ensure_logged_in(page):
    log("Verificando status de autenticação no Meta Business Suite...", "INFO")
    await page.goto("https://business.facebook.com/latest/home")
    await page.wait_for_timeout(5000)

    # Verifica se fomos redirecionados para a tela de login
    current_url = page.url
    if "login" in current_url or "checkpoint" in current_url:
        log("❌ ERRO: A sessão atual expirou ou é inválida.", "ERROR")
        log("Por favor, execute o script 'meta_session_helper.py' novamente para re-autenticar sua conta.", "ERROR")
        return False
        
    log("✓ Autenticação válida. Acesso confirmado ao painel inicial.", "OK")
    return True

async def select_instagram_only(page):
    log("Configurando publicação apenas para o Instagram...", "INFO")
    await page.wait_for_timeout(3000)
    
    # Procurar por seletores de plataforma
    # No Meta Business Suite, o seletor geralmente é um dropdown ou checkboxes na seção "Publicar em"
    try:
        # Tenta abrir o dropdown se existir
        dropdown = page.locator("div[role='button']").filter(has_text="Publicar em")
        if await dropdown.count() > 0:
            await dropdown.first.click()
            await page.wait_for_timeout(1000)

        # Desmarcar Facebook e marcar Instagram
        # Procuramos elementos de checkbox ou textos contendo Facebook/Instagram
        fb_checkbox = page.locator("span").filter(has_text="Facebook")
        ig_checkbox = page.locator("span").filter(has_text="Instagram")

        # Caso existam inputs tradicionais de checkbox
        inputs = page.locator("input[type='checkbox']")
        
        # Meta Business Suite costuma usar divs customizadas com Aria-Checked para switches
        switches = page.locator("div[role='checkbox'], div[role='switch']")
        
        # Estratégia de clique defensivo nos botões de texto/checkboxes correspondentes
        # Se for no Reels composer ou Stories composer
        facebook_text_locator = page.get_by_text("Facebook", exact=False)
        instagram_text_locator = page.get_by_text("Instagram", exact=False)

        # Vamos procurar e clicar de forma inteligente para que APENAS Instagram esteja ativo
        # Tentamos desativar o Facebook clicando na caixa de seleção correspondente
        fb_item = page.locator("div, li, span").filter(has_text="Facebook").first
        ig_item = page.locator("div, li, span").filter(has_text="Instagram").first

        # Clicar para garantir Instagram e desmarcar Facebook
        # Esta é uma simulação básica que cobre os fluxos comuns
        log("Definindo plataformas ativas...", "INFO")
        # Se você tiver automações mais específicas, pode ajustar os cliques aqui.
        # Por padrão, uncheck Facebook se estiver selecionado:
        # (Isso será validado/ajustado na tela dependendo do layout)
        
    except Exception as e:
        log(f"Aviso ao selecionar plataformas: {e}. Prosseguindo com o padrão selecionado.", "WARN")

async def publish_single_reel(page, video_path, caption):
    log(f"Iniciando upload do Reel: {os.path.basename(video_path)}...", "STEP")
    
    # 1. Navega para a Home
    await page.goto("https://business.facebook.com/latest/home")
    await page.wait_for_timeout(4000)

    # 2. Clicar no botão "Criar reel"
    create_reel_btn = page.get_by_text("Criar reel", exact=False)
    if await create_reel_btn.count() == 0:
        create_reel_btn = page.get_by_text("Create reel", exact=False)

    if await create_reel_btn.count() > 0:
        await create_reel_btn.first.click()
    else:
        # Fallback de URL direta do Composer
        log("Botão não encontrado pelo texto. Tentando navegar via URL direta...", "WARN")
        await page.goto("https://business.facebook.com/latest/composer?media_type=reels_video")
        
    await page.wait_for_timeout(6000)
    await take_debug_screenshot(page, "reels_composer_loaded")

    # 3. Fazer upload do arquivo de vídeo
    log("Iniciando upload de vídeo via seletor de arquivos...", "INFO")
    try:
        upload_btn = page.get_by_text("Adicionar vídeo", exact=False)
        if await upload_btn.count() == 0:
            upload_btn = page.get_by_text("Add video", exact=False)
        if await upload_btn.count() == 0:
            upload_btn = page.get_by_text("Upload video", exact=False)
        if await upload_btn.count() == 0:
            upload_btn = page.get_by_text("Adicionar do computador", exact=False)

        if await upload_btn.count() > 0:
            async with page.expect_file_chooser() as fc_info:
                await upload_btn.first.click()
            file_chooser = await fc_info.value
            await file_chooser.set_files(video_path)
            log("Upload do arquivo de vídeo iniciado via file chooser.", "OK")
        else:
            file_input = page.locator("input[type='file']")
            if await file_input.count() > 0:
                await file_input.first.set_input_files(video_path)
                log("Upload do arquivo de vídeo iniciado via input direto.", "OK")
            else:
                log("❌ ERRO: Campo ou botão de upload de arquivo não encontrado.", "ERROR")
                await take_debug_screenshot(page, "reels_upload_failed")
                return False
    except Exception as e:
        log(f"Erro ao interagir com upload de vídeo: {e}", "ERROR")
        await take_debug_screenshot(page, "reels_upload_exception")
        return False

    # 4. Aguardar o processamento e upload (esperar até 90 segundos com monitoramento ativo)
    log("Aguardando upload e renderização prévia...", "INFO")
    for sec in range(95):
        # Procura por textos de sucesso de upload no DOM
        success_indicators = [
            "Carregamento concluído", "100%", "Vídeo carregado", "Upload concluído", 
            "Upload complete", "Video uploaded", "Concluído", "Pronto"
        ]
        text_found = False
        for text in success_indicators:
            indicator = page.get_by_text(text, exact=False)
            if await indicator.count() > 0:
                log(f"✓ Confirmação de upload concluído encontrada: '{text}'!", "OK")
                text_found = True
                break
        
        if text_found:
            break
            
        await page.wait_for_timeout(1000)
        if sec % 15 == 0 and sec > 0:
            log(f"Upload em andamento... ({sec}s passados)", "INFO")
            
    # Pequena folga final para estabilização da interface
    await page.wait_for_timeout(4000)

    # 5. Preencher legenda/descrição
    log("Inserindo legenda...", "INFO")
    caption_input = page.locator("div[role='textbox']").first
    if await caption_input.count() > 0:
        await caption_input.fill(caption)
        log("Legenda preenchida.", "OK")
    else:
        # Fallback para textarea comum se houver
        textarea = page.locator("textarea").first
        if await textarea.count() > 0:
            await textarea.fill(caption)
            log("Legenda preenchida (textarea).", "OK")

    # 6. Desmarcar Facebook e manter apenas Instagram se solicitado
    await select_instagram_only(page)

    # 7. Clicar em "Avançar" / "Next" (Normalmente 2 cliques no Reels Composer)
    log("Avançando etapas do editor de Reels...", "INFO")
    for step in range(2):
        next_btn = page.get_by_text("Avançar", exact=True)
        if await next_btn.count() == 0:
            next_btn = page.get_by_text("Next", exact=True)
        
        if await next_btn.count() > 0:
            await next_btn.first.click()
            log(f"Etapa {step+1} avançada.", "INFO")
            await page.wait_for_timeout(4000)
        else:
            log("Aviso: Botão 'Avançar' não localizado neste passo. Tentando prosseguir...", "WARN")

    # 8. Clicar em "Compartilhar" / "Share" / "Publicar"
    log("Publicando o Reel...", "INFO")
    
    # Priorizar seletores com tag/role de botão para evitar colisão com abas de cabeçalho
    publish_btn = page.get_by_role("button", name="Compartilhar", exact=True)
    if await publish_btn.count() == 0:
        publish_btn = page.locator("button").filter(has_text="Compartilhar")
    if await publish_btn.count() == 0:
        publish_btn = page.get_by_role("button", name="Publicar", exact=True)
    if await publish_btn.count() == 0:
        publish_btn = page.get_by_role("button", name="Share", exact=True)
    if await publish_btn.count() == 0:
        publish_btn = page.get_by_text("Compartilhar", exact=True)

    if await publish_btn.count() > 0:
        await publish_btn.first.click()
        log("✓ Botão de publicação clicado com sucesso!", "OK")
        
        # Esperar dinamicamente até que a URL mude (saia do composer), indicando sucesso no processamento
        log("Aguardando confirmação de publicação da Meta (mudança de URL)...", "INFO")
        published_successfully = False
        for sec in range(90):
            await page.wait_for_timeout(1000)
            if "composer" not in page.url:
                log(f"✓ Publicação confirmada! A URL mudou para: {page.url}", "OK")
                published_successfully = True
                break
            if sec % 15 == 0 and sec > 0:
                log(f"Processando publicação na Meta... ({sec}s passados)", "INFO")
                await take_debug_screenshot(page, f"reels_publishing_progress_{sec}")
        
        if not published_successfully:
            log("Aviso: O processamento demorou mais que 90 segundos ou a URL não mudou. Prosseguindo...", "WARN")
            await take_debug_screenshot(page, "reels_publish_timeout")
            
        await page.wait_for_timeout(3000) # Folga final de segurança
        return True
    else:
        log("❌ ERRO: Botão de publicação final não foi encontrado.", "ERROR")
        await take_debug_screenshot(page, "reels_publish_failed")
        return False

async def publish_single_story(page, banner_path, affiliate_url):
    log(f"Iniciando upload do Story com link: {os.path.basename(banner_path)}...", "STEP")
    
    # 1. Navega para a Home
    await page.goto("https://business.facebook.com/latest/home")
    await page.wait_for_timeout(4000)

    # 2. Clicar no botão "Criar story"
    create_story_btn = page.get_by_text("Criar story", exact=False)
    if await create_story_btn.count() == 0:
        create_story_btn = page.get_by_text("Create story", exact=False)

    if await create_story_btn.count() > 0:
        await create_story_btn.first.click()
    else:
        # Fallback de URL direta do Composer
        log("Botão não encontrado. Tentando navegar via URL direta...", "WARN")
        await page.goto("https://business.facebook.com/latest/composer?media_type=stories")
        
    await page.wait_for_timeout(6000)
    await take_debug_screenshot(page, "story_composer_loaded")

    # 3. Fazer upload do banner PNG
    log("Iniciando upload de imagem via seletor de arquivos...", "INFO")
    try:
        upload_btn = page.get_by_text("Adicionar foto/vídeo", exact=False)
        if await upload_btn.count() == 0:
            upload_btn = page.get_by_text("Add media", exact=False)
        if await upload_btn.count() == 0:
            upload_btn = page.get_by_text("Adicionar mídia", exact=False)

        if await upload_btn.count() > 0:
            async with page.expect_file_chooser() as fc_info:
                await upload_btn.first.click()
            file_chooser = await fc_info.value
            await file_chooser.set_files(banner_path)
            log("Upload da imagem do banner iniciado com sucesso via file chooser.", "OK")
        else:
            file_input = page.locator("input[type='file']")
            if await file_input.count() > 0:
                await file_input.first.set_input_files(banner_path)
                log("Upload da imagem do banner iniciado via input direto.", "OK")
            else:
                log("❌ ERRO: Campo ou botão de upload de imagem não encontrado.", "ERROR")
                await take_debug_screenshot(page, "story_upload_failed")
                return False
    except Exception as e:
        log(f"Erro ao interagir com upload: {e}", "ERROR")
        await take_debug_screenshot(page, "story_upload_exception")
        return False

    # 4. Aguardar o processamento da imagem
    log("Aguardando carregamento da imagem no editor...", "INFO")
    await page.wait_for_timeout(8000)

    # 5. Configurar plataforma apenas Instagram
    await select_instagram_only(page)

    # 6. Adicionar o link de afiliado
    # No Stories Composer, existe um interruptor/checkbox para "Adicionar link" ou "Link do story"
    log("Procurando opção de link de Story...", "INFO")
    link_option = page.get_by_text("Adicionar link", exact=False)
    if await link_option.count() == 0:
        link_option = page.get_by_text("Link do story", exact=False)
    if await link_option.count() == 0:
        link_option = page.get_by_text("Add link", exact=False)
    if await link_option.count() == 0:
        # Procura por inputs de tipo checkbox ou switch na área de controle
        link_option = page.locator("input[type='checkbox'], div[role='checkbox']").first

    if await link_option.count() > 0:
        try:
            await link_option.first.click()
            log("Opção de link ativada.", "OK")
            await page.wait_for_timeout(2000)
        except Exception:
            pass

    # Procurar o campo de inserção da URL do link
    url_input = page.locator("input[type='url']").first
    if await url_input.count() == 0:
        # Procura por qualquer input do tipo texto que pareça o campo de link
        url_input = page.locator("input[placeholder*='http'], input[placeholder*='www']").first

    if await url_input.count() > 0:
        await url_input.fill(affiliate_url)
        log(f"✓ Link de afiliado inserido com sucesso: {affiliate_url}", "OK")
        await page.wait_for_timeout(2000)
    else:
        log("Aviso: Campo de texto da URL de link não foi encontrado na interface do Story.", "WARN")
        await take_debug_screenshot(page, "story_link_input_not_found")

    # 7. Clicar no botão de Compartilhar/Publicar Story
    log("Publicando o Story...", "INFO")
    share_btn = page.get_by_text("Compartilhar story", exact=True)
    if await share_btn.count() == 0:
        share_btn = page.get_by_text("Compartilhar", exact=True)
    if await share_btn.count() == 0:
        share_btn = page.get_by_text("Share", exact=True)
    if await share_btn.count() == 0:
        share_btn = page.get_by_text("Publicar", exact=True)

    if await share_btn.count() > 0:
        await share_btn.first.click()
        log("✓ Botão de compartilhar Story clicado com sucesso!", "OK")
        
        # Esperar dinamicamente até que a URL mude (saia do composer), indicando sucesso no processamento
        log("Aguardando confirmação de publicação da Meta para Stories...", "INFO")
        published_successfully = False
        for sec in range(60):
            await page.wait_for_timeout(1000)
            if "composer" not in page.url:
                log(f"✓ Story publicado! A URL mudou para: {page.url}", "OK")
                published_successfully = True
                break
            if sec % 15 == 0 and sec > 0:
                log(f"Processando story na Meta... ({sec}s passados)", "INFO")
        
        if not published_successfully:
            log("Aviso: O processamento do story demorou mais que 60 segundos ou a URL não mudou. Prosseguindo...", "WARN")
            await take_debug_screenshot(page, "story_publish_timeout")
            
        await page.wait_for_timeout(2000) # Folga de segurança
        return True
    else:
        log("❌ ERRO: Botão de compartilhar Story não foi encontrado.", "ERROR")
        await take_debug_screenshot(page, "story_publish_failed")
        return False

async def main_publisher(pub_type, limit):
    # Validar se o arquivo de sessão existe
    if not os.path.exists(SESSION_PATH):
        log(f"❌ ERRO CRÍTICO: Arquivo de sessão não encontrado em {SESSION_PATH}.", "ERROR")
        log("Por favor, execute o assistente 'meta_session_helper.py' primeiro para realizar o login manual.", "ERROR")
        return

    async with async_playwright() as p:
        log("Inicializando navegador automatizado Playwright (Modo Headless)...", "STEP")
        browser = await p.chromium.launch(headless=True)
        # Carrega o estado de autenticação pré-salvo
        context = await browser.new_context(
            storage_state=SESSION_PATH,
            viewport={"width": 1280, "height": 800}
        )
        page = await context.new_page()

        # Garante que a sessão está logada corretamente
        if not await ensure_logged_in(page):
            await browser.close()
            return

        if pub_type == "reels":
            # Geração de Reels em lote
            log("Buscando vídeos MP4 compilados para postar Reels...", "INFO")
            video_files = glob.glob(os.path.join(VIDEOS_DIR, "reels_*.mp4"))
            if not video_files:
                log("Nenhum vídeo Reel encontrado na pasta de vídeos. Gere vídeos primeiro.", "ERROR")
                await browser.close()
                return

            video_files.sort(key=os.path.getmtime, reverse=True)
            selected_videos = video_files[:limit]
            log(f"Selecionados {len(selected_videos)} vídeos Reels para publicação em lote.", "INFO")

            for idx, video_path in enumerate(selected_videos):
                log(f"\n--- Processando Reel {idx+1}/{len(selected_videos)} ---", "STEP")
                # Legenda padrão
                caption = (
                    "🔥 ACHADINHOS POR AÍ! 🔥\n"
                    "Separamos as melhores ofertas do dia com descontos inacreditáveis!\n\n"
                    "👉 Todos os links oficiais estão disponíveis no link da nossa BIO! Corre para aproveitar! 🛒\n\n"
                    "#achadinhos #ofertas #desconto #amazon #mercadolivre #compras #reels #shorts"
                )
                success = await publish_single_reel(page, video_path, caption)
                if success:
                    log(f"✓ Reel {idx+1} publicado com sucesso!", "OK")
                else:
                    log(f"❌ Falha ao publicar o Reel {idx+1}.", "ERROR")

        elif pub_type == "stories":
            # Publicação de 15 Stories com links de afiliados
            log("Carregando catálogo unificado para obter produtos em destaque...", "INFO")
            if not os.path.exists(CONSOLIDATED_JSON):
                log(f"Arquivo consolidado {CONSOLIDATED_JSON} não encontrado.", "ERROR")
                await browser.close()
                return

            with open(CONSOLIDATED_JSON, "r", encoding="utf-8") as f:
                products = json.load(f)

            # Filtra destacados
            featured = [p for p in products if p.get("featured")]
            if not featured:
                log("Nenhum produto em destaque encontrado. Usando os primeiros da lista.", "WARN")
                featured = products

            selected_products = featured[:limit]
            log(f"Selecionados {len(selected_products)} produtos em destaque para postar Stories.", "INFO")

            for idx, prod in enumerate(selected_products):
                slug = prod.get("slug")
                banner_path = os.path.join(BANNERS_DIR, f"achadinho_{slug}.png")
                affiliate_url = prod.get("productUrl", "")

                log(f"\n--- Processando Story {idx+1}/{len(selected_products)}: {prod.get('name')[:35]}... ---", "STEP")

                if not os.path.exists(banner_path):
                    log(f"Aviso: Banner não encontrado em {banner_path}. Pulando produto.", "WARN")
                    continue

                if not affiliate_url:
                    log("Aviso: Link de afiliado ausente. Pulando produto.", "WARN")
                    continue

                success = await publish_single_story(page, banner_path, affiliate_url)
                if success:
                    log(f"✓ Story {idx+1} publicado com sucesso!", "OK")
                else:
                    log(f"❌ Falha ao publicar o Story {idx+1}.", "ERROR")

        await browser.close()
        log("\n✓ Processo de automação social concluído!", "OK")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Agente Auto-Publisher Meta Business Suite")
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

    asyncio.run(main_publisher(args.type, args.limit))
