"""Carregamento de configuração a partir de arquivos YAML."""

import os
from dataclasses import dataclass
from pathlib import Path

import yaml

from spacy_intent.domain.entities import Action
from spacy_intent.domain.registry import (
    IntentConfidence,
    IntentDefinition,
    IntentPatterns,
    IntentRegistry,
)
from spacy_intent.exceptions import ConfigurationError


@dataclass(frozen=True)
class TrainingConfig:
    """Configuração da coleta de dados de treinamento.

    A database_url é resolvida na seguinte ordem:
      1. Campo database_url no YAML
      2. Variável de ambiente SPACY_INTENT_DATABASE_URL
      3. Variável de ambiente DATABASE_URL
    """

    enabled: bool
    database_url: str | None
    queue_size: int
    pool_size: int


@dataclass(frozen=True)
class LibraryConfig:
    """Configuração completa carregada do YAML."""

    spacy_model: str
    registry: IntentRegistry
    min_confidence: float
    preprocessing_steps: tuple[str, ...]
    training: TrainingConfig


class ConfigLoader:
    """Carrega e valida um arquivo YAML, retornando um LibraryConfig."""

    @staticmethod
    def load(path: str | Path) -> LibraryConfig:
        resolved = Path(path)
        if not resolved.exists():
            raise ConfigurationError(f"Arquivo de configuração não encontrado: {resolved}")

        try:
            with resolved.open(encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as exc:
            raise ConfigurationError(f"Erro ao parsear YAML: {exc}") from exc

        if not isinstance(data, dict):
            raise ConfigurationError("O arquivo de configuração deve ser um mapeamento YAML")

        return ConfigLoader._build(data)

    @staticmethod
    def _build(data: dict) -> LibraryConfig:
        registry = IntentRegistry()

        for raw in data.get("intents", []):
            try:
                definition = IntentDefinition(
                    name=raw["name"],
                    action=Action(
                        type=raw["action"]["type"],
                        description=raw["action"]["description"],
                    ),
                    patterns=IntentPatterns(
                        phrases=tuple(raw["patterns"]["phrases"]),
                        lemmas=tuple(raw["patterns"]["lemmas"]),
                    ),
                    confidence=IntentConfidence(
                        phrase=float(raw["confidence"]["phrase"]),
                        lemma=float(raw["confidence"]["lemma"]),
                    ),
                )
            except (KeyError, TypeError) as exc:
                raise ConfigurationError(
                    f"Intenção mal configurada — campo ausente: {exc}"
                ) from exc

            registry.register(definition)

        thresholds = data.get("thresholds", {})
        preprocessing = data.get("preprocessing", {})
        training_raw = data.get("training", {})

        return LibraryConfig(
            spacy_model=data.get("spacy_model", "pt_core_news_sm"),
            registry=registry,
            min_confidence=float(thresholds.get("min_action_confidence", 0.70)),
            preprocessing_steps=tuple(preprocessing.get("steps", [])),
            training=ConfigLoader._build_training(training_raw),
        )

    @staticmethod
    def _build_training(raw: dict) -> TrainingConfig:
        enabled = bool(raw.get("enabled", False))

        db_url = (
            raw.get("database_url")
            or os.getenv("SPACY_INTENT_DATABASE_URL")
            or os.getenv("DATABASE_URL")
        )

        if enabled and not db_url:
            raise ConfigurationError(
                "training.enabled=true mas nenhuma database_url foi configurada. "
                "Defina training.database_url no YAML ou a variável "
                "SPACY_INTENT_DATABASE_URL / DATABASE_URL."
            )

        return TrainingConfig(
            enabled=enabled,
            database_url=db_url or None,
            queue_size=int(raw.get("queue_size", 1_000)),
            pool_size=int(raw.get("pool_size", 2)),
        )
