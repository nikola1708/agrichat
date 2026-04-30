# Ollama Local Setup (Quick)

1. Install Ollama (follow official instructions):
   - Windows: use the installer from https://ollama.com/docs

2. Start Ollama server locally (example):

```powershell
ollama server
```

3. Pull or install a model locally (example):

```powershell
ollama pull <model-name>
```

4. Configure the bot to use Ollama in `local.settings.json`:

- Set `AI_ENGINE` to `ollama`.
- Ensure `OLLAMA_URL` matches the server URL (default `http://localhost:11434`).
- Set `OLLAMA_MODEL` to the model name you pulled.

5. Restart the bot/backend (Azure Functions host or local runner).

Notes:
- Ollama endpoints and response shapes may vary by version. If responses are empty,
  check the server logs and adjust `shared/ai_engine.py` endpoint paths accordingly.
