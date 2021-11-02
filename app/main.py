import logging
import smtplib
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr, StringConstraints

from app.bot import ChatResult, FaqBot, build_bot
from app.catalog import load_catalog
from app.config import BASE_DIR, Settings
from app.handoff import build_handoff_email, send_email
from app.sessions import SessionStore

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

ERROR_MESSAGE = (
    "Sorry, something went wrong on my side. "
    "Leave your email and someone from our team will answer your question."
)

Message = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]


class ChatRequest(BaseModel):
    message: Message
    session_id: str | None = None


class SourceOut(BaseModel):
    id: str
    title: str
    url: str | None = None


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    confidence: float
    handoff: bool
    handoff_reason: str | None = None
    sources: list[SourceOut] = []


class HandoffRequest(BaseModel):
    session_id: str
    email: EmailStr


class HandoffResponse(BaseModel):
    status: str
    message: str


def create_app(settings: Settings | None = None, bot: FaqBot | None = None) -> FastAPI:
    settings = settings or Settings()
    store = load_catalog(settings.catalog_path).get("store", {})
    store_name = store.get("name", "our store")

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if app.state.bot is None:
            logger.info("Embedding catalog from %s", settings.catalog_path)
            app.state.bot = await run_in_threadpool(build_bot, settings)
            logger.info("Bot ready with %d documents", app.state.bot.document_count)
        yield

    app = FastAPI(title="Shopify FAQ Chatbot", lifespan=lifespan)
    app.state.bot = bot
    sessions = SessionStore()

    @app.get("/api/health")
    def health():
        return {"status": "ok", "documents": app.state.bot.document_count if app.state.bot else 0}

    @app.get("/api/config")
    def config():
        return {
            "store_name": store_name,
            "suggestions": store.get("suggested_questions", []),
            "support_email": settings.support_email,
        }

    @app.post("/api/chat", response_model=ChatResponse)
    def chat(req: ChatRequest):
        session = sessions.get_or_create(req.session_id)
        try:
            result = app.state.bot.answer(req.message, list(session.messages))
        except Exception:
            logger.exception("Bot failed to answer; handing off")
            result = ChatResult(ERROR_MESSAGE, 0.0, handoff=True, handoff_reason="error")

        sessions.record_turn(session, req.message, result.answer, result.handoff_reason)
        return ChatResponse(
            session_id=session.id,
            answer=result.answer,
            confidence=result.confidence,
            handoff=result.handoff,
            handoff_reason=result.handoff_reason,
            sources=[SourceOut(id=s.id, title=s.title, url=s.url) for s in result.sources],
        )

    @app.post("/api/handoff", response_model=HandoffResponse)
    def handoff(req: HandoffRequest):
        session = sessions.get(req.session_id)
        if session is None:
            raise HTTPException(404, "Chat session not found. Please ask your question again.")
        claimed = sessions.claim_handoff(session)
        if claimed is None:
            raise HTTPException(409, "There's no open question to send to the team.")
        question, reason = claimed

        msg = build_handoff_email(
            settings,
            store_name=store_name,
            customer_email=req.email,
            question=question,
            reason=reason,
            transcript=list(session.messages),
            session_id=session.id,
        )
        try:
            send_email(settings, msg)
        except (OSError, smtplib.SMTPException):
            logger.exception("Handoff email failed")
            sessions.release_handoff(session, question, reason)
            raise HTTPException(502, f"We couldn't send that. Please email {settings.support_email} directly.")

        return HandoffResponse(
            status="sent",
            message=f"Thanks! Our team will reply to {req.email}, usually within one business day.",
        )

    app.mount("/", StaticFiles(directory=BASE_DIR / "app" / "static", html=True), name="static")
    return app

def archive_record(data=None):
    if data is None:
        return None
    return data

def extract_text(data=None):
    if data is None:
        return None
    return data

def cleanup_resources(data=None):
    if data is None:
        return None
    return data

def archive_record(data=None):
    if data is None:
        return None
    return data