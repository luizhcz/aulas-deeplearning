"""Contratos de domínio para parsing de inputs estruturados."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from spacy_intent.domain.entities import Entity, IntentName

# Mapeamento de sinais de intenção usados nos diferentes formatos de input.
# Centralizado aqui para que todos os parsers usem a mesma lógica de domínio.
INTENT_SIGNAL_MAP: dict[str, str] = {
    "C": IntentName.BUY_STOCK,
    "COMPRA": IntentName.BUY_STOCK,
    "BUY": IntentName.BUY_STOCK,
    "V": IntentName.SELL_STOCK,
    "VENDA": IntentName.SELL_STOCK,
    "SELL": IntentName.SELL_STOCK,
}


@dataclass(frozen=True)
class ParsedInput:
    """Resultado de um parser estruturado, antes da resolução de ação."""

    intent: str
    confidence: float
    entities: tuple[Entity, ...]


class InputParserPort(ABC):
    """Interface para parsers de formatos estruturados de input.

    Cada implementação reconhece e extrai dados de um formato específico.
    O método can_parse() deve ser rápido (O(1) via regex) — é chamado
    para todos os parsers antes de qualquer processamento.
    """

    @abstractmethod
    def can_parse(self, text: str) -> bool:
        """Retorna True se este parser reconhece o formato do texto."""
        ...

    @abstractmethod
    def parse(self, text: str) -> ParsedInput:
        """Extrai intenção e entidades do texto estruturado."""
        ...
