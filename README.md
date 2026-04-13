# NestGPT

NestGPT is a local relocation-planning web app for comparing housing options across supported cities in Japan, Germany, and Portugal.

It combines:
- structured trip inputs
- source-backed research through OpenRouter
- local benchmark datasets for apartment rentals and house purchases
- decision-support tools like city comparison, risk scoring, action plans, and landlord message drafting

## What the app does

- Collects relocation inputs such as country, city, budget, currency, move timeline, passport profile, and relocation reason
- Lets the user ask a focused housing or relocation question
- Supports both `NestGPT research mode` and `Baseline AI mode`
- Uses live web research when available
- Uses local benchmark datasets as supplemental evidence for:
  - renting apartments
  - buying houses, townhouses, or detached homes
- Shows a direct answer with sources
- Adds interactive planning features in the UI, including:
  - personalized move verdict
  - risk scoring
  - same-country city comparison
  - action plan generator
  - landlord-ready message draft
  - what-if scenario controls
  - saved scenarios
  - source insight summaries
- Shows a real listing reference card when the user explicitly asks for a listing or example property

## Supported scope

The app is intentionally narrow.

Supported countries and cities:
- Japan: Tokyo, Osaka, Kyoto
- Germany: Berlin, Munich, Hamburg
- Portugal: Lisbon, Porto, Faro

Supported housing intent:
- apartment rentals
- house purchases

Excluded on purpose:
- apartment purchases
- whole-building purchases
- large land-only deals
- broad commercial property searches

## Main files

- `nestgpt_agent.py`: backend app, research pipeline, routing, source handling, and dataset loading
- `app_template.html`: full front-end UI and interaction logic
- `AGENT.md`: answer behavior and structure instructions
- `SKILL.md`: research workflow and source-priority guidance
- `datasets/`: local benchmark dataset manifests and records
- `requirements.txt`: Python dependencies
- `NestGPT-Logo.png`: logo asset
- `report.md`: optional project/report file
- `benchmark_cases.md`: optional benchmark or evaluation prompts

## Dataset approach

NestGPT currently uses small local benchmark datasets rather than live bulk property feeds.

These datasets are used to keep the app focused on:
- apartment rental guidance
- house-purchase guidance

Each dataset includes:
- source origin
- source URL
- license note
- dataset type
- market type
- preprocessing notes

The app also documents benchmark provenance in the sources section when those datasets are used.

See [datasets/README.md](C:\Users\erta0\OneDrive\Desktop\NestGPT_v2\datasets\README.md) for the manifest format.

## Setup

1. Install dependencies:

```powershell
pip install -r requirements.txt
```

2. Set your OpenRouter API key:

```powershell
$env:OPENROUTER_API_KEY="your_key_here"
```

Optional model override:

```powershell
$env:OPENROUTER_MODEL="openai/gpt-5.4"
```

3. Run the app:

```powershell
python nestgpt_agent.py
```

4. Open:

`http://127.0.0.1:8000`

## Requirements

Current Python dependencies:
- `requests`
- `beautifulsoup4`

## Limitations

- Some guidance uses curated benchmark data rather than live listing feeds
- Real listing references are lightweight and intended as practical examples, not a full inventory system
- Passport-profile effects are planning heuristics, not legal advice or visa eligibility decisions
- The app currently compares cities within the selected country, not across all countries at once

## Future improvements

- Add multiple live listing candidates per city
- Add cross-country city comparison
- Add explicit rent-vs-buy UI toggles
- Add more official local data sources for each city
- Add export or shareable scenario summaries
