# CLAUDE.md - Desenvolvimento e Execução do Projeto

Este arquivo serve como guia de desenvolvimento rápido e execução para desenvolvedores e agentes de IA que trabalhem neste repositório.

---

## 🚀 Comandos Rápidos de Execução

Sempre execute os comandos a partir da raiz do projeto usando o interpretador do ambiente virtual (`venv\Scripts\python` no Windows).

### 1. Raspagem de Produtos (Scrapers)
* **Apenas Mercado Livre (Ofertas Relâmpago):**
  ```bash
  venv\Scripts\python main.py --source mercadolivre
  ```
  *(Parâmetros úteis: `--pages 5` (quantidade de páginas), `--delay 1.5` (tempo entre requisições), `--reset` (ignora cache))*
* **Apenas Amazon (Mais Vendidos com SiteStripe):**
  ```bash
  venv\Scripts\python main.py --source amazon
  ```
  *(Parâmetros úteis: `--top-n 40` (produtos por categoria))*
* **Raspagem Completa (Ambas as fontes):**
  ```bash
  venv\Scripts\python main.py --source all
  ```

### 2. Consolidação de Catálogos (Merge)
Combina as saídas individuais do Mercado Livre e da Amazon e atualiza a exibição web:
```bash
venv\Scripts\python merge.py
```

### 3. Publicação e Versionamento (GitHub Commit/Push)
Copia o consolidado unificado para o repositório externo e faz o push para produção:
```bash
venv\Scripts\python commit.py
```

### 4. Geração Automática de Banners (Design)
Gera imagens 1080x1920px (Stories/Reels) com fotos reais dos produtos e cache inteligente:
```bash
venv\Scripts\python generate_banners.py
```
*(Parâmetros úteis: `--limit <n>` (limita a quantidade), `--all` (gera para todos os produtos do catálogo consolidado), `--force` (força a regeração de imagens pulando o cache))*

---

## 🛠️ Ambiente e Instalação

* **Pré-requisitos:** Python 3.11+ e Playwright (Chromium).
* **Instalação das Dependências:**
  ```bash
  venv\Scripts\python -m pip install -r requirements.txt
  venv\Scripts\playwright install chromium
  ```

---

## 📁 Estrutura de Arquivos e Saídas

* `main.py`: Ponto de entrada unificado para raspagem.
* `merge.py`: Rotina utilitária de consolidação de dados.
* `commit.py`: Rotina utilitária para publicação no repositório de produção `achadinhosporai-v2-data`.
* `output/`: Pasta destino de todos os JSONs gerados.
  - `ml_produtos.json`: Cache/saída do Mercado Livre.
  - `amazon_all.json`: Saída consolidada sem timestamp da Amazon.
  - `produtos_consolidado.json`: Catálogo unificado final.
  - `produtos.js`: Arquivo JS estático para o painel web.

---

## 🤖 Arquitetura de Agentes de IA

Este projeto está estruturado para ser operado de forma automatizada por **5 agentes inteligentes especializados**:
1. **`product_retriever_agent`** (Mercado Livre)
2. **`amazon_retriever_agent`** (Amazon)
3. **`products_merge_agent`** (Consolidador de dados)
4. **`image_generator_agent`** (Designer Gráfico)
5. **`github_commit_agent`** (Publicador no GitHub)

> [!NOTE]
> Para especificações detalhadas dos agentes (prompts de sistema sugeridos, entradas/saídas e fluxo de controle), consulte o arquivo de portabilidade: [agentes.md](file:///C:/Users/ferna/development/amazon-products/agentes.md) (ou [agents_specs.md](file:///C:/Users/ferna/development/amazon-products/agents_specs.md)).

---

## 📅 Agendamento Recorrente
O pipeline completo (ML Scraper ➔ Amazon Scraper ➔ Merge ➔ Git Push) está programado para executar automaticamente **a cada 3 horas** no ambiente local (Expressão Cron: `0 */3 * * *`).
