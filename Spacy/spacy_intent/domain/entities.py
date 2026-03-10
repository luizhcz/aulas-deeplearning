from dataclasses import dataclass


class IntentName:
    """Constantes para os nomes de intenção padrão da biblioteca."""

    BUY_STOCK = "buy_stock"
    SELL_STOCK = "sell_stock"
    UNKNOWN = "unknown"


class EntityLabel:
    """Labels padrão para entidades extraídas do input."""

    TICKER = "TICKER"
    QUANTITY = "QUANTITY"
    PRICE = "PRICE"
    ACCOUNT = "ACCOUNT"
    VALIDITY = "VALIDITY"
    CURRENCY = "CURRENCY"


@dataclass(frozen=True)
class Entity:
    """Entidade extraída do input estruturado.

    Attributes:
        label: Categoria da entidade (ex.: EntityLabel.TICKER).
        value: Valor bruto extraído (ex.: "PETR4", "100", "M").
    """

    label: str
    value: str


@dataclass(frozen=True)
class Action:
    type: str
    description: str


@dataclass(frozen=True)
class IntentResult:
    """Resultado completo de uma classificação de intenção.

    Attributes:
        text:           Texto original recebido.
        intent:         Nome da intenção (ex.: "buy_stock").
        confidence:     Score de confiabilidade de 0.0 a 1.0.
                        Inputs estruturados retornam 1.0 (sem ambiguidade).
        action:         Ação resolvida com base na intenção e confiabilidade.
        entities:       Entidades extraídas (ticker, qty, preço, conta, validade).
                        Preenchido por parsers estruturados; vazio para NLP.
        processed_text: Texto normalizado enviado ao classificador NLP.
                        None para inputs estruturados (não passam por NLP).
    """

    text: str
    intent: str
    confidence: float
    action: Action
    entities: tuple[Entity, ...] = ()
    processed_text: str | None = None
    duration_ms: float = 0.0
