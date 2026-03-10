import pytest

from spacy_intent.application.preprocessing import (
    CollapseWhitespacePreprocessor,
    NormalizeUnicodePreprocessor,
    PreprocessingPipeline,
    StripWhitespacePreprocessor,
)
from spacy_intent.exceptions import ConfigurationError


class TestStripWhitespace:
    def test_removes_leading_spaces(self):
        assert StripWhitespacePreprocessor().process("  texto") == "texto"

    def test_removes_trailing_spaces(self):
        assert StripWhitespacePreprocessor().process("texto  ") == "texto"

    def test_removes_newlines(self):
        assert StripWhitespacePreprocessor().process("\ntexto\n") == "texto"

    def test_preserves_internal_spaces(self):
        assert StripWhitespacePreprocessor().process("  a b  ") == "a b"


class TestNormalizeUnicode:
    def test_nfc_normalization(self):
        # Cria string com decomposição NFD (a + combining accent)
        nfd = "a\u0301c\u0327a\u0303o"  # ação em NFD
        result = NormalizeUnicodePreprocessor().process(nfd)
        assert result == "ação"

    def test_already_normalized_unchanged(self):
        text = "quero comprar ações"
        assert NormalizeUnicodePreprocessor().process(text) == text


class TestCollapseWhitespace:
    def test_collapses_multiple_spaces(self):
        assert CollapseWhitespacePreprocessor().process("a  b   c") == "a b c"

    def test_collapses_tabs(self):
        assert CollapseWhitespacePreprocessor().process("a\t\tb") == "a b"

    def test_collapses_mixed_whitespace(self):
        assert CollapseWhitespacePreprocessor().process("a  \t  b") == "a b"


class TestPreprocessingPipeline:
    def test_runs_steps_in_order(self):
        pipeline = PreprocessingPipeline.from_names(
            ["strip_whitespace", "collapse_whitespace"]
        )
        result = pipeline.run("  quero  comprar  ")
        assert result == "quero comprar"

    def test_empty_pipeline_returns_text_unchanged(self):
        pipeline = PreprocessingPipeline(steps=[])
        assert pipeline.run("texto qualquer") == "texto qualquer"

    def test_unknown_step_raises_configuration_error(self):
        with pytest.raises(ConfigurationError, match="Preprocessador desconhecido"):
            PreprocessingPipeline.from_names(["inexistente"])

    def test_from_names_with_valid_steps(self):
        pipeline = PreprocessingPipeline.from_names(
            ["strip_whitespace", "normalize_unicode", "collapse_whitespace"]
        )
        assert pipeline.run("  ação  ") == "ação"
