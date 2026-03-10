"""Testes dos parsers de formatos estruturados.

Cada parser é testado de forma isolada:
  - can_parse() não deve dar falsos positivos ou negativos
  - parse() deve extrair corretamente todas as entidades
  - Inputs ambíguos ou parciais não devem ser detectados como estruturados
"""

import pytest

from spacy_intent.domain.entities import EntityLabel, IntentName
from spacy_intent.infrastructure.parsers.command_style import CommandStyleParser
from spacy_intent.infrastructure.parsers.pipe_delimited import PipeDelimitedParser
from spacy_intent.infrastructure.parsers.space_separated import SpaceSeparatedParser


# ---------------------------------------------------------------------------
# PipeDelimitedParser
# ---------------------------------------------------------------------------
class TestPipeDelimitedParser:
    @pytest.fixture
    def parser(self):
        return PipeDelimitedParser()

    # can_parse
    def test_detects_buy_pipe_format(self, parser):
        assert parser.can_parse("JURO11|C|140|M|203832|VAC") is True

    def test_detects_sell_pipe_format(self, parser):
        assert parser.can_parse("PETR4|V|50|25.50|987654|DAY") is True

    def test_detects_with_header_line(self, parser):
        text = "Ativo|C/V|Quantidade|Preço|Conta|Validade\nJURO11|C|140|M|203832|VAC"
        assert parser.can_parse(text) is True

    def test_rejects_natural_language(self, parser):
        assert parser.can_parse("quero comprar ações da Petrobras") is False

    def test_rejects_command_style(self, parser):
        assert parser.can_parse("472947927942 -V AZIN11") is False

    def test_rejects_partial_pipe(self, parser):
        assert parser.can_parse("PETR4|C") is False

    # parse — intent
    def test_parse_c_maps_to_buy(self, parser):
        result = parser.parse("JURO11|C|140|M|203832|VAC")
        assert result.intent == IntentName.BUY_STOCK

    def test_parse_v_maps_to_sell(self, parser):
        result = parser.parse("PETR4|V|50|25.50|987654|DAY")
        assert result.intent == IntentName.SELL_STOCK

    def test_parse_confidence_is_one(self, parser):
        result = parser.parse("JURO11|C|140|M|203832|VAC")
        assert result.confidence == 1.0

    # parse — entities
    def test_parse_extracts_ticker(self, parser):
        result = parser.parse("JURO11|C|140|M|203832|VAC")
        tickers = [e.value for e in result.entities if e.label == EntityLabel.TICKER]
        assert tickers == ["JURO11"]

    def test_parse_extracts_quantity(self, parser):
        result = parser.parse("JURO11|C|140|M|203832|VAC")
        qtys = [e.value for e in result.entities if e.label == EntityLabel.QUANTITY]
        assert qtys == ["140"]

    def test_parse_extracts_price(self, parser):
        result = parser.parse("JURO11|C|140|M|203832|VAC")
        prices = [e.value for e in result.entities if e.label == EntityLabel.PRICE]
        assert prices == ["M"]

    def test_parse_extracts_account(self, parser):
        result = parser.parse("JURO11|C|140|M|203832|VAC")
        accounts = [e.value for e in result.entities if e.label == EntityLabel.ACCOUNT]
        assert accounts == ["203832"]

    def test_parse_extracts_validity(self, parser):
        result = parser.parse("JURO11|C|140|M|203832|VAC")
        validities = [e.value for e in result.entities if e.label == EntityLabel.VALIDITY]
        assert validities == ["VAC"]

    def test_parse_with_header_returns_correct_data(self, parser):
        text = "Ativo|C/V|Quantidade|Preço|Conta|Validade\nJURO11|C|140|M|203832|VAC"
        result = parser.parse(text)
        assert result.intent == IntentName.BUY_STOCK
        tickers = [e.value for e in result.entities if e.label == EntityLabel.TICKER]
        assert tickers == ["JURO11"]


# ---------------------------------------------------------------------------
# CommandStyleParser
# ---------------------------------------------------------------------------
class TestCommandStyleParser:
    @pytest.fixture
    def parser(self):
        return CommandStyleParser()

    # can_parse
    def test_detects_sell_command(self, parser):
        assert parser.can_parse("472947927942 -V AZIN11") is True

    def test_detects_buy_command(self, parser):
        assert parser.can_parse("123456789 -C PETR4") is True

    def test_rejects_natural_language(self, parser):
        assert parser.can_parse("quero vender minhas ações") is False

    def test_rejects_pipe_format(self, parser):
        assert parser.can_parse("JURO11|C|140|M|203832|VAC") is False

    def test_rejects_short_account(self, parser):
        # conta muito curta — não deveria ser reconhecida
        assert parser.can_parse("123 -V AZIN11") is False

    # parse — intent
    def test_parse_minus_v_maps_to_sell(self, parser):
        result = parser.parse("472947927942 -V AZIN11")
        assert result.intent == IntentName.SELL_STOCK

    def test_parse_minus_c_maps_to_buy(self, parser):
        result = parser.parse("123456789 -C PETR4")
        assert result.intent == IntentName.BUY_STOCK

    def test_parse_confidence_is_one(self, parser):
        result = parser.parse("472947927942 -V AZIN11")
        assert result.confidence == 1.0

    # parse — entities
    def test_parse_extracts_account(self, parser):
        result = parser.parse("472947927942 -V AZIN11")
        accounts = [e.value for e in result.entities if e.label == EntityLabel.ACCOUNT]
        assert accounts == ["472947927942"]

    def test_parse_extracts_ticker(self, parser):
        result = parser.parse("472947927942 -V AZIN11")
        tickers = [e.value for e in result.entities if e.label == EntityLabel.TICKER]
        assert tickers == ["AZIN11"]

    def test_parse_normalizes_ticker_to_uppercase(self, parser):
        result = parser.parse("123456789 -C petr4")
        tickers = [e.value for e in result.entities if e.label == EntityLabel.TICKER]
        assert tickers == ["PETR4"]


