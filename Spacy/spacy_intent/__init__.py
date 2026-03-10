"""spacy-intent: classificador de intenções em português usando spaCy."""

from spacy_intent.domain.entities import Action, Entity, EntityLabel, IntentName, IntentResult
from spacy_intent.domain.parsing import InputParserPort, ParsedInput
from spacy_intent.domain.training import TrainingDataPort, TrainingRecord
from spacy_intent.engine import IntentEngine
from spacy_intent.exceptions import (
    ConfigurationError,
    InvalidInputError,
    ModelNotFoundError,
    SpacyIntentError,
)

__all__ = [
    # API pública principal
    "IntentEngine",
    "IntentResult",
    "IntentName",
    "Action",
    # Entidades extraídas de inputs estruturados
    "Entity",
    "EntityLabel",
    "InputParserPort",
    "ParsedInput",
    # Treinamento ML
    "TrainingRecord",
    "TrainingDataPort",
    # Exceções
    "SpacyIntentError",
    "InvalidInputError",
    "ModelNotFoundError",
    "ConfigurationError",
]
