from unittest.mock import MagicMock

import pytest

from spacy_intent.application.use_cases import ClassifyIntentUseCase
from spacy_intent.domain.entities import Action, IntentName, IntentResult
from spacy_intent.exceptions import InvalidInputError


@pytest.fixture
def mock_classifier():
    return MagicMock()


@pytest.fixture
def mock_resolver():
    return MagicMock()


def test_execute_combines_classifier_and_resolver(mock_classifier, mock_resolver):
    mock_classifier.classify.return_value = (IntentName.BUY_STOCK, 0.92)
    mock_resolver.resolve.return_value = Action(type="BUY_STOCK", description="comprar")

    use_case = ClassifyIntentUseCase(mock_classifier, mock_resolver)
    result = use_case.execute("quero comprar")

    assert isinstance(result, IntentResult)
    assert result.intent == IntentName.BUY_STOCK
    assert result.confidence == 0.92
    assert result.action.type == "BUY_STOCK"
    assert result.text == "quero comprar"


def test_execute_passes_text_to_classifier(mock_classifier, mock_resolver):
    mock_classifier.classify.return_value = (IntentName.UNKNOWN, 0.0)
    mock_resolver.resolve.return_value = Action(type="NO_ACTION", description="")

    use_case = ClassifyIntentUseCase(mock_classifier, mock_resolver)
    use_case.execute("minha mensagem")

    mock_classifier.classify.assert_called_once_with("minha mensagem")


def test_execute_passes_intent_and_confidence_to_resolver(mock_classifier, mock_resolver):
    mock_classifier.classify.return_value = (IntentName.SELL_STOCK, 0.75)
    mock_resolver.resolve.return_value = Action(type="SELL_STOCK", description="vender")

    use_case = ClassifyIntentUseCase(mock_classifier, mock_resolver)
    use_case.execute("vender")

    mock_resolver.resolve.assert_called_once_with(IntentName.SELL_STOCK, 0.75)


def test_empty_text_raises_invalid_input(mock_classifier, mock_resolver):
    use_case = ClassifyIntentUseCase(mock_classifier, mock_resolver)
    with pytest.raises(InvalidInputError):
        use_case.execute("")


def test_whitespace_only_raises_invalid_input(mock_classifier, mock_resolver):
    use_case = ClassifyIntentUseCase(mock_classifier, mock_resolver)
    with pytest.raises(InvalidInputError):
        use_case.execute("   ")


def test_text_exceeding_limit_raises_invalid_input(mock_classifier, mock_resolver):
    use_case = ClassifyIntentUseCase(mock_classifier, mock_resolver)
    with pytest.raises(InvalidInputError):
        use_case.execute("a" * 1001)


def test_non_string_raises_invalid_input(mock_classifier, mock_resolver):
    use_case = ClassifyIntentUseCase(mock_classifier, mock_resolver)
    with pytest.raises(InvalidInputError):
        use_case.execute(123)  # type: ignore[arg-type]


def test_classifier_receives_preprocessed_text(mock_classifier, mock_resolver):
    """O classificador deve receber o texto pré-processado, não o original."""
    from spacy_intent.application.preprocessing import PreprocessingPipeline, StripWhitespacePreprocessor

    mock_classifier.classify.return_value = (IntentName.BUY_STOCK, 0.92)
    mock_resolver.resolve.return_value = Action(type="BUY_STOCK", description="")

    preprocessor = PreprocessingPipeline(steps=[StripWhitespacePreprocessor()])
    use_case = ClassifyIntentUseCase(mock_classifier, mock_resolver, preprocessor)
    use_case.execute("  quero comprar  ")

    mock_classifier.classify.assert_called_once_with("quero comprar")