# ---------------------------------------------------------------------------
# SpaceSeparatedParser
# ---------------------------------------------------------------------------
class TestSpaceSeparatedParser:
    @pytest.fixture
    def parser(self):
        return SpaceSeparatedParser()

    # can_parse
    def test_detects_sell_space_format(self, parser):
        assert parser.can_parse("ABEV3    SELL    2,50000 BRL, OTD") is True

    def test_detects_buy_space_format(self, parser):
        assert parser.can_parse("PETR4 BUY 25.50 BRL") is True

    def test_rejects_natural_language(self, parser):
        assert parser.can_parse("quero comprar ações da Petrobras") is False

    def test_rejects_pipe_format(self, parser):
        assert parser.can_parse("JURO11|C|140|M|203832|VAC") is False

    def test_rejects_c_v_flags(self, parser):
        # 'C'/'V' não são reconhecidos neste formato — só BUY/SELL
        assert parser.can_parse("ABEV3 C 2,50 BRL") is False

    def test_rejects_without_price_and_currency(self, parser):
        assert parser.can_parse("ABEV3 SELL") is False

    # parse — intent
    def test_parse_sell_maps_to_sell(self, parser):
        result = parser.parse("ABEV3    SELL    2,50000 BRL, OTD")
        assert result.intent == IntentName.SELL_STOCK

    def test_parse_buy_maps_to_buy(self, parser):
        result = parser.parse("PETR4 BUY 25.50 BRL")
        assert result.intent == IntentName.BUY_STOCK

    def test_parse_confidence_is_one(self, parser):
        result = parser.parse("ABEV3 SELL 2,50000 BRL, OTD")
        assert result.confidence == 1.0

    # parse — entities
    def test_parse_extracts_ticker(self, parser):
        result = parser.parse("ABEV3    SELL    2,50000 BRL, OTD")
        tickers = [e.value for e in result.entities if e.label == EntityLabel.TICKER]
        assert tickers == ["ABEV3"]

    def test_parse_extracts_price(self, parser):
        result = parser.parse("ABEV3    SELL    2,50000 BRL, OTD")
        prices = [e.value for e in result.entities if e.label == EntityLabel.PRICE]
        assert prices == ["2,50000"]

    def test_parse_extracts_currency(self, parser):
        result = parser.parse("ABEV3    SELL    2,50000 BRL, OTD")
        currencies = [e.value for e in result.entities if e.label == EntityLabel.CURRENCY]
        assert currencies == ["BRL"]

    def test_parse_extracts_validity_when_present(self, parser):
        result = parser.parse("ABEV3    SELL    2,50000 BRL, OTD")
        validities = [e.value for e in result.entities if e.label == EntityLabel.VALIDITY]
        assert validities == ["OTD"]

    def test_parse_no_validity_when_absent(self, parser):
        result = parser.parse("PETR4 BUY 25.50 BRL")
        validities = [e.value for e in result.entities if e.label == EntityLabel.VALIDITY]
        assert validities == []


# ---------------------------------------------------------------------------
# Testes cruzados: um formato não deve ser detectado pelo parser de outro
# ---------------------------------------------------------------------------
class TestParserIsolation:
    PIPE_INPUT = "JURO11|C|140|M|203832|VAC"
    CMD_INPUT = "472947927942 -V AZIN11"
    SPACE_INPUT = "ABEV3 SELL 2,50000 BRL, OTD"
    NLP_INPUT = "quero comprar ações da Petrobras"

    def test_pipe_parser_rejects_cmd_and_space(self):
        p = PipeDelimitedParser()
        assert not p.can_parse(self.CMD_INPUT)
        assert not p.can_parse(self.SPACE_INPUT)
        assert not p.can_parse(self.NLP_INPUT)

    def test_cmd_parser_rejects_pipe_and_space(self):
        p = CommandStyleParser()
        assert not p.can_parse(self.PIPE_INPUT)
        assert not p.can_parse(self.SPACE_INPUT)
        assert not p.can_parse(self.NLP_INPUT)

    def test_space_parser_rejects_pipe_and_cmd(self):
        p = SpaceSeparatedParser()
        assert not p.can_parse(self.PIPE_INPUT)
        assert not p.can_parse(self.CMD_INPUT)
        assert not p.can_parse(self.NLP_INPUT)
