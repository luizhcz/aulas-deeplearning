"""Parser para o formato command-style com flag de direção.

Formato:
    ACCOUNT -C TICKER    (compra)
    ACCOUNT -V TICKER    (venda)

Exemplo:
    472947927942 -V AZIN11
"""

import re

from spacy_intent.domain.entities import Entity, EntityLabel, IntentName
from spacy_intent.domain.parsing import INTENT_SIGNAL_MAP, InputParserPort, ParsedInput

_PATTERN = re.compile(
    r"^(?P<account>\d{6,})"       # conta: 6+ dígitos
    r"\s+-(?P<flag>[CV])"          # flag: -C ou -V
    r"\s+(?P<ticker>[A-Z0-9]{3,12})$",  # ticker: 3-12 chars
    re.IGNORECASE,
)


class CommandStyleParser(InputParserPort):
    """Reconhece e parseia o formato ACCOUNT -C/-V TICKER."""

    def can_parse(self, text: str) -> bool:
        return bool(_PATTERN.match(text.strip()))

    def parse(self, text: str) -> ParsedInput:
        m = _PATTERN.match(text.strip())
        if not m:
            raise ValueError(f"Texto não corresponde ao formato command-style: {text!r}")

        flag = m.group("flag").upper()
        intent = INTENT_SIGNAL_MAP.get(flag, IntentName.UNKNOWN)

        entities = (
            Entity(label=EntityLabel.ACCOUNT, value=m.group("account")),
            Entity(label=EntityLabel.TICKER,  value=m.group("ticker").upper()),
        )
        return ParsedInput(intent=intent, confidence=1.0, entities=entities)
