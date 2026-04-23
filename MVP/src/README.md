# Source Code

## Entrypoint

- `nestgpt_agent.py`: local HTTP server, retrieval pipeline, prompt construction, dataset loading, and API calls

## Supporting Files

- `app_template.html`: complete front-end UI
- `AGENT.md`: answer-formatting and safety guidance
- `SKILL.md`: source-priority and research workflow guidance
- `NestGPT-Logo.png`: UI logo asset

## Run

From the `mvp/` directory:

```powershell
python .\src\nestgpt_agent.py
```

The server will start on `http://127.0.0.1:8000`.
