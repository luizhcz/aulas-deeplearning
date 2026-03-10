"""Parser para o formato pipe-delimited de ordens de bolsa.

Formato:
    [Ativo|C/V|Quantidade|Preço|Conta|Validade]   ← header opcional
    JURO11|C|140|M|203832|VAC

Campos:
    [0] Ativo     — ticker do ativo
    [1] C/V       — C (compra) ou V (venda)
    [2] Quantidade — número inteiro de cotas/ações
    [3] Preço     — M (mercado), L (limite + valor) ou valor numérico
    [4] Conta     — número da conta
    [5] Validade  — código de validade (VAC, DAY, etc.)
"""

import re

from spacy_intent.domain.entities import Entity, EntityLabel, IntentName
from spacy_intent.domain.parsing import INTENT_SIGNAL_MAP, InputParserPort, ParsedInput

# Padrão para a linha de dados (não o header)
_DATA_PATTERN = re.compile(
    r"^(?P<ticker>[A-Z0-9]{2,12})"
    r"\|(?P<cv>[CV])"
    r"\|(?P<qty>\d+)"
    r"\|(?P<price>[A-Z0-9.,]+)"
    r"\|(?P<account>\d+)"
    r"\|(?P<validity>[A-Z]+)$",
    re.IGNORECASE,
)

# Termos que indicam linha de header — ignorados no parse
_HEADER_TERMS = {"ativo", "c/v", "quantidade", "preço", "conta", "validade"}


class PipeDelimitedParser(InputParserPort):
    """Reconhece e parseia o formato TICKER|C/V|QTY|PRICE|ACCOUNT|VALIDITY."""

    def can_parse(self, text: str) -> bool:
        return bool(_DATA_PATTERN.match(self._data_line(text)))

    def parse(self, text: str) -> ParsedInput:
        m = _DATA_PATTERN.match(self._data_line(text))
        if not m:
            raise ValueError(f"Texto não corresponde ao formato pipe-delimited: {text!r}")

        cv = m.group("cv").upper()
        intent = INTENT_SIGNAL_MAP.get(cv, IntentName.UNKNOWN)

        entities = (
            Entity(label=EntityLabel.TICKER,   value=m.group("ticker").upper()),
            Entity(label=EntityLabel.QUANTITY,  value=m.group("qty")),
            Entity(label=EntityLabel.PRICE,     value=m.group("price").upper()),
            Entity(label=EntityLabel.ACCOUNT,   value=m.group("account")),
            Entity(label=EntityLabel.VALIDITY,  value=m.group("validity").upper()),
        )
        return ParsedInput(intent=intent, confidence=1.0, entities=entities)

    @staticmethod
    def _data_line(text: str) -> str:
        """Retorna a última linha não-vazia, ignorando a linha de header."""
        lines = [ln.strip() for ln in text.strip().splitlines() if ln.strip()]
        if not lines:
            return ""
        # Se a primeira linha parece header, usa a segunda
        first = lines[0].lower()
        if any(term in first for term in _HEADER_TERMS):
            return lines[1] if len(lines) > 1 else ""
        return lines[-1]
