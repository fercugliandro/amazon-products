import os
from google import genai
from google.genai import types

def main():
    api_key = "AIzaSyDwLDtLTZvj4d0lqM-abj97D3JfDHuHlJ4"
    print("Iniciando teste do Imagen 4.0...")
    
    try:
        client = genai.Client(api_key=api_key)
        print("Enviando solicitação de geração de imagem para imagen-4.0-generate-001...")
        
        response = client.models.generate_images(
            model='imagen-4.0-generate-001',
            prompt='A professional commercial product photograph of a modern mechanical keyboard, studio lighting, highly detailed',
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio="1:1"
            )
        )
        
        print(f"Resposta recebida! Quantidade de imagens geradas: {len(response.generated_images)}")
        
        os.makedirs('scratch', exist_ok=True)
        for i, generated_image in enumerate(response.generated_images):
            output_path = f'scratch/test_result_imagen4_{i}.jpg'
            generated_image.image.save(output_path)
            print(f"Imagem salva com sucesso em: {output_path}")
            
    except Exception as e:
        print(f"Erro ao gerar imagem: {e}")

if __name__ == "__main__":
    main()
