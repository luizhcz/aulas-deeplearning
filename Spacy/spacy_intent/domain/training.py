"""Contratos de domínio para coleta de dados de treinamento ML."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone

from spacy_intent.domain.entities import IntentResult


@dataclass(frozen=True)
class TrainingRecord:
    """Registro de uma classificação, pronto para ser usado como dado de treino ML.

    Attributes:
        text:           Texto original recebido pelo engine.
        processed_text: Texto após o pipeline de pré-processamento (o que o modelo viu).
        intent:         Intenção classificada (label de treino).
        confidence:     Score de confiabilidade (útil para filtrar amostras de baixa qualidade).
        classified_at:  Momento da classificação (UTC).
    """

    text: str
    processed_text: str
    intent: str
    confidence: float
    classified_at: datetime

    @classmethod
    def from_result(cls, result: IntentResult) -> "TrainingRecord":
        return cls(
            text=result.text,
            processed_text=result.processed_text or result.text,
            intent=result.intent,
            confidence=result.confidence,
            classified_at=datetime.now(timezone.utc),
        )


class TrainingDataPort(ABC):
    """Interface para persistência de dados de treinamento.

    Implementações concretas (Postgres, arquivo, etc.) vivem na camada
    de infraestrutura e são injetadas via configuração.
    """

    @abstractmethod
    def save(self, record: TrainingRecord) -> None:
        """Persiste um registro de treinamento. Chamado em thread separada."""
        ...
