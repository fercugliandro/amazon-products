import os

# ── Amazon ─────────────────────────────────────────────────────────────────────
AMAZON_AFFILIATE_TAG = os.getenv("AMAZON_AFFILIATE_TAG", "fercugliandro-20")
AMAZON_COOKIES_FILE = "amazon_cookies.json"
AMAZON_TOP_N = 40

AMAZON_CATEGORIES = {
    "tech": {
        "label": "Eletrônicos",
        "url": "https://www.amazon.com.br/gp/bestsellers/electronics/",
    },
    "gaming": {
        "label": "Games e Consoles",
        "url": "https://www.amazon.com.br/gp/bestsellers/videogames/",
    },
    "beauty": {
        "label": "Beleza e Cuidados Pessoais",
        "url": "https://www.amazon.com.br/gp/bestsellers/beauty/",
    },
    "home": {
        "label": "Casa e Cozinha",
        "url": "https://www.amazon.com.br/gp/bestsellers/kitchen/",
    },
    "baby": {
        "label": "Bebês",
        "url": "https://www.amazon.com.br/gp/bestsellers/baby-products/?ie=UTF8&ref_=sv_b_1",
    },
    "fitness": {
        "label": "Esportes e Aventura",
        "url": "https://www.amazon.com.br/gp/bestsellers/sports/",
    },
    "automotive": {
        "label": "Automotivo",
        "url": "https://www.amazon.com.br/gp/bestsellers/automotive/",
    },
    "pets_cachorro": {
        "label": "Pet Shop - Cachorro",
        "url": "https://www.amazon.com.br/gp/bestsellers/pet-products/19653951011/",
    },
    "pets_gato": {
        "label": "Pet Shop - Gato",
        "url": "https://www.amazon.com.br/gp/bestsellers/pet-products/19653950011/",
    },
    "perfumaria_feminina": {
        "label": "Perfumaria Feminina",
        "url": "https://www.amazon.com.br/gp/bestsellers/beauty/?ie=UTF8&ref_=sv_b_1",
    }
}

# ── Mercado Livre ───────────────────────────────────────────────────────────────
ML_AFFILIATE_ID = os.getenv("ML_AFFILIATE_ID", "GABRIELWIRE")
ML_OFFERS_URL = "https://www.mercadolivre.com.br/ofertas"
ML_PAGE_SIZE = 20
ML_REQUEST_DELAY = 1.5
ML_PRICE_INCREASE_TOLERANCE = 0.05  # remove produto se preço subiu mais de 5%

ML_KEYWORD_CATEGORY_MAP = {
    "tech": [
        "smartphone", "celular", "iphone", "samsung galaxy", "tv ", "smart tv",
        "notebook", "laptop", "impressora", "tablet", "câmera", "headphone",
        "fone", "monitor", "teclado", "mouse", "placa de vídeo", "processador",
        "ssd", "memória", "roteador", "wifi", "alexa", "echo", "fire tv",
        "carregador", "bateria", "cabo usb", "hub", "pendrive", "hd externo",
        "action camera", "drone", "projetor", "caixa de som", "speaker",
    ],
    "home": [
        "máquina de lavar", "geladeira", "fogão", "micro-ondas", "microondas",
        "panela", "varal", "cadeira", "mesa ", "sofá", "colchão", "travesseiro",
        "jogo de cama", "cobertor", "ventilador", "ar condicionado", "purificador",
        "liquidificador", "batedeira", "fritadeira", "airfryer", "aspirador",
        "robô limpeza", "vassoura", "ferro de passar", "organizer", "prateleira",
        "rack", "estante", "luminária", "lâmpada", "tomada", "extensão",
    ],
    "fashion": [
        "tênis", "calçado", "sandália", "chinelo", "sapato", "bota",
        "camiseta", "camisa", "calça", "bermuda", "shorts", "vestido",
        "jaqueta", "moletom", "mochila", "bolsa", "carteira", "relógio",
        "óculos", "perfume", "acessório",
    ],
    "sports": [
        "creatina", "whey", "suplemento", "proteína", "vitamina",
        "bicicleta", "esteira", "haltere", "musculação", "natação",
        "chuteira", "luva", "capacete", "skate", "patins",
    ],
    "beauty": [
        "shampoo", "condicionador", "hidratante", "protetor solar",
        "maquiagem", "batom", "base", "sérum", "creme", "desodorante",
        "escova", "secador", "chapinha", "prancha", "perfumaria"
    ],
}

ML_DEFAULT_CATEGORY = "geral"

# ── Saída ───────────────────────────────────────────────────────────────────────
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")
ML_OUTPUT_FILE = os.path.join(OUTPUT_DIR, "ml_produtos.json")
PRODUTOS_JS_PATH = os.getenv("PRODUTOS_JS_PATH", os.path.join(OUTPUT_DIR, "produtos.js"))
