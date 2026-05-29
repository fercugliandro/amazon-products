import os
import sys
from dotenv import load_dotenv
from google import genai

load_dotenv()

def main():
    print("Verificando chaves e listando modelos do Gemini...")
    
    # Carregar API Key da mesma forma que generate_ai_images.py
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        sibling_env_path = r"C:\Users\ferna\development\gemini-agents\.env"
        if os.path.exists(sibling_env_path):
            with open(sibling_env_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip().startswith("GEMINI_API_KEY="):
                        api_key = line.strip().split("=")[1].strip()
                        break
                        
    if not api_key:
        print("Erro: GEMINI_API_KEY não encontrada.")
        return

    print(f"Chave de API carregada com sucesso (prefixo: {api_key[:8]}...).")

    try:
        client = genai.Client(api_key=api_key)
        
        print("Consultando modelos disponíveis na API...")
        models = client.models.list()
        
        print("\n--- Modelos Disponíveis ---")
        for m in models:
            print(f"Model: {m.name} | Supported Actions: {m.supported_actions}")
            
    except Exception as e:
        print(f"Erro ao consultar a API: {e}")

if __name__ == "__main__":
    main()
