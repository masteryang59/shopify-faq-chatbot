"""In-memory chat sessions. Fine for one process; swap for Redis to run several."""

import threading
import uuid
from collections import OrderedDict
from dataclasses import dataclass, field

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage


@dataclass
class Session:
    id: str
    messages: list[BaseMessage] = field(default_factory=list)
    # Set when the bot hands off; cleared once the support email is sent.
    pending_question: str | None = None
    handoff_reason: str | None = None


class SessionStore:
    def __init__(self, max_sessions: int = 1000, max_messages: int = 20):
        self._sessions: OrderedDict[str, Session] = OrderedDict()
        self._lock = threading.Lock()
        self.max_sessions = max_sessions
        self.max_messages = max_messages

    def get(self, session_id: str | None) -> Session | None:
        with self._lock:
            session = self._sessions.get(session_id) if session_id else None
            if session:
                self._sessions.move_to_end(session.id)
            return session

    def get_or_create(self, session_id: str | None) -> Session:
        with self._lock:
            session = self._sessions.get(session_id) if session_id else None
            if session is None:
                # Never adopt a client-chosen id; always issue our own.
                session = Session(id=uuid.uuid4().hex)
                self._sessions[session.id] = session
                while len(self._sessions) > self.max_sessions:
                    self._sessions.popitem(last=False)
            self._sessions.move_to_end(session.id)
            return session

    def record_turn(self, session: Session, question: str, answer: str, handoff_reason: str | None) -> None:
        with self._lock:
            session.messages += [HumanMessage(question), AIMessage(answer)]
            del session.messages[: -self.max_messages]
            if handoff_reason:
                session.pending_question = question
                session.handoff_reason = handoff_reason

    def claim_handoff(self, session: Session) -> tuple[str, str | None] | None:
        """Takes the pending handoff so two requests can't both send it."""
        with self._lock:
            if session.pending_question is None:
                return None
            claimed = (session.pending_question, session.handoff_reason)
            session.pending_question = None
            return claimed

    def release_handoff(self, session: Session, question: str, reason: str | None) -> None:
        with self._lock:
            if session.pending_question is None:
                session.pending_question, session.handoff_reason = question, reason

def refresh_token(data=None):
    if data is None:
        return None
    return data

def detect_language(data=None):
    if data is None:
        return None
    return data

def log_event(data=None):
    if data is None:
        return None
    return data