# Amazon Top Products Scraper

Scraper automatizado para coletar os produtos mais vendidos da Amazon Brasil por categoria, gerando dados estruturados em JSON com links de afiliado via SiteStripe.

## O que faz

- Acessa as páginas de **mais vendidos** da Amazon.com.br em 6 categorias
- Extrai para cada produto: título, preço, preço original, imagem em alta resolução e descrição
- Gera **links curtos de afiliado** autenticados via SiteStripe (`amzn.to/...`)
- Salva um JSON por categoria + um JSON consolidado com todos os produtos

## Categorias

| Chave       | Label                        |
|-------------|------------------------------|
| `tech`      | Eletrônicos                  |
| `gaming`    | Games e Consoles             |
| `beauty`    | Beleza e Cuidados Pessoais   |
| `home`      | Casa e Cozinha               |
| `baby`      | Bebês                        |
| `fitness`   | Esportes e Aventura          |

## Pré-requisitos

- Python 3.11+
- Conta Amazon com programa de afiliados ativo (para o SiteStripe)

## Instalação

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

## Uso

```bash
python anuncios.py
```

Na primeira execução (sem `amazon_cookies.json`) o navegador abrirá a página de login da Amazon. Faça o login manualmente e pressione **ENTER** no terminal — os cookies serão salvos para as próximas execuções.

## Saída

Os arquivos são gravados na pasta `output/`:

```
output/
├── tech_top10.json
├── gaming_top10.json
├── beauty_top10.json
├── home_top10.json
├── baby_top10.json
├── fitness_top10.json
└── all_categories_<timestamp>.json
```

Cada produto tem o seguinte schema:

```json
{
  "id": "1",
  "name": "Nome do Produto",
  "slug": "nome-do-produto",
  "price": 299.90,
  "originalPrice": 399.90,
  "image": "https://...",
  "amazonUrl": "https://amzn.to/...",
  "category": "tech",
  "featured": true,
  "bestSeller": true,
  "description": "Primeiro bullet point do produto..."
}
```

## Configuração

Edite as constantes no topo de `anuncios.py`:

| Variável        | Padrão              | Descrição                            |
|-----------------|---------------------|--------------------------------------|
| `AFFILIATE_TAG` | `fercugliandro-20`  | Tag do programa de afiliados         |
| `TOP_N`         | `10`                | Produtos coletados por categoria     |
| `OUTPUT_DIR`    | `output`            | Pasta de saída dos JSONs             |
| `COOKIES_FILE`  | `amazon_cookies.json` | Arquivo de sessão persistente      |

## Observações

- O arquivo `amazon_cookies.json` contém sua sessão autenticada — nunca o versione.
- O scraper usa um navegador real (Chromium via Playwright) para contornar proteções anti-bot.
- Respeite os [Termos de Uso](https://associados.amazon.com.br/help/operating/agreement) do programa de afiliados da Amazon.
