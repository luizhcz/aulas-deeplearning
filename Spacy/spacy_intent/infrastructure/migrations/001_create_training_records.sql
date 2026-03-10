-- =============================================================================
-- Migração 001: tabela de registros de treinamento para o modelo ML
--
-- Execute antes de habilitar training.enabled=true na configuração.
-- =============================================================================

CREATE TABLE IF NOT EXISTS intent_training_records (
    id             BIGSERIAL        PRIMARY KEY,
    text           TEXT             NOT NULL,
    processed_text TEXT             NOT NULL,
    intent         VARCHAR(100)     NOT NULL,
    confidence     DOUBLE PRECISION NOT NULL,
    classified_at  TIMESTAMPTZ      NOT NULL,
    created_at     TIMESTAMPTZ      NOT NULL DEFAULT NOW()
);

-- Consultas típicas para geração de dataset de treino:
--   SELECT * FROM intent_training_records WHERE confidence >= 0.7
--   SELECT * FROM intent_training_records WHERE intent = 'buy_stock' ORDER BY classified_at DESC
--   SELECT * FROM intent_training_records WHERE classified_at >= NOW() - INTERVAL '30 days'

CREATE INDEX IF NOT EXISTS idx_itr_intent
    ON intent_training_records (intent);

CREATE INDEX IF NOT EXISTS idx_itr_confidence
    ON intent_training_records (confidence);

CREATE INDEX IF NOT EXISTS idx_itr_classified_at
    ON intent_training_records (classified_at DESC);
