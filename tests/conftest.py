import pytest
from langchain_core.documents import Document
from langchain_core.embeddings import DeterministicFakeEmbedding
from langchain_core.runnables import RunnableLambda

from app.bot import BotReply, FaqBot

DOCS = [
    Document("Product: Gooseneck Kettle\nVariant: Brushed Steel; price 59.00 USD; out of stock",
             metadata={"id": "product:kettle", "type": "product", "title": "Gooseneck Kettle",
                       "url": "https://shop.example/products/kettle"}),
    Document("Store policy: Shipping\nWe ship to Canada for a flat $19.",
             metadata={"id": "policy:shipping", "type": "policy", "title": "Shipping"}),
    Document("FAQ: Do you sell decaf?\nYes.",
             metadata={"id": "faq:decaf", "type": "faq", "title": "Do you sell decaf?"}),
]


class FakeAnswerer:
    """Stands in for `llm.with_structured_output(BotReply)` and records each prompt."""

    def __init__(self, reply: BotReply | Exception):
        self.reply = reply
        self.prompts = []

    def __call__(self, prompt_value):
        self.prompts.append(prompt_value.to_messages())
        if isinstance(self.reply, Exception):
            raise self.reply
        return self.reply


@pytest.fixture
def make_bot():
    def factory(reply: BotReply | Exception, threshold: float = 0.7):
        answerer = FakeAnswerer(reply)
        bot = FaqBot(DOCS, DeterministicFakeEmbedding(size=32), RunnableLambda(answerer),
                     store_name="Test Store", confidence_threshold=threshold, k=4)
        return bot, answerer

    return factory

def backup_table(data=None):
    if data is None:
        return None
    return data

def acknowledge_receipt(data=None):
    if data is None:
        return None
    return data

def compress_payload(data=None):
    if data is None:
        return None
    return data

def backup_table(data=None):
    if data is None:
        return None
    return data