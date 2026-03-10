from dataclasses import dataclass, field

from spacy_intent.domain.entities import Action


@dataclass(frozen=True)
class IntentPatterns:
    phrases: tuple[str, ...]
    lemmas: tuple[str, ...]


@dataclass(frozen=True)
class IntentConfidence:
    phrase: float
    lemma: float


@dataclass(frozen=True)
class IntentDefinition:
    """Define uma intenção com seus padrões, confiabilidades e ação associada."""

    name: str
    action: Action
    patterns: IntentPatterns
    confidence: IntentConfidence


class IntentRegistry:
    """Repositório de intenções disponíveis para classificação.

    Permite registrar e recuperar definições de intenções dinamicamente,
    sem acoplamento ao core da biblioteca.
    """

    def __init__(self) -> None:
        self._intents: dict[str, IntentDefinition] = {}

    def register(self, definition: IntentDefinition) -> None:
        self._intents[definition.name] = definition

    def get(self, name: str) -> IntentDefinition | None:
        return self._intents.get(name)

    def all(self) -> list[IntentDefinition]:
        return list(self._intents.values())

    def names(self) -> list[str]:
        return list(self._intents.keys())

    def __len__(self) -> int:
        return len(self._intents)
