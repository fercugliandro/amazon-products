import os
import shutil

OUTPUT_DIR = r"C:\Users\ferna\development\amazon-products\output"

# Arquivos de sessão a serem preservados para evitar re-autenticação manual
PRESERVE = {"meta_session.json", "instagram_session.json"}

def clean():
    print("Iniciando a limpeza completa dos caches...")
    if not os.path.exists(OUTPUT_DIR):
        print(f"Diretório {OUTPUT_DIR} não encontrado.")
        return

    # Limpar arquivos na raiz da pasta output/
    for entry in os.scandir(OUTPUT_DIR):
        if entry.is_file():
            if entry.name not in PRESERVE:
                try:
                    os.remove(entry.path)
                    print(f"OK: Removido arquivo de cache: {entry.name}")
                except Exception as e:
                    print(f"ERRO: Erro ao remover arquivo {entry.name}: {e}")
        elif entry.is_dir():
            # Limpar o conteúdo dos subdiretórios (banners, ai_images, videos, etc.)
            print(f"Limpando subdiretorio: {entry.name}/")
            for sub_entry in os.scandir(entry.path):
                try:
                    if sub_entry.is_file():
                        os.remove(sub_entry.path)
                    elif sub_entry.is_dir():
                        shutil.rmtree(sub_entry.path)
                except Exception as e:
                    print(f"ERRO: Erro ao limpar {sub_entry.path}: {e}")

    print("Limpeza de caches concluída com sucesso!")

if __name__ == "__main__":
    clean()
