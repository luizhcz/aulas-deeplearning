import httpx

payload = {
  "input": {"text": "quero comprar 10 PETR4 a 37,50"},
  "context": {"session_id": "s-test", "trace_id": "t-test", "vars": {}}
}

r = httpx.post("http://localhost:9005/invoke", json=payload, timeout=10)
print(r.status_code)
print(r.json())