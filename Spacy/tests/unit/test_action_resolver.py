import pytest

from spacy_intent.application.action_resolver import ConfidenceBasedActionResolver
from spacy_intent.domain.entities import Action, IntentName
from spacy_intent.domain.registry import (
    IntentConfidence,
    IntentDefinition,
    IntentPatterns,
    IntentRegistry,
)


def _make_registry() -> IntentRegistry:
    registry = IntentRegistry()
    registry.register(
        IntentDefinition(
            name=IntentName.BUY_STOCK,
            action=Action(type="BUY_STOCK", description="comprar"),
            patterns=IntentPatterns(phrases=(), lemmas=()),
            confidence=IntentConfidence(phrase=0.92, lemma=0.75),
        )
    )
    registry.register(
        IntentDefinition(
            name=IntentName.SELL_STOCK,
            action=Action(type="SELL_STOCK", description="vender"),
            patterns=IntentPatterns(phrases=(), lemmas=()),
            confidence=IntentConfidence(phrase=0.92, lemma=0.75),
        )
    )
    return registry


MIN_CONFIDENCE = 0.70


@pytest.fixture
def resolver() -> ConfidenceBasedActionResolver:
    return ConfidenceBasedActionResolver(_make_registry(), MIN_CONFIDENCE)


def test_buy_with_high_confidence_returns_buy_action(resolver):
    action = resolver.resolve(IntentName.BUY_STOCK, 0.92)
    assert action.type == "BUY_STOCK"


def test_sell_with_high_confidence_returns_sell_action(resolver):
    action = resolver.resolve(IntentName.SELL_STOCK, 0.92)
    assert action.type == "SELL_STOCK"


def test_unknown_intent_returns_no_action(resolver):
    action = resolver.resolve(IntentName.UNKNOWN, 0.0)
    assert action.type == "NO_ACTION"


def test_low_confidence_returns_no_action_regardless_of_intent(resolver):
    action = resolver.resolve(IntentName.BUY_STOCK, 0.5)
    assert action.type == "NO_ACTION"


def test_exactly_at_threshold_executes_action(resolver):
    action = resolver.resolve(IntentName.BUY_STOCK, MIN_CONFIDENCE)
    assert action.type == "BUY_STOCK"


def test_just_below_threshold_returns_no_action(resolver):
    action = resolver.resolve(IntentName.BUY_STOCK, MIN_CONFIDENCE - 0.01)
    assert action.type == "NO_ACTION"


def test_unregistered_intent_returns_no_action(resolver):
    action = resolver.resolve("intent_desconhecida", 0.99)
    assert action.type == "NO_ACTION"


def test_low_confidence_action_has_descriptive_message(resolver):
    action = resolver.resolve(IntentName.SELL_STOCK, 0.3)
    assert "insuficiente" in action.description.lower()
