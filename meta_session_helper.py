import asyncio
import os
from playwright.async_api import async_playwright
from utils import log

# Caminho para salvar a sessão
SESSION_PATH = r"C:\Users\ferna\development\amazon-products\output\meta_session.json"

async def initialize_session():
    log("Iniciando o assistente de autenticação da Meta...", "STEP")
    log("Este script abrirá uma janela visível do navegador para você realizar o login.", "INFO")
    
    os.makedirs(os.path.dirname(SESSION_PATH), exist_ok=True)

    async with async_playwright() as p:
        # Abrir navegador visível para o login manual
        browser = await p.chromium.launch(headless=False)
        # Configurar viewport padrão confortável
        context = await browser.new_context(viewport={"width": 1280, "height": 800})
        page = await context.new_page()

        log("Navegando para o Meta Business Suite...", "INFO")
        await page.goto("https://business.facebook.com/latest/home")

        log("\n" + "="*70, "WARN")
        log("INSTRUÇÕES IMPORTANTES:", "WARN")
        log("1. Faça login na sua conta do Facebook/Meta na janela do navegador que se abriu.", "WARN")
        log("2. Resolva qualquer verificação de segurança ou 2FA (Autenticação de Dois Fatores).", "WARN")
        log("3. Certifique-se de estar na página inicial do Meta Business Suite.", "WARN")
        log("4. Volte aqui para este terminal e aperte [ENTER] para salvar sua sessão.", "WARN")
        log("="*70 + "\n", "WARN")

        # Aguarda a entrada do usuário no console nativo
        # Como o script roda em ambiente assíncrono, usamos um executor em thread para o input
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, input, "Pressione [ENTER] AQUI no terminal após concluir o login com sucesso...")

        # Salvar estado da sessão (cookies, localStorage, etc.)
        await context.storage_state(path=SESSION_PATH)
        log(f"✓ Sessão autenticada salva com sucesso em: {SESSION_PATH}", "OK")
        
        await browser.close()
        log("Navegador fechado. O agente está pronto para rodar em background!", "OK")

if __name__ == "__main__":
    asyncio.run(initialize_session())
