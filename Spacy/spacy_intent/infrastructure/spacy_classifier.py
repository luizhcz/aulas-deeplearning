"""Classificador de intenções baseado em spaCy com cache de modelo thread-safe."""

import threading

import spacy
from spacy.language import Language
from spacy.matcher import Matcher, PhraseMatcher

from spacy_intent.domain.entities import IntentName
from spacy_intent.domain.ports import IntentClassifierPort
from spacy_intent.domain.registry import IntentRegistry
from spacy_intent.exceptions import ModelNotFoundError

# ---------------------------------------------------------------------------
# Cache de modelo — o modelo spaCy é carregado uma única vez por nome.
# O double-checked locking garante thread-safety sem lock em toda leitura.
# ---------------------------------------------------------------------------
_nlp_cache: dict[str, Language] = {}
_cache_lock = threading.Lock()


def _get_cached_model(model_name: str) -> Language:
    if model_name not in _nlp_cache:
        with _cache_lock:
            if model_name not in _nlp_cache:
                try:
                    _nlp_cache[model_name] = spacy.load(model_name)
                except OSError as exc:
                    raise ModelNotFoundError(
                        f"Modelo spaCy '{model_name}' não encontrado. "
                        f"Execute: python -m spacy download {model_name}"
                    ) from exc
    return _nlp_cache[model_name]


class SpacyIntentClassifier(IntentClassifierPort):
    """Classificador com correspondência em dois níveis lidos do IntentRegistry.

    - Nível 1 (alta confiabilidade): PhraseMatcher com frases explícitas.
    - Nível 2 (média confiabilidade): Matcher baseado em lemas de verbos.

    Os matchers são construídos uma vez na inicialização a partir do registry,
    tornando o classify() puramente de leitura e seguro para uso concorrente.
    """

    def __init__(self, model_name: str, registry: IntentRegistry) -> None:
        self._nlp = _get_cached_model(model_name)
        self._registry = registry
        self._phrase_matcher = self._build_phrase_matcher()
        self._lemma_matcher = self._build_lemma_matcher()

    def classify(self, text: str) -> tuple[str, float]:
        doc = self._nlp(text)

        phrase_matches = self._phrase_matcher(doc)
        if phrase_matches:
            name = self._nlp.vocab.strings[phrase_matches[0][0]]
            definition = self._registry.get(name)
            confidence = definition.confidence.phrase if definition else 0.0
            return name, confidence

        lemma_matches = self._lemma_matcher(doc)
        if lemma_matches:
            name = self._nlp.vocab.strings[lemma_matches[0][0]]
            definition = self._registry.get(name)
            confidence = definition.confidence.lemma if definition else 0.0
            return name, confidence

        return IntentName.UNKNOWN, 0.0

    def _build_phrase_matcher(self) -> PhraseMatcher:
        matcher = PhraseMatcher(self._nlp.vocab, attr="LOWER")
        for definition in self._registry.all():
            patterns = [self._nlp.make_doc(p) for p in definition.patterns.phrases]
            matcher.add(definition.name, patterns)
        return matcher

    def _build_lemma_matcher(self) -> Matcher:
        matcher = Matcher(self._nlp.vocab)
        for definition in self._registry.all():
            patterns = [[{"LEMMA": lemma}] for lemma in definition.patterns.lemmas]
            matcher.add(definition.name, patterns)
        return matcher
