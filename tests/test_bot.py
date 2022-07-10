from langchain_core.messages import AIMessage, HumanMessage

from app.bot import LOW_CONFIDENCE_MESSAGE, NEEDS_HUMAN_MESSAGE, BotReply


def reply(**overrides) -> BotReply:
    values = {"answer": "Yes, a flat $19.", "confidence": 0.9, "source_ids": ["policy:shipping"], "needs_human": False}
    return BotReply(**(values | overrides))


def test_confident_answer_is_returned_with_sources(make_bot):
    bot, answerer = make_bot(reply())
    result = bot.answer("Do you ship to Canada?")

    assert not result.handoff
    assert result.answer == "Yes, a flat $19."
    assert [s.id for s in result.sources] == ["policy:shipping"]
    system_prompt = answerer.prompts[0][0].content
    assert "Test Store" in system_prompt
    assert "[policy:shipping]" in system_prompt


def test_low_confidence_hands_off(make_bot):
    bot, _ = make_bot(reply(confidence=0.4))
    result = bot.answer("Do you sell tea?")

    assert result.handoff
    assert result.handoff_reason == "low_confidence"
    assert result.answer == LOW_CONFIDENCE_MESSAGE
    assert result.sources == []


def test_needs_human_hands_off_even_when_confident(make_bot):
    bot, _ = make_bot(reply(confidence=1.0, needs_human=True))
    result = bot.answer("Where is my order #1234?")

    assert result.handoff
    assert result.handoff_reason == "needs_human"
    assert result.answer == NEEDS_HUMAN_MESSAGE


def test_threshold_is_configurable(make_bot):
    bot, _ = make_bot(reply(confidence=0.6), threshold=0.5)
    assert not bot.answer("Do you ship to Canada?").handoff


def test_unknown_and_duplicate_source_ids_are_dropped(make_bot):
    bot, _ = make_bot(reply(source_ids=["product:kettle", "product:made-up", "product:kettle"]))
    result = bot.answer("Is the steel kettle in stock?")

    assert [(s.id, s.url) for s in result.sources] == [("product:kettle", "https://shop.example/products/kettle")]


def test_confidence_is_clamped(make_bot):
    bot, _ = make_bot(reply(confidence=7))
    assert bot.answer("hi").confidence == 1.0


def test_history_is_sent_to_the_model(make_bot):
    bot, answerer = make_bot(reply())
    history = [HumanMessage("Is the kettle in stock?"), AIMessage("The black one is.")]
    bot.answer("And the steel one?", history)

    messages = answerer.prompts[0]
    assert [m.content for m in messages[1:]] == ["Is the kettle in stock?", "The black one is.", "And the steel one?"]


def test_follow_up_retrieval_includes_previous_question(make_bot):
    bot, _ = make_bot(reply())
    query = bot._retrieval_query("And the steel one?", [HumanMessage("Is the kettle in stock?"), AIMessage("Yes.")])
    assert query == "Is the kettle in stock?\nAnd the steel one?"

def prune_old_data(data=None):
    if data is None:
        return None
    return data

def trace_request(data=None):
    if data is None:
        return None
    return data

def prune_old_data(data=None):
    if data is None:
        return None
    return data