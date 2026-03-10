"""Pipeline de pré-processamento de texto.

Cada etapa implementa TextPreprocessorPort e pode ser composta livremente.
Novas etapas são registradas em _PREPROCESSOR_REGISTRY sem alterar o core.
"""

import unicodedata
from abc import ABC, abstractmethod

from spacy_intent.exceptions import ConfigurationError


class TextPreprocessorPort(ABC):
    @abstractmethod
    def process(self, text: str) -> str:
        ...


class StripWhitespacePreprocessor(TextPreprocessorPort):
    """Remove espaços e quebras de linha nas bordas."""

    def process(self, text: str) -> str:
        return text.strip()


class NormalizeUnicodePreprocessor(TextPreprocessorPort):
    """Normaliza Unicode para NFC — garante representação consistente de acentos."""

    def process(self, text: str) -> str:
        return unicodedata.normalize("NFC", text)


class CollapseWhitespacePreprocessor(TextPreprocessorPort):
    """Colapsa sequências de espaços internos em um único espaço."""

    def process(self, text: str) -> str:
        return " ".join(text.split())


_PREPROCESSOR_REGISTRY: dict[str, type[TextPreprocessorPort]] = {
    "strip_whitespace": StripWhitespacePreprocessor,
    "normalize_unicode": NormalizeUnicodePreprocessor,
    "collapse_whitespace": CollapseWhitespacePreprocessor,
}


class PreprocessingPipeline:
    """Executa uma sequência ordenada de preprocessadores no texto."""

    def __init__(self, steps: list[TextPreprocessorPort]) -> None:
        self._steps = steps

    @classmethod
    def from_names(cls, step_names: list[str]) -> "PreprocessingPipeline":
        """Constrói o pipeline a partir de nomes registrados em _PREPROCESSOR_REGISTRY."""
        steps: list[TextPreprocessorPort] = []
        for name in step_names:
            if name not in _PREPROCESSOR_REGISTRY:
                raise ConfigurationError(
                    f"Preprocessador desconhecido: '{name}'. "
                    f"Disponíveis: {sorted(_PREPROCESSOR_REGISTRY)}"
                )
            steps.append(_PREPROCESSOR_REGISTRY[name]())
        return cls(steps)

    def run(self, text: str) -> str:
        result = text
        for step in self._steps:
            result = step.process(result)
        return result
