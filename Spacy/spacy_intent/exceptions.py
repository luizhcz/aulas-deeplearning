"""Exceções customizadas da biblioteca spacy-intent."""


class SpacyIntentError(Exception):
    """Exceção base da biblioteca."""


class InvalidInputError(SpacyIntentError, ValueError):
    """Levantada quando o texto de entrada é inválido."""


class ModelNotFoundError(SpacyIntentError, RuntimeError):
    """Levantada quando o modelo spaCy não está instalado."""


class ConfigurationError(SpacyIntentError, ValueError):
    """Levantada quando a configuração é inválida ou malformada."""
