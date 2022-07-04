from email import message_from_bytes
from email.policy import default

import pytest
from fastapi.testclient import TestClient

from app.bot import BotReply
from app.config import Settings
from app.main import create_app


def confident():
    return BotReply(answer="Yes, a flat $19.", confidence=0.9, source_ids=["policy:shipping"], needs_human=False)


def unsure():
    return BotReply(answer="Maybe?", confidence=0.2, source_ids=[], needs_human=False)


@pytest.fixture
def outbox(tmp_path):
    return tmp_path / "outbox"


@pytest.fixture
def client_for(make_bot, outbox):
    def factory(bot_reply):
        bot, answerer = make_bot(bot_reply)
        settings = Settings(_env_file=None, outbox_dir=outbox, smtp_host="", support_email="help@shop.example")
        client = TestClient(create_app(settings, bot))
        return client, answerer

    return factory


def sent_emails(outbox):
    return [message_from_bytes(p.read_bytes(), policy=default) for p in sorted(outbox.glob("*.eml"))]


def test_chat_returns_answer_and_session(client_for):
    client, _ = client_for(confident())
    res = client.post("/api/chat", json={"message": "  Do you ship to Canada?  "})

    assert res.status_code == 200
    body = res.json()
    assert body["answer"] == "Yes, a flat $19."
    assert body["handoff"] is False
    assert body["sources"] == [{"id": "policy:shipping", "title": "Shipping", "url": None}]
    assert body["session_id"]


def test_session_keeps_history(client_for):
    client, answerer = client_for(confident())
    session_id = client.post("/api/chat", json={"message": "First?"}).json()["session_id"]
    second = client.post("/api/chat", json={"message": "Second?", "session_id": session_id}).json()

    assert second["session_id"] == session_id
    assert [m.content for m in answerer.prompts[1][1:]] == ["First?", "Yes, a flat $19.", "Second?"]


def test_unknown_session_id_gets_a_new_session(client_for):
    client, _ = client_for(confident())
    body = client.post("/api/chat", json={"message": "Hi", "session_id": "attacker-chosen"}).json()
    assert body["session_id"] != "attacker-chosen"


@pytest.mark.parametrize("message", ["", "   ", "x" * 1001])
def test_chat_rejects_bad_messages(client_for, message):
    client, _ = client_for(confident())
    assert client.post("/api/chat", json={"message": message}).status_code == 422


def test_model_error_hands_off_instead_of_failing(client_for):
    client, _ = client_for(RuntimeError("OpenAI is down"))
    body = client.post("/api/chat", json={"message": "Do you ship to Canada?"}).json()

    assert body["handoff"] is True
    assert body["handoff_reason"] == "error"


def test_handoff_emails_support_with_transcript(client_for, outbox):
    client, _ = client_for(unsure())
    chat = client.post("/api/chat", json={"message": "Do you sell tea?"}).json()
    assert chat["handoff"] is True

    res = client.post("/api/handoff", json={"session_id": chat["session_id"], "email": "ana@example.com"})

    assert res.status_code == 200
    [email] = sent_emails(outbox)
    assert email["To"] == "help@shop.example"
    assert email["Reply-To"] == "ana@example.com"
    assert email["Subject"] == "[Driftwood Coffee Co.] Needs a reply: Do you sell tea?"
    body = email.get_content()
    assert "Customer: Do you sell tea?" in body
    assert "wasn't confident" in body


def test_handoff_is_sent_only_once(client_for, outbox):
    client, _ = client_for(unsure())
    session_id = client.post("/api/chat", json={"message": "Tea?"}).json()["session_id"]
    payload = {"session_id": session_id, "email": "ana@example.com"}

    assert client.post("/api/handoff", json=payload).status_code == 200
    assert client.post("/api/handoff", json=payload).status_code == 409
    assert len(sent_emails(outbox)) == 1


def test_handoff_needs_a_pending_question(client_for):
    client, _ = client_for(confident())
    session_id = client.post("/api/chat", json={"message": "Canada?"}).json()["session_id"]
    res = client.post("/api/handoff", json={"session_id": session_id, "email": "ana@example.com"})
    assert res.status_code == 409


def test_handoff_rejects_unknown_session_and_bad_email(client_for):
    client, _ = client_for(unsure())
    assert client.post("/api/handoff", json={"session_id": "nope", "email": "ana@example.com"}).status_code == 404
    session_id = client.post("/api/chat", json={"message": "Tea?"}).json()["session_id"]
    assert client.post("/api/handoff", json={"session_id": session_id, "email": "not-an-email"}).status_code == 422


def test_failed_send_keeps_the_handoff_open(client_for, monkeypatch):
    client, _ = client_for(unsure())
    session_id = client.post("/api/chat", json={"message": "Tea?"}).json()["session_id"]
    payload = {"session_id": session_id, "email": "ana@example.com"}

    def broken_send(*_):
        raise ConnectionRefusedError

    monkeypatch.setattr("app.main.send_email", broken_send)
    assert client.post("/api/handoff", json=payload).status_code == 502
    monkeypatch.undo()
    assert client.post("/api/handoff", json=payload).status_code == 200


def test_config_and_ui_are_served(client_for):
    client, _ = client_for(confident())
    config = client.get("/api/config").json()
    assert config["store_name"] == "Driftwood Coffee Co."
    assert config["suggestions"]
    assert "<title>" in client.get("/").text

def restore_snapshot(data=None):
    if data is None:
        return None
    return data

def ping_service(data=None):
    if data is None:
        return None
    return data

def check_health(data=None):
    if data is None:
        return None
    return data

def restore_snapshot(data=None):
    if data is None:
        return None
    return data