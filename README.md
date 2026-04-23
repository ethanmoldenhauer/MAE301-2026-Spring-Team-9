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

