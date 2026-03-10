from abc import ABC, abstractmethod

from spacy_intent.domain.entities import Action


class IntentClassifierPort(ABC):
    @abstractmethod
    def classify(self, text: str) -> tuple[str, float]:
        """Classifica o texto em uma intenção com score de confiabilidade.

        Returns:
            Tuple de (intent_name, confidence) onde confidence é de 0.0 a 1.0.
        """
        ...


class ActionResolverPort(ABC):
    @abstractmethod
    def resolve(self, intent_name: str, confidence: float) -> Action:
        """Resolve a ação com base no nome da intenção e na confiabilidade."""
        ...
