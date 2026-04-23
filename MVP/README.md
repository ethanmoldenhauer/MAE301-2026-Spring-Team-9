# NestGPT MVP

This folder contains the Phase 3 MVP submission package for NestGPT, a local web app for relocation-focused housing research.

## Folder Layout

- `src/`: application source code and UI assets
- `data/`: local open-dataset slices plus provenance notes
- `models/`: model-hosting and checkpoint notes
- `report.md`: MVP report
- `requirements.txt`: Python dependencies

## What The MVP Does

NestGPT helps a user compare supported cities in Japan, Germany, and Portugal for either apartment renting or house purchasing. The user enters a city, budget, timeline, nationality, and relocation context, then receives either:

- `NestGPT Research Mode`: retrieval-augmented output grounded in live web search plus local benchmark datasets
- `Baseline AI Mode`: a direct model response without retrieval

The UI also includes:

- risk scoring
- same-country city comparison
- action plan generation
- landlord-ready message drafting
- saved scenarios
- source insight summaries
- example listing cards when the user explicitly asks for a listing

## Setup

1. Open a terminal in the `mvp/` directory.
2. Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

3. Provide an OpenRouter API key using either method below:

```powershell
$env:OPENROUTER_API_KEY="your_key_here"
```

Or create `mvp/APIKEY.txt` and place the key there.

4. Optional: choose a different model:

```powershell
$env:OPENROUTER_MODEL="openai/gpt-5.4"
```

## Run A Minimal Demo

From the `mvp/` directory:

```powershell
python .\src\nestgpt_agent.py
```

Then open:

`http://127.0.0.1:8000`

## Colab / Instructor Notes

- This MVP is designed to run locally with Python.
- The app is lightweight and does not require local model weights.
- If running in Colab, upload the `mvp/` folder, install `requirements.txt`, set the API key as an environment variable, and run `python src/nestgpt_agent.py`.
- Because the app serves a local web page, local desktop execution is the simplest path for grading and demo purposes.

## Important Notes

- The MVP uses external web research and therefore needs internet access at runtime.
- If OpenRouter credits are unavailable, the app falls back to a shorter source-summary mode for research answers.
- Dataset licensing, source origin, and preprocessing notes are documented in `data/`.
