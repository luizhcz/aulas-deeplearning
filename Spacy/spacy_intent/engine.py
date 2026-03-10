import os
from pathlib import Path

from spacy_intent.application.action_resolver import ConfidenceBasedActionResolver
from spacy_intent.application.preprocessing import PreprocessingPipeline
from spacy_intent.application.training_collector import AsyncTrainingDataCollector
from spacy_intent.application.use_cases import ClassifyIntentUseCase
from spacy_intent.domain.entities import IntentResult
from spacy_intent.domain.parsing import InputParserPort
from spacy_intent.domain.ports import ActionResolverPort, IntentClassifierPort
from spacy_intent.domain.training import TrainingDataPort, TrainingRecord
from spacy_intent.infrastructure.config_loader import ConfigLoader
from spacy_intent.infrastructure.parsers.command_style import CommandStyleParser
from spacy_intent.infrastructure.parsers.pipe_delimited import PipeDelimitedParser
from spacy_intent.infrastructure.parsers.space_separated import SpaceSeparatedParser
from spacy_intent.infrastructure.spacy_classifier import SpacyIntentClassifier

# Parsers estruturados instanciados uma única vez — são stateless.
# A ordem importa: mais específico primeiro.
_DEFAULT_STRUCTURED_PARSERS: list[InputParserPort] = [
    PipeDelimitedParser(),    # TICKER|C/V|QTY|PRICE|ACCOUNT|VALIDITY
    CommandStyleParser(),     # ACCOUNT -C/-V TICKER
    SpaceSeparatedParser(),   # TICKER BUY/SELL PRICE CURRENCY [VALIDITY]
]


def _default_config_path() -> Path:
    env = os.getenv("SPACY_INTENT_CONFIG")
    if env:
        return Path(env)
    return Path(__file__).parent / "config" / "intents.yml"


class IntentEngine:
    """Ponto de entrada público da biblioteca.

    O modo recomendado é via from_config()::

        engine = IntentEngine.from_config()

        # Input estruturado (bypassa spaCy, confidence=1.0)
        result = engine.process("PETR4|C|100|M|203832|VAC")
        result.intent           # "buy_stock"
        result.confidence       # 1.0
        result.entities         # (Entity(TICKER, PETR4), Entity(QUANTITY, 100), ...)

        # Linguagem natural (usa spaCy)
        result = engine.process("quero comprar ações da Petrobras")
        result.intent           # "buy_stock"
        result.confidence       # 0.92
        result.entities         # ()

    Para injetar implementações customizadas (ex.: testes)::

        engine = IntentEngine(classifier=stub, resolver=stub)
    """

    def __init__(
        self,
        classifier: IntentClassifierPort,
        resolver: ActionResolverPort,
        preprocessor: PreprocessingPipeline | None = None,
        training_collector: AsyncTrainingDataCollector | None = None,
        structured_parsers: list[InputParserPort] | None = None,
    ) -> None:
        _preprocessor = preprocessor or PreprocessingPipeline(steps=[])
        _parsers = structured_parsers if structured_parsers is not None else _DEFAULT_STRUCTURED_PARSERS
        self._use_case = ClassifyIntentUseCase(classifier, resolver, _preprocessor, _parsers)
        # Guardados para reutilização em with_training()
        self._classifier = classifier
        self._resolver = resolver
        self._preprocessor = _preprocessor
        self._structured_parsers = _parsers
        # None = training desabilitado; process() faz um único check O(1)
        self._training_collector = training_collector

    @classmethod
    def from_config(cls, config_path: str | Path | None = None) -> "IntentEngine":
        """Cria o engine a partir de um arquivo YAML.

        Args:
            config_path: Caminho para o YAML. Se None, usa SPACY_INTENT_CONFIG
                         ou o arquivo bundled com a biblioteca.
        """
        config = ConfigLoader.load(config_path or _default_config_path())
        classifier = SpacyIntentClassifier(config.spacy_model, config.registry)
        resolver = ConfidenceBasedActionResolver(config.registry, config.min_confidence)
        preprocessor = PreprocessingPipeline.from_names(list(config.preprocessing_steps))

        training_collector = None
        if config.training.enabled:
            from spacy_intent.infrastructure.postgres_repository import (
                PostgresTrainingDataRepository,
            )
            repository = PostgresTrainingDataRepository(
                dsn=config.training.database_url,  # type: ignore[arg-type]
                pool_size=config.training.pool_size,
            )
            training_collector = AsyncTrainingDataCollector(
                repository=repository,
                max_queue_size=config.training.queue_size,
            )

        return cls(classifier, resolver, preprocessor, training_collector)

    def process(self, text: str) -> IntentResult:
        """Processa um input e retorna a intenção classificada com a ação.

        Inputs estruturados (pipe-delimited, command-style, space-separated)
        são identificados por regex e parseados sem chamar o spaCy.
        Linguagem natural passa pelo pipeline NLP completo.

        Args:
            text: Input do usuário (qualquer formato suportado).

        Returns:
            IntentResult com intent, confidence, action, entities e texto original.

        Raises:
            InvalidInputError: Se o texto for vazio, None ou exceder 1000 caracteres.
        """
        result = self._use_case.execute(text)

        if self._training_collector is not None:
            self._training_collector.collect(TrainingRecord.from_result(result))

        return result

    def with_training(
        self,
        repository: TrainingDataPort,
        queue_size: int = 1_000,
    ) -> "IntentEngine":
        """Retorna nova instância com coleta de treinamento habilitada."""
        collector = AsyncTrainingDataCollector(repository, max_queue_size=queue_size)
        return IntentEngine(
            classifier=self._classifier,
            resolver=self._resolver,
            preprocessor=self._preprocessor,
            training_collector=collector,
            structured_parsers=self._structured_parsers,
        )
