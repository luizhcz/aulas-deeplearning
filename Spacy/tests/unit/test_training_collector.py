"""Testes do AsyncTrainingDataCollector.

Verificações críticas:
  - collect() é não-bloqueante mesmo com repositório lento
  - registros são entregues ao repositório em background
  - fila cheia descarta silenciosamente, sem bloquear
  - erros no repositório não propagam ao caller
"""

import time
import threading
from datetime import datetime, timezone
from unittest.mock import MagicMock, call

import pytest

from spacy_intent.application.training_collector import AsyncTrainingDataCollector
from spacy_intent.domain.training import TrainingRecord


def _make_record(intent: str = "buy_stock", confidence: float = 0.92) -> TrainingRecord:
    return TrainingRecord(
        text="quero comprar",
        processed_text="quero comprar",
        intent=intent,
        confidence=confidence,
        classified_at=datetime.now(timezone.utc),
    )


class TestNonBlocking:
    def test_collect_returns_immediately_with_slow_repository(self):
        """collect() não pode bloquear mesmo que o repositório demore."""

        class SlowRepository:
            def save(self, record: TrainingRecord) -> None:
                time.sleep(0.5)  # simula I/O lento

        collector = AsyncTrainingDataCollector(SlowRepository(), max_queue_size=10)
        start = time.monotonic()
        collector.collect(_make_record())
        elapsed = time.monotonic() - start

        assert elapsed < 0.05, f"collect() bloqueou por {elapsed:.3f}s"

    def test_collect_does_not_raise_on_full_queue(self):
        """Fila cheia deve descartar silenciosamente, nunca levantar exceção."""
        blocking_event = threading.Event()

        class BlockingRepository:
            def save(self, record: TrainingRecord) -> None:
                blocking_event.wait()  # trava o worker para encher a fila

        collector = AsyncTrainingDataCollector(BlockingRepository(), max_queue_size=2)

        # Enche a fila além da capacidade — nenhuma chamada deve lançar
        for _ in range(10):
            collector.collect(_make_record())  # não deve lançar

        blocking_event.set()  # libera o worker


class TestDelivery:
    def test_record_is_eventually_saved_to_repository(self):
        """O registro deve chegar ao repositório após o worker processá-lo."""
        mock_repo = MagicMock()
        collector = AsyncTrainingDataCollector(mock_repo, max_queue_size=10)
        record = _make_record()

        collector.collect(record)
        collector.flush(timeout=2.0)

        mock_repo.save.assert_called_once_with(record)

    def test_multiple_records_are_all_delivered(self):
        mock_repo = MagicMock()
        collector = AsyncTrainingDataCollector(mock_repo, max_queue_size=100)
        records = [_make_record(intent=f"intent_{i}") for i in range(10)]

        for record in records:
            collector.collect(record)

        collector.flush(timeout=2.0)

        assert mock_repo.save.call_count == 10

    def test_records_delivered_in_order(self):
        """Registros devem ser entregues na ordem em que foram enfileirados."""
        saved: list[TrainingRecord] = []

        class OrderCapturingRepository:
            def save(self, record: TrainingRecord) -> None:
                saved.append(record)

        collector = AsyncTrainingDataCollector(
            OrderCapturingRepository(), max_queue_size=50
        )
        records = [_make_record(intent=f"intent_{i}") for i in range(5)]

        for record in records:
            collector.collect(record)

        collector.flush(timeout=2.0)

        assert saved == records


class TestErrorIsolation:
    def test_repository_error_does_not_propagate_to_caller(self):
        """Erro no repositório deve ser absorvido, não propagar."""

        class FailingRepository:
            def save(self, record: TrainingRecord) -> None:
                raise RuntimeError("Postgres connection lost")

        collector = AsyncTrainingDataCollector(FailingRepository(), max_queue_size=10)

        # Não deve lançar exceção
        collector.collect(_make_record())
        collector.flush(timeout=2.0)

    def test_worker_continues_after_repository_error(self):
        """Worker deve continuar processando após falha em um registro."""
        saved: list[TrainingRecord] = []
        call_count = 0

        class FlakyRepository:
            def save(self, record: TrainingRecord) -> None:
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    raise RuntimeError("falha temporária")
                saved.append(record)

        collector = AsyncTrainingDataCollector(FlakyRepository(), max_queue_size=10)
        collector.collect(_make_record(intent="primeiro"))   # vai falhar
        collector.collect(_make_record(intent="segundo"))    # deve ser salvo
        collector.flush(timeout=2.0)

        assert len(saved) == 1
        assert saved[0].intent == "segundo"


class TestShutdown:
    def test_flush_waits_for_pending_records(self):
        """flush() deve aguardar o processamento de todos os registros."""
        processed: list[TrainingRecord] = []

        class SlowRepository:
            def save(self, record: TrainingRecord) -> None:
                time.sleep(0.05)
                processed.append(record)

        collector = AsyncTrainingDataCollector(SlowRepository(), max_queue_size=20)
        for _ in range(5):
            collector.collect(_make_record())

        collector.flush(timeout=3.0)
        assert len(processed) == 5
