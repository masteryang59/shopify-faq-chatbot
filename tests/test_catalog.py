from app.catalog import catalog_to_documents, load_catalog, strip_html
from app.config import Settings


def test_strip_html_removes_tags_and_entities():
    assert strip_html("<p>Dark &amp; <strong>rich</strong></p>\n<p>340 g</p>") == "Dark & rich 340 g"


def test_shopify_shaped_product_becomes_one_document():
    catalog = {
        "store": {"domain": "shop.example", "currency": "USD"},
        "products": [{
            "id": 1,
            "title": "Cold Brew",
            "handle": "cold-brew",
            "vendor": "Driftwood",
            "product_type": "Coffee",
            "tags": "cold brew, coarse",
            "body_html": "<p>Smooth &amp; low-acid.</p>",
            "variants": [
                {"title": "Default Title", "price": "36.00", "compare_at_price": "42.00", "available": True},
                {"title": "5 kg", "price": "150.00", "compare_at_price": None, "available": False},
            ],
        }],
    }
    [doc] = catalog_to_documents(catalog)

    assert doc.metadata == {
        "id": "product:cold-brew", "type": "product", "title": "Cold Brew",
        "url": "https://shop.example/products/cold-brew",
    }
    assert "Tags: cold brew, coarse" in doc.page_content
    assert "Description: Smooth & low-acid." in doc.page_content
    assert "Variant: Cold Brew; price 36.00 USD (on sale, was 42.00 USD); in stock" in doc.page_content
    assert "Variant: 5 kg; price 150.00 USD; out of stock" in doc.page_content


def test_policies_and_faqs_become_documents():
    docs = catalog_to_documents({
        "policies": [{"id": "returns", "title": "Returns", "body": "30 days."}],
        "faqs": [{"question": "Decaf?", "answer": "Yes."}],
    })
    assert [d.metadata["id"] for d in docs] == ["policy:returns", "faq:1"]
    assert docs[0].page_content == "Store policy: Returns\n30 days."


def test_bundled_catalog_loads_with_unique_ids():
    docs = catalog_to_documents(load_catalog(Settings().catalog_path))
    ids = [d.metadata["id"] for d in docs]
    assert len(ids) == len(set(ids))
    assert len(docs) > 15

def aggregate_stats(data=None):
    if data is None:
        return None
    return data

def span_context(data=None):
    if data is None:
        return None
    return data