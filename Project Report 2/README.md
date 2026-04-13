# NestGPT MVP

This project is a tutorial-style MVP for **NestGPT**, an agent that researches housing-abroad questions using live web sources and a language model.

## What this MVP does

- Accepts a relocation or housing question in a small local web app
- Lets the user choose between a baseline AI mode and an improved NestGPT research mode
- Collects structured inputs such as country, city, budget, currency, move timeline, and relocation reason
- Searches the web for relevant sources
- Fetches text from a few pages
- Sends the grounded context to a model through OpenRouter
- Returns a structured answer with source citations

Example questions:

- `What should a U.S. citizen know about renting an apartment in Lisbon for one year?`
- `Compare visa and rental requirements for moving to Berlin as a student.`
- `What are the major risks when trying to rent in Tokyo before arrival?`

## Project files

- `AGENT.md`: the system behavior and answer structure
- `SKILL.md`: the research workflow and source priority rules
- `nestgpt_agent.py`: the local web app and research pipeline
- `requirements.txt`: Python dependencies
- `phase2/benchmark_cases.md`: benchmark prompts for comparing baseline vs improved behavior
- `phase2/report.md`: starter Phase 2 progress report

## Setup

1. Create a virtual environment if you want:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Set your OpenRouter API key:

```powershell
$env:OPENROUTER_API_KEY="your_key_here"
```

Optional:

```powershell
$env:OPENROUTER_MODEL="openai/gpt-5.4"
```

4. Run the app:

```powershell
python nestgpt_agent.py
```

5. Open:

`http://127.0.0.1:8000`

## Suggested next upgrades

- Add source filtering by country and topic
- Save research results so repeated questions are faster
- Add listing APIs for current housing inventory
- Add multilingual translation support for landlord communication
- Add structured country profiles for your first few MVP locations

## Open dataset support

NestGPT can also use small local open datasets as supplemental evidence.

- Put dataset manifests in [datasets/README.md](C:\Users\erta0\OneDrive\Desktop\NestGPT_v2\datasets\README.md)'s format.
- Supported sources can include Kaggle, Hugging Face Datasets, UCI, or government open data exports, as long as you respect the dataset's license and terms.
- Each dataset should document:
  - origin
  - source URL
  - license
  - dataset type and market type
  - preprocessing steps such as filtering, deduplication, or sampling

When a dataset matches the selected city/country, NestGPT injects a small number of records into the research context and asks the model to cite the dataset responsibly.
