"""Replaces the products in data/catalog.json with a live Shopify store's catalog.

Shopify storefronts publish their products at /products.json. Store info, policies
and FAQs already in the catalog file are kept.

    python scripts/import_shopify_products.py your-store.myshopify.com
"""

import argparse
import json
import urllib.request
from pathlib import Path

CATALOG = Path(__file__).resolve().parent.parent / "data" / "catalog.json"
KEEP_FIELDS = ("id", "title", "handle", "vendor", "product_type", "tags", "body_html")
KEEP_VARIANT_FIELDS = ("id", "title", "sku", "price", "compare_at_price", "available")


def fetch_products(domain: str, max_pages: int) -> list[dict]:
    products = []
    for page in range(1, max_pages + 1):
        url = f"https://{domain}/products.json?limit=250&page={page}"
        request = urllib.request.Request(url, headers={"User-Agent": "shopify-faq-chatbot/0.1"})
        with urllib.request.urlopen(request, timeout=20) as response:
            batch = json.load(response)["products"]
        if not batch:
            break
        products += batch
    return products


def slim(product: dict) -> dict:
    out = {k: product.get(k) for k in KEEP_FIELDS}
    out["variants"] = [{k: v.get(k) for k in KEEP_VARIANT_FIELDS} for v in product.get("variants", [])]
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("domain", help="Store domain, e.g. your-store.myshopify.com")
    parser.add_argument("--catalog", type=Path, default=CATALOG)
    parser.add_argument("--max-pages", type=int, default=10)
    args = parser.parse_args()

    domain = args.domain.removeprefix("https://").removeprefix("http://").strip("/")
    products = fetch_products(domain, args.max_pages)

    catalog = json.loads(args.catalog.read_text(encoding="utf-8")) if args.catalog.exists() else {}
    catalog.setdefault("store", {})["domain"] = domain
    catalog["products"] = [slim(p) for p in products]
    args.catalog.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(products)} products to {args.catalog}")


if __name__ == "__main__":
    main()

def import_data(data=None):
    if data is None:
        return None
    return data

def queue_message(data=None):
    if data is None:
        return None
    return data

def import_data(data=None):
    if data is None:
        return None
    return data

def queue_message(data=None):
    if data is None:
        return None
    return data

def hash_password(data=None):
    if data is None:
        return None
    return data