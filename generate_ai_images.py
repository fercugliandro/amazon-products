import os
import json
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types
from utils import log

# Carregar variáveis de ambiente (como GEMINI_API_KEY)
load_dotenv()

# Configurações de caminhos
PROMPTS_JSON = r"C:\Users\ferna\development\amazon-products\output\ai_prompts.json"
AI_IMAGES_DIR = r"C:\Users\ferna\development\amazon-products\output\ai_images"

def main():
    log("Iniciando processo de geração física de imagens por IA...", "STEP")
    
    # 1. Carregar API Key
    # Tenta carregar do .env local ou do arquivo .env da pasta vizinha se necessário
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        # Fallback para o arquivo .env do gemini-agents se existir
        sibling_env_path = r"C:\Users\ferna\development\gemini-agents\.env"
        if os.path.exists(sibling_env_path):
            with open(sibling_env_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip().startswith("GEMINI_API_KEY="):
                        api_key = line.strip().split("=")[1].strip()
                        break
                        
    if not api_key:
        log("Erro: GEMINI_API_KEY não encontrada no ambiente nem no arquivo .env. Por favor, configure sua chave.", "ERROR")
        return

    # 2. Carregar prompts salvos
    if not os.path.exists(PROMPTS_JSON):
        log(f"Arquivo de prompts não encontrado em {PROMPTS_JSON}. Por favor, execute generate_prompts.py primeiro.", "ERROR")
        return
        
    with open(PROMPTS_JSON, "r", encoding="utf-8") as f:
        prompts_data = json.load(f)
        
    log(f"Carregados {len(prompts_data)} prompts do arquivo {PROMPTS_JSON}.", "INFO")
    
    # Garantir que a pasta de destino existe
    os.makedirs(AI_IMAGES_DIR, exist_ok=True)
    
    # 3. Inicializar o cliente Google GenAI
    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        log(f"Erro ao inicializar o cliente Google GenAI: {e}", "ERROR")
        return
        
    success_count = 0
    skipped_count = 0
    error_count = 0
    
    # Modelo padrão a ser utilizado (Imagen 4.0 oficial ativo na API)
    model_name = 'imagen-4.0-generate-001'
    
    for idx, item in enumerate(prompts_data):
        slug = item.get("slug")
        prompt = item.get("prompt")
        name = item.get("name", "Produto")
        
        if not slug or not prompt:
            continue
            
        output_path = os.path.join(AI_IMAGES_DIR, f"achadinho_{slug}.png")
        
        # Cache Inteligente: se a imagem já existir, pula para economizar API
        if os.path.exists(output_path):
            skipped_count += 1
            continue
            
        log(f"\n[{idx+1}/{len(prompts_data)}] Gerando imagem IA para: {name[:40]}...", "STEP")
        log(f"Prompt: {prompt[:120]}...", "INFO")
        
        try:
            # Chamar a API de geração de imagens do Imagen
            response = client.models.generate_images(
                model=model_name,
                prompt=prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio="1:1"
                )
            )
            
            if response.generated_images:
                # Salvar a primeira imagem gerada
                generated_image = response.generated_images[0]
                generated_image.image.save(output_path)
                log(f"✓ Imagem IA gerada com sucesso e salva em: {output_path}", "OK")
                success_count += 1
            else:
                log(f"⚠️ A API respondeu com sucesso, mas nenhuma imagem foi retornada para: {slug}", "WARN")
                error_count += 1
                
            # Atraso de cortesia para respeitar os limites de taxa de requisição da API
            time.sleep(3.0)
            
        except Exception as e:
            error_str = str(e)
            if "INVALID_ARGUMENT" in error_str and "paid plans" in error_str:
                log("❌ ERRO CRÍTICO: A chave de API do Gemini informada está no plano gratuito (Free Plan).", "ERROR")
                log("A geração de imagens com o Imagen 3 está disponível apenas para contas com faturamento ativo (paid plans).", "ERROR")
                log("Por favor, ative o faturamento (billing) no seu projeto do Google AI Studio ou insira uma chave paga.", "ERROR")
                return
            else:
                log(f"Erro ao gerar imagem para {slug}: {e}", "ERROR")
                error_count += 1
                
    log("\n--- Relatório Final de Geração de Imagens por IA ---", "STEP")
    log(f"Imagens geradas com sucesso: {success_count}", "OK")
    log(f"Imagens puladas (já existiam no cache): {skipped_count}", "INFO")
    log(f"Erros encontrados: {error_count}", "WARN" if error_count > 0 else "OK")
    
if __name__ == "__main__":
    main()
