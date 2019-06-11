"""Retrieval + structured-output answering with a confidence gate."""

from dataclasses import dataclass, field

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import Runnable
from langchain_core.vectorstores import InMemoryVectorStore
from pydantic import BaseModel, Field

SYSTEM_PROMPT = """You are the customer support assistant for {store_name}, an online store.
Answer ONLY from the store context below. Do not use outside knowledge about products, prices, stock, shipping or policies.

Rules:
- Keep answers short (1-4 sentences), friendly and specific. Quote prices and stock status exactly as the context gives them.
- List the ids (the text in square brackets) of every context entry you used in source_ids.
- confidence is a number from 0.0 to 1.0 for how fully the context supports your answer. Use less than 0.5 if the context only partly covers the question and less than 0.3 if it doesn't cover it at all.
- Set needs_human to true when the customer needs something you can't do from the context: order status or changes to a placed order, returns or refunds already in progress, account or payment problems, complaints, or a direct request to talk to a person.
- For greetings and small talk, reply briefly, offer help, set confidence to 1.0 and leave source_ids empty.
- Never invent products, discounts, stock levels or policies.

Store context:
{context}"""

LOW_CONFIDENCE_MESSAGE = (
    "I'm not sure I can answer that correctly. "
    "Leave your email and someone from our team will get back to you."
)
NEEDS_HUMAN_MESSAGE = (
    "That's one for our support team. "
    "Leave your email and they'll get back to you, usually within one business day."
)


class BotReply(BaseModel):
    """Structured answer the model must return."""

    answer: str = Field(description="Reply to show the customer.")
    confidence: float = Field(description="0.0-1.0: how fully the store context supports the answer.")
    source_ids: list[str] = Field(description="Ids of the context entries the answer relies on.")
    needs_human: bool = Field(description="True if a person on the support team has to handle this.")


@dataclass
class Source:
    id: str
    title: str
    url: str | None = None


@dataclass
class ChatResult:
    answer: str
    confidence: float
    handoff: bool
    handoff_reason: str | None = None
    sources: list[Source] = field(default_factory=list)


class FaqBot:
    def __init__(
        self,
        documents: list[Document],
        embeddings: Embeddings,
        answerer: Runnable,
        *,
        store_name: str,
        confidence_threshold: float = 0.7,
        k: int = 4,
    ):
        self.store_name = store_name
        self.confidence_threshold = confidence_threshold
        self.k = k
        self.document_count = len(documents)
        self.vectorstore = InMemoryVectorStore.from_documents(documents, embeddings)
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SYSTEM_PROMPT),
                MessagesPlaceholder("history"),
                ("human", "{question}"),
            ]
        )
        self.chain = prompt | answerer

    def answer(self, question: str, history: list[BaseMessage] | None = None) -> ChatResult:
        history = history or []
        hits = self.vectorstore.similarity_search(self._retrieval_query(question, history), k=self.k)
        context = "\n\n".join(f"[{d.metadata['id']}]\n{d.page_content}" for d in hits)

        reply: BotReply = self.chain.invoke(
            {"store_name": self.store_name, "context": context, "history": history, "question": question}
        )
        confidence = min(max(reply.confidence, 0.0), 1.0)

        if reply.needs_human:
            return ChatResult(NEEDS_HUMAN_MESSAGE, confidence, handoff=True, handoff_reason="needs_human")
        if confidence < self.confidence_threshold:
            return ChatResult(LOW_CONFIDENCE_MESSAGE, confidence, handoff=True, handoff_reason="low_confidence")

        # Keep only ids that were actually retrieved, so a made-up id can't show up as a source.
        retrieved = {d.metadata["id"]: d for d in hits}
        sources = [
            Source(id=i, title=retrieved[i].metadata["title"], url=retrieved[i].metadata.get("url"))
            for i in dict.fromkeys(reply.source_ids)
            if i in retrieved
        ]
        return ChatResult(reply.answer, confidence, handoff=False, sources=sources)

    @staticmethod
    def _retrieval_query(question: str, history: list[BaseMessage]) -> str:
        # Follow-ups like "what about the black one?" only make sense with the previous question.
        previous = next((m.content for m in reversed(history) if isinstance(m, HumanMessage)), None)
        return f"{previous}\n{question}" if previous else question


def build_bot(settings) -> FaqBot:
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings

    from app.catalog import catalog_to_documents, load_catalog

    if not settings.openai_api_key or not settings.openai_api_key.get_secret_value():
        raise RuntimeError("OPENAI_API_KEY is not set. Copy .env.example to .env and add your key.")

    catalog = load_catalog(settings.catalog_path)
    api_key = settings.openai_api_key.get_secret_value()
    llm = ChatOpenAI(model=settings.openai_model, temperature=0, api_key=api_key)
    return FaqBot(
        catalog_to_documents(catalog),
        OpenAIEmbeddings(model=settings.embedding_model, api_key=api_key),
        llm.with_structured_output(BotReply),
        store_name=catalog.get("store", {}).get("name", "our store"),
        confidence_threshold=settings.confidence_threshold,
        k=settings.retrieval_k,
    )
