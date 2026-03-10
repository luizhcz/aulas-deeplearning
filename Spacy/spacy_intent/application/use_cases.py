import time

from spacy_intent.application.preprocessing import PreprocessingPipeline
from spacy_intent.domain.entities import IntentResult
from spacy_intent.domain.parsing import InputParserPort
from spacy_intent.domain.ports import ActionResolverPort, IntentClassifierPort
from spacy_intent.exceptions import InvalidInputError

_MAX_TEXT_LENGTH = 1_000


def _validate(text: str) -> None:
    if not isinstance(text, str):
        raise InvalidInputError(f"Esperado str, recebido {type(text).__name__}")
    if not text or not text.strip():
        raise InvalidInputError("O texto não pode ser vazio ou apenas espaços")
    if len(text) > _MAX_TEXT_LENGTH:
        raise InvalidInputError(
            f"Texto com {len(text)} caracteres excede o limite de {_MAX_TEXT_LENGTH}"
        )


class ClassifyIntentUseCase:
    """Orquestra validação, roteamento de formato, classificação e resolução de ação."""

    def __init__(
        self,
        classifier: IntentClassifierPort,
        action_resolver: ActionResolverPort,
        preprocessor: PreprocessingPipeline | None = None,
        structured_parsers: list[InputParserPort] | None = None,
    ) -> None:
        self._classifier = classifier
        self._action_resolver = action_resolver
        self._preprocessor = preprocessor or PreprocessingPipeline(steps=[])
        self._structured_parsers = structured_parsers or []

    def execute(self, text: str) -> IntentResult:
        start = time.perf_counter()
        _validate(text)

        # — Rota 1: input estruturado (regex, O(1), bypassa spaCy) —
        for parser in self._structured_parsers:
            if parser.can_parse(text):
                parsed = parser.parse(text)
                action = self._action_resolver.resolve(parsed.intent, parsed.confidence)
                return IntentResult(
                    text=text,
                    intent=parsed.intent,
                    confidence=parsed.confidence,
                    action=action,
                    entities=parsed.entities,
                    duration_ms=round((time.perf_counter() - start) * 1_000, 3),
                )

        # — Rota 2: linguagem natural (pré-processamento + spaCy) —
        processed = self._preprocessor.run(text)
        intent, confidence = self._classifier.classify(processed)
        action = self._action_resolver.resolve(intent, confidence)
        return IntentResult(
            text=text,
            intent=intent,
            confidence=confidence,
            action=action,
            processed_text=processed if processed != text else None,
            duration_ms=round((time.perf_counter() - start) * 1_000, 3),
        )
