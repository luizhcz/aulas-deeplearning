"""Parser para o formato space-separated com palavras-chave BUY/SELL.

Formato:
    TICKER  BUY|SELL  PRICE  CURRENCY[, VALIDITY]

Exemplo:
    ABEV3    SELL    2,50000 BRL, OTD
"""

import re

from spacy_intent.domain.entities import Entity, EntityLabel, IntentName
from spacy_intent.domain.parsing import INTENT_SIGNAL_MAP, InputParserPort, ParsedInput

_PATTERN = re.compile(
    r"^(?P<ticker>[A-Z0-9]{3,12})"      # ticker
    r"\s+(?P<intent>BUY|SELL)"          # direção — apenas keywords explícitas
    r"\s+(?P<price>[\d,.]+)"            # preço (ex.: 2,50000 ou 25.50)
    r"\s+(?P<currency>[A-Z]{3})"        # moeda ISO 4217 (BRL, USD...)
    r"(?:[,\s]+(?P<validity>[A-Z]{2,5}))?$",  # validade opcional (OTD, DAY...)
    re.IGNORECASE,
)


class SpaceSeparatedParser(InputParserPort):
    """Reconhece e parseia o formato TICKER BUY/SELL PRICE CURRENCY [VALIDITY]."""

    def can_parse(self, text: str) -> bool:
        return bool(_PATTERN.match(text.strip()))

    def parse(self, text: str) -> ParsedInput:
        m = _PATTERN.match(text.strip())
        if not m:
            raise ValueError(f"Texto não corresponde ao formato space-separated: {text!r}")

        intent_str = m.group("intent").upper()
        intent = INTENT_SIGNAL_MAP.get(intent_str, IntentName.UNKNOWN)

        entities: list[Entity] = [
            Entity(label=EntityLabel.TICKER,   value=m.group("ticker").upper()),
            Entity(label=EntityLabel.PRICE,    value=m.group("price")),
            Entity(label=EntityLabel.CURRENCY, value=m.group("currency").upper()),
        ]
        if m.group("validity"):
            entities.append(
                Entity(label=EntityLabel.VALIDITY, value=m.group("validity").upper())
            )

        return ParsedInput(intent=intent, confidence=1.0, entities=tuple(entities))
