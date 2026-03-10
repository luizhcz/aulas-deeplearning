"""Repositório Postgres para dados de treinamento.

Usa connection pool thread-safe (psycopg2.ThreadedConnectionPool) porque
o worker do AsyncTrainingDataCollector roda em thread separada.

Instalação:
    pip install "spacy-intent[postgres]"
    # ou: pip install psycopg2-binary
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from spacy_intent.domain.training import TrainingDataPort, TrainingRecord
from spacy_intent.exceptions import ConfigurationError

if TYPE_CHECKING:
    import psycopg2.pool

_logger = logging.getLogger(__name__)

_INSERT_SQL = """
    INSERT INTO intent_training_records
        (text, processed_text, intent, confidence, classified_at)
    VALUES
        (%(text)s, %(processed_text)s, %(intent)s, %(confidence)s, %(classified_at)s)
"""


class PostgresTrainingDataRepository(TrainingDataPort):
    """Persiste registros de treinamento em Postgres via connection pool.

    Args:
        dsn:       String de conexão Postgres.
                   Exemplo: postgresql://user:pass@localhost:5432/mydb
        pool_size: Número máximo de conexões no pool (default: 2 — suficiente
                   para um único worker thread com folga).
    """

    def __init__(self, dsn: str, pool_size: int = 2) -> None:
        self._pool = self._create_pool(dsn, pool_size)

    def save(self, record: TrainingRecord) -> None:
        conn = self._pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    _INSERT_SQL,
                    {
                        "text": record.text,
                        "processed_text": record.processed_text,
                        "intent": record.intent,
                        "confidence": record.confidence,
                        "classified_at": record.classified_at,
                    },
                )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            self._pool.putconn(conn)

    @staticmethod
    def _create_pool(dsn: str, pool_size: int) -> "psycopg2.pool.ThreadedConnectionPool":
        try:
            import psycopg2.pool
        except ImportError as exc:
            raise ConfigurationError(
                "psycopg2 não encontrado. "
                'Instale com: pip install "spacy-intent[postgres]" ou pip install psycopg2-binary'
            ) from exc

        try:
            return psycopg2.pool.ThreadedConnectionPool(1, pool_size, dsn)
        except Exception as exc:
            raise ConfigurationError(
                f"Não foi possível conectar ao Postgres: {exc}"
            ) from exc
