# Models

NestGPT does not ship a fine-tuned local checkpoint in this MVP.

## Model Strategy

- Primary hosted model: OpenRouter-served frontier LLM
- Default model identifier: `openai/gpt-5.4`
- Baseline mode: same hosted model, but without retrieval
- Research mode: same hosted model with retrieved web evidence and local dataset evidence injected into the prompt

## Why There Is No Local Checkpoint

This project is an agentic retrieval-and-reasoning MVP rather than a supervised fine-tuning project. The core contribution is the workflow:

- structured user profile collection
- targeted search-query generation
- web retrieval and source cleaning
- dataset-aware prompt construction
- grounded answer formatting with explicit risks and citations

## Reproducibility

To reproduce the MVP:

1. Install `../requirements.txt`
2. Set `OPENROUTER_API_KEY`
3. Run `python ..\src\nestgpt_agent.py` from the `mvp/` directory

## Optional Public Sharing

If this project is later shared on Hugging Face, the recommended artifact is not a model checkpoint but a model card or Space documenting:

- supported countries and cities
- data sources and licenses
- retrieval pipeline
- limitations and risks
- demo instructions
