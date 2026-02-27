import requests

r = requests.post("http://localhost:9001/invoke", json={
  "input": {"text": "quero comprar 10 PETR4 a 37,50"},
  "context": {"session_id": "s1", "tenant_id": "t1", "user_id": "u1", "verbose": True, "vars": {}}
})

print(r.status_code)
print(r.json())