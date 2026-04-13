# Phase 2 Report

## Objective And Current MVP Definition

NestGPT is an AI-assisted housing and relocation research tool for people planning to move abroad. The current MVP focuses on three countries and three cities per country:

- Japan: Tokyo, Osaka, Kyoto
- Germany: Berlin, Munich, Hamburg
- Portugal: Lisbon, Porto, Faro

Concrete MVP definition:

- A user can choose a destination, enter a budget and relocation context, and receive housing-focused relocation guidance.
- The system returns an answer that explains likely affordability, housing process details, risks, and relevant visa-related housing considerations.

## What Has Been Built So Far

- A local Python web application with a guided form UI
- Structured user inputs for country, city, budget, currency, timeline, reason, nationality, and special concerns
- A `Baseline AI Mode` that answers without live retrieval
- A `NestGPT Research Mode` that performs web search, fetches source text, and grounds the answer in retrieved content
- Prompt specialization through `AGENT.md` and `SKILL.md`

## Technical Approach

Baseline:

- Send the structured relocation prompt directly to the model without retrieval

Improved NestGPT mode:

- Build a targeted search query from the user form
- Search the web for relevant pages
- Fetch and clean excerpts from the top pages
- Send the source excerpts plus prompt instructions to the model
- Return a structured answer with citations

## Evidence Of Progress

Planned comparison method:

- Run the benchmark cases in `phase2/benchmark_cases.md`
- Compare baseline output versus research-grounded output
- Record differences in:
  - specificity
  - citation quality
  - affordability assessment
  - rental-process detail
  - uncertainty handling

## Current Limitations And Open Risks

- Search quality depends on general web results rather than official listing APIs
- Housing rules can vary by neighborhood, landlord, and lease type
- The agent provides the most common answers to questions rather than extremely specific "house-by-house" information
- The system does not yet rank actual listing inventory
- Source freshness and extraction quality can vary between websites
- Users are still encouraged to self verify any information provided by NestGPT, though how many truly will is hard to say

## Plan For Phase 3

- Add listing-aware recommendations using a structured data source
- Improve source prioritization for official government and city pages
- Add saved evaluation outputs and screenshots as artifacts
- Expand support for multilingual landlord communication
- Direct users toward potential housing listings (possible but not likely)
