from pathlib import Path

import pytest

from spacy_intent.domain.entities import IntentName
from spacy_intent.exceptions import ConfigurationError
from spacy_intent.infrastructure.config_loader import ConfigLoader

_FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(autouse=True)
def create_fixtures_dir(tmp_path):
    """Fornece diretório temporário para YAML de teste."""
    return tmp_path


def _write_yaml(path: Path, content: str) -> Path:
    config = path / "config.yml"
    config.write_text(content, encoding="utf-8")
    return config


class TestValidConfig:
    def test_loads_spacy_model(self, tmp_path):
        config_file = _write_yaml(tmp_path, """
spacy_model: pt_core_news_sm
intents: []
""")
        config = ConfigLoader.load(config_file)
        assert config.spacy_model == "pt_core_news_sm"

    def test_loads_min_confidence(self, tmp_path):
        config_file = _write_yaml(tmp_path, """
spacy_model: pt_core_news_sm
thresholds:
  min_action_confidence: 0.80
intents: []
""")
        config = ConfigLoader.load(config_file)
        assert config.min_confidence == 0.80

    def test_loads_preprocessing_steps(self, tmp_path):
        config_file = _write_yaml(tmp_path, """
spacy_model: pt_core_news_sm
preprocessing:
  steps:
    - strip_whitespace
    - normalize_unicode
intents: []
""")
        config = ConfigLoader.load(config_file)
        assert "strip_whitespace" in config.preprocessing_steps
        assert "normalize_unicode" in config.preprocessing_steps

    def test_loads_intent_buy_stock(self, tmp_path):
        config_file = _write_yaml(tmp_path, """
spacy_model: pt_core_news_sm
intents:
  - name: buy_stock
    action:
      type: BUY_STOCK
      description: "Comprar ação"
    confidence:
      phrase: 0.92
      lemma: 0.75
    patterns:
      phrases:
        - "quero comprar"
      lemmas:
        - comprar
""")
        config = ConfigLoader.load(config_file)
        assert len(config.registry) == 1
        definition = config.registry.get(IntentName.BUY_STOCK)
        assert definition is not None
        assert definition.action.type == "BUY_STOCK"
        assert "quero comprar" in definition.patterns.phrases
        assert "comprar" in definition.patterns.lemmas
        assert definition.confidence.phrase == 0.92

    def test_defaults_when_optional_keys_absent(self, tmp_path):
        config_file = _write_yaml(tmp_path, "spacy_model: pt_core_news_sm\nintents: []")
        config = ConfigLoader.load(config_file)
        assert config.min_confidence == 0.70
        assert config.preprocessing_steps == ()

    def test_uses_default_model_when_absent(self, tmp_path):
        config_file = _write_yaml(tmp_path, "intents: []")
        config = ConfigLoader.load(config_file)
        assert config.spacy_model == "pt_core_news_sm"


class TestInvalidConfig:
    def test_raises_when_file_not_found(self):
        with pytest.raises(ConfigurationError, match="não encontrado"):
            ConfigLoader.load("/caminho/inexistente/config.yml")

    def test_raises_on_missing_intent_name(self, tmp_path):
        config_file = _write_yaml(tmp_path, """
intents:
  - action:
      type: BUY_STOCK
      description: "x"
    confidence:
      phrase: 0.9
      lemma: 0.7
    patterns:
      phrases: []
      lemmas: []
""")
        with pytest.raises(ConfigurationError, match="campo ausente"):
            ConfigLoader.load(config_file)

    def test_raises_on_malformed_yaml(self, tmp_path):
        config_file = tmp_path / "bad.yml"
        config_file.write_text("key: [unclosed bracket", encoding="utf-8")
        with pytest.raises(ConfigurationError, match="parsear YAML"):
            ConfigLoader.load(config_file)
