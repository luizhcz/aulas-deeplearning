import pytest

from spacy_intent.domain.entities import Action, IntentName, IntentResult


def test_intent_name_constants():
    assert IntentName.BUY_STOCK == "buy_stock"
    assert IntentName.SELL_STOCK == "sell_stock"
    assert IntentName.UNKNOWN == "unknown"


def test_action_is_immutable():
    action = Action(type="BUY_STOCK", description="comprar")
    with pytest.raises(Exception):
        action.type = "SELL_STOCK"  # type: ignore[misc]


def test_intent_result_is_immutable():
    result = IntentResult(
        text="comprar",
        intent=IntentName.BUY_STOCK,
        confidence=0.9,
        action=Action(type="BUY_STOCK", description="comprar"),
    )
    with pytest.raises(Exception):
        result.confidence = 0.5  # type: ignore[misc]


def test_intent_result_stores_all_fields():
    action = Action(type="BUY_STOCK", description="comprar")
    result = IntentResult(
        text="msg",
        intent=IntentName.BUY_STOCK,
        confidence=0.9,
        action=action,
    )
    assert result.text == "msg"
    assert result.intent == IntentName.BUY_STOCK
    assert result.confidence == 0.9
    assert result.action == action


def test_intent_result_intent_is_string():
    result = IntentResult(
        text="x",
        intent="custom_intent",
        confidence=0.5,
        action=Action(type="NO_ACTION", description=""),
    )
    assert isinstance(result.intent, str)
