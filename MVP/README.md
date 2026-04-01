# NestGPT Source-Backed MVP

A Streamlit MVP for helping users find housing abroad.

## What it does
- answers housing and visa questions from source-backed documents
- shows citations and freshness labels
- translates text such as landlord messages
- summarizes lease or immigration text
- saves user profile preferences
- saves apartments and compares them side by side

## Project structure
- `app.py` - main Streamlit app
- `src/` - retrieval, answering, memory, comparison, utilities
- `data/processed/` - source-backed JSONL documents
- `storage/nestgpt.db` - SQLite database created automatically

## Setup
### Mac/Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Windows PowerShell
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## API keys
The app supports either OpenRouter or OpenAI directly.

### OpenRouter
```powershell
$env:OPENROUTER_API_KEY="your_key_here"
```

### OpenAI
```powershell
$env:OPENAI_API_KEY="your_key_here"
```

If no API key is present, the app still works in local fallback mode for retrieval, profile memory, apartment saving, and comparisons.
Translation and richer AI answers require an API key.

## Run
```bash
streamlit run app.py
```

## Optional logo
Place one of these in the project folder to show a custom logo in the app header:
- `logo.png`
- `logo.jpg`
- `logo.jpeg`
- `logo.webp`

## How the source-backed system works
1. Load JSONL records from `data/processed/`
2. Retrieve relevant chunks by country and topic
3. Ask the model to answer only from those chunks
4. Render citations with source title, URL, publisher, and freshness

## Add more verified sources
Add more JSONL files to `data/processed/` with records like:
```json
{
  "chunk_id": "de-housing-001",
  "country": "Germany",
  "topic": "housing",
  "title": "Housing and registration",
  "publisher": "Make it in Germany",
  "url": "https://www.make-it-in-germany.com/en/living-in-germany/housing-mobility/housing-registration",
  "last_checked": "2026-04-01",
  "text": "Your cleaned source text here"
}
```

## Notes
- The included sample documents are starter records for the MVP.
- Replace and expand them with your own verified extracts before relying on the app for real guidance.
- This project is not legal or immigration advice.
