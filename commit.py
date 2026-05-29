import os
import shutil
import subprocess
from utils import log

# Configurações de caminhos
SOURCE_JSON = r"C:\Users\ferna\development\amazon-products\output\produtos_consolidado.json"
TARGET_REPO = r"C:\Users\ferna\development\achadinhos-bot\achadinhosporai-v2-data"
TARGET_JSON = os.path.join(TARGET_REPO, "data", "products", "products.json")

def main():
    log("Iniciando processo de publicação de produtos no GitHub...", "STEP")
    
    if not os.path.exists(SOURCE_JSON):
        log(f"Arquivo de origem não encontrado em {SOURCE_JSON}. Abortando.", "ERROR")
        return

    log(f"Copiando {SOURCE_JSON} para {TARGET_JSON}...", "INFO")
    try:
        os.makedirs(os.path.dirname(TARGET_JSON), exist_ok=True)
        shutil.copyfile(SOURCE_JSON, TARGET_JSON)
        log("Arquivo de produtos copiado com sucesso.", "OK")
    except Exception as e:
        log(f"Erro ao copiar arquivo: {e}", "ERROR")
        return

    # Git commands
    log("Iniciando operações do Git...", "STEP")
    try:
        # Verifica se há alterações para commitar
        # Usamos cwd=TARGET_REPO para garantir que o git execute na pasta correta
        status = subprocess.run(["git", "status", "--porcelain", "data/products/products.json"], cwd=TARGET_REPO, capture_output=True, text=True)
        if not status.stdout.strip():
            log("Nenhuma alteração detectada no products.json. Nada a publicar.", "WARN")
            return

        # git add
        subprocess.run(["git", "add", "data/products/products.json"], cwd=TARGET_REPO, check=True)
        
        # git commit
        commit_msg = "update: atualizar catalogo unificado de produtos"
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=TARGET_REPO, check=True)
        log(f"Commit realizado: '{commit_msg}'", "OK")

        # git push
        subprocess.run(["git", "push"], cwd=TARGET_REPO, check=True)
        log("Alterações enviadas (pushed) para o GitHub com sucesso!", "OK")
        
    except subprocess.CalledProcessError as e:
        log(f"Erro ao executar comando Git: {e}", "ERROR")
    except Exception as e:
        log(f"Erro inesperado no processo Git: {e}", "ERROR")

if __name__ == "__main__":
    main()
