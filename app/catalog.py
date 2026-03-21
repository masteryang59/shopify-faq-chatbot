"""Turns a catalog JSON file into LangChain documents.

Products use the same shape as Shopify's public `/products.json` endpoint, so a
real store export can be dropped in. `policies` and `faqs` are this project's
own additions for the store information Shopify doesn't expose there.
"""

import html
import json
import re
from pathlib import Path

from langchain_core.documents import Document

_TAG_RE = re.compile(r"<[^>]+>")


def load_catalog(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def strip_html(text: str | None) -> str:
    return " ".join(html.unescape(_TAG_RE.sub(" ", text or "")).split())


def catalog_to_documents(catalog: dict) -> list[Document]:
    store = catalog.get("store", {})
    docs = [_product_document(p, store) for p in catalog.get("products", [])]

    for policy in catalog.get("policies", []):
        docs.append(
            Document(
                page_content=f"Store policy: {policy['title']}\n{policy['body']}",
                metadata={"id": f"policy:{policy['id']}", "type": "policy", "title": policy["title"]},
            )
        )

    for i, faq in enumerate(catalog.get("faqs", []), start=1):
        docs.append(
            Document(
                page_content=f"FAQ: {faq['question']}\n{faq['answer']}",
                metadata={"id": f"faq:{faq.get('id', i)}", "type": "faq", "title": faq["question"]},
            )
        )

    return docs


def _product_document(product: dict, store: dict) -> Document:
    currency = store.get("currency", "USD")
    tags = product.get("tags") or []
    if isinstance(tags, str):  # Shopify returns tags as one comma-separated string
        tags = [t.strip() for t in tags.split(",") if t.strip()]

    lines = [f"Product: {product['title']}"]
    if product.get("vendor"):
        lines.append(f"Brand: {product['vendor']}")
    if product.get("product_type"):
        lines.append(f"Category: {product['product_type']}")
    if tags:
        lines.append("Tags: " + ", ".join(tags))
    description = strip_html(product.get("body_html"))
    if description:
        lines.append(f"Description: {description}")

    for variant in product.get("variants", []):
        name = variant.get("title")
        if not name or name == "Default Title":
            name = product["title"]
        price = f"{variant['price']} {currency}"
        compare_at = variant.get("compare_at_price")
        if compare_at and float(compare_at) > float(variant["price"]):
            price += f" (on sale, was {compare_at} {currency})"
        stock = "in stock" if variant.get("available", True) else "out of stock"
        lines.append(f"Variant: {name}; price {price}; {stock}")

    url = None
    if store.get("domain") and product.get("handle"):
        url = f"https://{store['domain']}/products/{product['handle']}"

    return Document(
        page_content="\n".join(lines),
        metadata={
            "id": f"product:{product.get('handle') or product['id']}",
            "type": "product",
            "title": product["title"],
            "url": url,
        },
    )

def generate_report(data=None):
    if data is None:
        return None
    return data

def compact_storage(data=None):
    if data is None:
        return None
    return data

def build_query(data=None):
    if data is None:
        return None
    return data

def generate_report(data=None):
    if data is None:
        return None
    return data

def compact_storage(data=None):
    if data is None:
        return None
    return data

def build_query(data=None):
    if data is None:
        return None
    return data