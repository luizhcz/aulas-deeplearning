"""Testes de integração que exercitam o pipeline completo com spaCy."""

import pytest

from spacy_intent.domain.entities import IntentName
from spacy_intent.engine import IntentEngine
from spacy_intent.exceptions import InvalidInputError


@pytest.fixture(scope="module")
def engine() -> IntentEngine:
    return IntentEngine.from_config()


class TestBuyIntent:
    def test_explicit_phrase_classified_as_buy(self, engine):
        result = engine.process("quero comprar ações da Petrobras")
        assert result.intent == IntentName.BUY_STOCK

    def test_explicit_phrase_has_high_confidence(self, engine):
        result = engine.process("quero comprar ações da Petrobras")
        assert result.confidence >= 0.9

    def test_explicit_phrase_triggers_buy_action(self, engine):
        result = engine.process("quero comprar ações da Petrobras")
        assert result.action.type == "BUY_STOCK"

    def test_verb_lemma_classified_as_buy(self, engine):
        result = engine.process("preciso comprar hoje")
        assert result.intent == IntentName.BUY_STOCK
        assert result.action.type == "BUY_STOCK"

    def test_acquire_verb_classified_as_buy(self, engine):
        result = engine.process("desejo adquirir papéis da Vale")
        assert result.intent == IntentName.BUY_STOCK

    def test_result_preserves_original_text(self, engine):
        text = "  quero comprar ações  "
        result = engine.process(text)
        assert result.text == text


class TestSellIntent:
    def test_explicit_phrase_classified_as_sell(self, engine):
        result = engine.process("quero vender minhas ações")
        assert result.intent == IntentName.SELL_STOCK

    def test_explicit_phrase_has_high_confidence(self, engine):
        result = engine.process("quero vender minhas ações")
        assert result.confidence >= 0.9

    def test_explicit_phrase_triggers_sell_action(self, engine):
        result = engine.process("quero vender minhas ações")
        assert result.action.type == "SELL_STOCK"

    def test_verb_lemma_classified_as_sell(self, engine):
        result = engine.process("preciso vender agora")
        assert result.intent == IntentName.SELL_STOCK
        assert result.action.type == "SELL_STOCK"


class TestUnknownIntent:
    def test_unrelated_phrase_classified_as_unknown(self, engine):
        result = engine.process("bom dia, como você está?")
        assert result.intent == IntentName.UNKNOWN

    def test_unrelated_phrase_has_zero_confidence(self, engine):
        result = engine.process("bom dia, como você está?")
        assert result.confidence == 0.0

    def test_unrelated_phrase_returns_no_action(self, engine):
        result = engine.process("bom dia, como você está?")
        assert result.action.type == "NO_ACTION"


class TestInputValidation:
    def test_empty_string_raises(self, engine):
        with pytest.raises(InvalidInputError):
            engine.process("")

    def test_whitespace_only_raises(self, engine):
        with pytest.raises(InvalidInputError):
            engine.process("   ")

    def test_text_too_long_raises(self, engine):
        with pytest.raises(InvalidInputError):
            engine.process("a" * 1001)


class TestIntentResultStructure:
    def test_result_has_all_required_fields(self, engine):
        result = engine.process("qualquer coisa")
        assert hasattr(result, "text")
        assert hasattr(result, "intent")
        assert hasattr(result, "confidence")
        assert hasattr(result, "action")

    def test_intent_is_string(self, engine):
        result = engine.process("quero comprar")
        assert isinstance(result.intent, str)

    def test_confidence_is_between_zero_and_one(self, engine):
        for phrase in ["quero comprar", "quero vender", "olá mundo"]:
            result = engine.process(phrase)
            assert 0.0 <= result.confidence <= 1.0

    def test_preprocessing_strips_text_before_classify(self, engine):
        result_clean = engine.process("quero comprar")
        result_padded = engine.process("  quero comprar  ")
        assert result_clean.intent == result_padded.intent
        assert result_clean.confidence == result_padded.confidence
