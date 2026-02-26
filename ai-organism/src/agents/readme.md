# README — Rodar e testar o projeto de Agents (HTTP)

Este projeto expõe **agents via HTTP** usando FastAPI/Uvicorn, com endpoints padrão:

* `GET /spec` — metadados + schemas
* `GET /health` — health check
* `POST /invoke` — invocação do agente (sync)

Os agents usam **LLM + tools (@tool)** quando necessário (ex.: `time_by_zone` chama `get_time_by_zone`).

---

## 0) Pré-requisitos

### 0.1 Python

Recomendado: **Python 3.12** (ou 3.11).
Evite 3.14 (problemas de compatibilidade com LangChain/Pydantic).

Verificar:

```bash
python -V
```

### 0.2 Ollama

* Instale e suba o Ollama
* Baixe um modelo (exemplo):

```bash
ollama pull llama3.1:8b
```

---

## 1) Criar ambiente virtual e instalar dependências

Na raiz do projeto:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

---

## 2) Variáveis de ambiente (.env)

Recomendado criar um `.env` na raiz com:

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b

# opcionais (para heartbeat; pode deixar vazio se não usar registry)
REGISTRY_URL=http://localhost:9100
HEARTBEAT_INTERVAL_S=10
```

Se você usa `python-dotenv`, inclua no `main.py` do agent (ou exporte no shell):

```python
from dotenv import load_dotenv
load_dotenv()
```

---

## 3) Subir um Agent (passo a passo)

### 3.1 Regra importante: projeto usa `src/` layout

Sempre rode uvicorn com:

* `--app-dir src`

Exemplo geral:

```bash
uvicorn --app-dir src <import.path>:app --port <PORT> --reload
```

---

## 4) Subir os Agents disponíveis

### 4.1 Agent: `order_extraction` (LLM)

```bash
uvicorn --app-dir src agents.trading.order_extraction.main:app --port 9001 --reload
```

### 4.2 Agent: `order_placement` (LLM + tool ou execução, dependendo da versão do seu código)

```bash
uvicorn --app-dir src agents.trading.order_placement.main:app --port 9002 --reload
```

### 4.3 Agent: `time_by_zone` (LLM + tool `get_time_by_zone`)

```bash
uvicorn --app-dir src agents.util.time_by_zone.main:app --port 9010 --reload
```

> Dica: rode cada agente em um terminal separado.

---

## 5) Como testar um Agent (3 testes)

Supondo que o agent está rodando em `http://127.0.0.1:<PORT>`.

### 5.1 Smoke test (spec + health)

```bash
curl http://127.0.0.1:9010/spec
curl http://127.0.0.1:9010/health
```

Você deve ver `status: UP`.

---

### 5.2 Teste funcional (POST /invoke)

Formato padrão da request:

```json
{
  "input": { ... },
  "context": { "session_id": "...", "trace_id": "...", "vars": {} }
}
```

#### (A) `time_by_zone`

```bash
curl -X POST http://127.0.0.1:9010/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "input": { "message": "Como está o tempo no brasil" },
    "context": { "session_id": "s-time-1", "trace_id": "t-001", "vars": {} }
  }'
```

#### (B) `order_extraction`

```bash
curl -X POST http://127.0.0.1:9001/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "input": { "text": "quero comprar 10 PETR4 a 37,50" },
    "context": { "session_id": "s-order-1", "trace_id": "t-002", "vars": {} }
  }'
```

#### (C) `order_placement`

```bash
curl -X POST http://127.0.0.1:9002/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "input": { "side": "BUY", "asset": "PETR4", "quantity": 10, "price": 37.5 },
    "context": { "session_id": "s-order-2", "trace_id": "t-003", "vars": {} }
  }'
```

---

### 5.3 Teste com múltiplas sessões (isolamento)

Repita o `/invoke` mudando `session_id`:

```bash
curl -X POST http://127.0.0.1:9010/invoke \
  -H "Content-Type: application/json" \
  -d '{"input":{"message":"Como está o tempo no brasil"},"context":{"session_id":"s1","vars":{}}}'

curl -X POST http://127.0.0.1:9010/invoke \
  -H "Content-Type: application/json" \
  -d '{"input":{"message":"Como está o tempo no brasil"},"context":{"session_id":"s2","vars":{}}}'

curl -X POST http://127.0.0.1:9010/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "input": { "message": "Como está o tempo no brasil" },
    "context": { "session_id": "s1", "trace_id": "t-001", "verbose": true, "vars": {} }
  }'
```

Cada chamada deve ser independente (o host suporta múltiplas sessões).

---

## 6) Erros comuns e como resolver

### 6.1 `ModuleNotFoundError: No module named 'agents'`

Você esqueceu `--app-dir src`:

✅ Use:

```bash
uvicorn --app-dir src agents.util.time_by_zone.main:app --port 9010 --reload
```

---

### 6.2 Tool exige docstring

Se aparecer:
`ValueError: Function must have a docstring if description not provided`

✅ coloque docstring na função `@tool`:

```python
@tool
def my_tool(...):
    """Descrição da ferramenta."""
    ...
```

---

### 6.3 Ollama lento / timeout

* Use um modelo menor (ex.: `qwen2.5:3b`)
* Aumente timeout do agente (na spec/base) se necessário
* Confirme Ollama:

```bash
curl http://localhost:11434/api/tags
```

---

## 7) Dicas de operação (boa prática)

* Um agent por porta.
* Use logs do Uvicorn para debug.
* Use `/spec` para confirmar schema do input/output.

---