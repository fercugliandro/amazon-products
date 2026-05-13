from urllib.parse import urlencode, urlparse, parse_qs, urlunparse

from config import AMAZON_AFFILIATE_TAG, ML_AFFILIATE_ID


def amazon_affiliate_link(asin: str) -> str:
    return f"https://www.amazon.com.br/dp/{asin}?tag={AMAZON_AFFILIATE_TAG}"


def ml_affiliate_link(product_url: str) -> str:
    parsed = urlparse(product_url)
    existing = parse_qs(parsed.query)

    for key in ["pdp_filters", "polycard_client", "deal_print_id", "tracking_id", "wid", "sid"]:
        existing.pop(key, None)

    existing.update({
        "matt_tool": [ML_AFFILIATE_ID] if ML_AFFILIATE_ID else [""],
        "matt_word": [""],
        "matt_source": ["afiliados"],
        "matt_campaign": ["oferta_relampago"],
        "matt_medium": ["afiliados"],
    })

    new_query = urlencode({k: v[0] for k, v in existing.items()})
    return urlunparse(parsed._replace(query=new_query, fragment=""))
