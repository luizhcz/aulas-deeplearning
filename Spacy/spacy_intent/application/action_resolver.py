from spacy_intent.domain.entities import Action, IntentName
from spacy_intent.domain.ports import ActionResolverPort
from spacy_intent.domain.registry import IntentRegistry

_LOW_CONFIDENCE_ACTION = Action(
    type="NO_ACTION",
    description="Confiabilidade insuficiente para executar a ação",
)

_UNKNOWN_ACTION = Action(
    type="NO_ACTION",
    description="Intenção não reconhecida, nenhuma ação executada",
)


class ConfidenceBasedActionResolver(ActionResolverPort):
    """Resolve a ação consultando o registry se a confiabilidade atingir o limiar."""

    def __init__(self, registry: IntentRegistry, min_confidence: float) -> None:
        self._registry = registry
        self._min_confidence = min_confidence

    def resolve(self, intent_name: str, confidence: float) -> Action:
        if confidence < self._min_confidence:
            return _LOW_CONFIDENCE_ACTION

        if intent_name == IntentName.UNKNOWN:
            return _UNKNOWN_ACTION

        definition = self._registry.get(intent_name)
        if definition is None:
            return _UNKNOWN_ACTION

        return definition.action
