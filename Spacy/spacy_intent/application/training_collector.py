"""Coleta de dados de treinamento sem impacto na performance.

O AsyncTrainingDataCollector recebe registros via collect() — operação O(1),
não-bloqueante — e os persiste em background via worker thread daemon.

Fluxo:
  process() → collect() → Queue.put_nowait()  ← crítico (< 1µs)
                                ↓
                        [worker thread]
                                ↓
                       repository.save()       ← I/O Postgres (background)
"""

import logging
import queue
import threading
from typing import Final

from spacy_intent.domain.training import TrainingDataPort, TrainingRecord

_logger = logging.getLogger(__name__)

_SENTINEL: Final = object()  # sinal de encerramento para o worker


class AsyncTrainingDataCollector:
    """Coleta registros de treinamento de forma não-bloqueante.

    - collect() coloca o registro na fila e retorna imediatamente.
    - Um único worker thread daemon consome a fila e persiste no repositório.
    - Se a fila estiver cheia, o registro é descartado silenciosamente —
      nunca bloqueia o thread principal.
    - Erros no repositório são logados, nunca propagados ao caller.
    """

    def __init__(
        self,
        repository: TrainingDataPort,
        max_queue_size: int = 1_000,
    ) -> None:
        self._repository = repository
        self._queue: queue.Queue[TrainingRecord | object] = queue.Queue(
            maxsize=max_queue_size
        )
        self._worker = threading.Thread(
            target=self._run,
            name="spacy-intent-training-worker",
            daemon=True,  # não impede o processo de encerrar
        )
        self._worker.start()

    def collect(self, record: TrainingRecord) -> None:
        """Enfileira o registro de forma não-bloqueante.

        Se a fila estiver cheia, descarta o registro e loga um aviso.
        Nunca lança exceções.
        """
        try:
            self._queue.put_nowait(record)
        except queue.Full:
            _logger.warning(
                "Training queue full — record dropped (intent=%s, confidence=%.2f)",
                record.intent,
                record.confidence,
            )

    def flush(self, timeout: float = 5.0) -> None:
        """Aguarda o processamento de todos os registros pendentes.

        Útil em testes e em graceful shutdown da API.
        """
        join_thread = threading.Thread(target=self._queue.join, daemon=True)
        join_thread.start()
        join_thread.join(timeout=timeout)

    def shutdown(self) -> None:
        """Encerra o worker após processar todos os registros pendentes."""
        self._queue.put(_SENTINEL)
        self._worker.join()

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _run(self) -> None:
        while True:
            item = self._queue.get()
            try:
                if item is _SENTINEL:
                    return
                self._repository.save(item)  # type: ignore[arg-type]
            except Exception:
                _logger.exception("Failed to save training record — record discarded")
            finally:
                self._queue.task_done()
