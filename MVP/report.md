# NestGPT MVP Report

## 1. Summary

NestGPT is a local web application for housing-focused relocation planning. It targets users who are considering a move to a supported city in Japan, Germany, or Portugal and need more than a generic chatbot answer. The MVP combines structured user inputs, retrieval from live web sources, and small open-dataset slices to produce grounded relocation guidance.

The MVP does not attempt to be a full real-estate marketplace. Instead, it narrows scope to two practical use cases:

- long-term apartment rental guidance
- house-purchase planning guidance

In its current form, the MVP can:

- collect a relocation profile including city, budget, timeline, nationality, and move reason
- answer a focused housing question in either baseline or retrieval-backed mode
- use local benchmark datasets as supplemental evidence
- surface risk scores, city comparison, action-plan guidance, and landlord-message support in the UI

## 2. User And Use Case

Primary persona:

- internationally mobile student, worker, or remote professional who is early in the move-planning process and needs trustworthy first-pass guidance

Example usage narrative:

1. A user selects Berlin, enters a monthly budget of 1100 EUR, chooses `Study`, and states that they are planning to move within three to six months.
2. The user asks what barriers international students face when trying to rent and whether the budget is realistic.
3. NestGPT builds a focused search query, gathers web results, loads any matching local rental benchmarks, and generates a grounded answer.
4. The UI then adds a budget/risk readout, same-country city comparison, and suggested next steps the user can act on immediately.

The product is meant to reduce three problems:

- scattered and inconsistent relocation information
- difficulty translating a personal budget into a realistic housing judgment
- weak visibility into uncertainty, scams, and paperwork friction

## 3. System Design

High-level architecture:

```text
User Form Input
    |
    v
Profile Builder + Query Builder
    |
    +--> Baseline Mode ------------------------------+
    |                                                |
    v                                                v
Web Search --> Page Fetch --> Source Cleaning --> Prompt Assembly
    |                                                |
    +--> Local Dataset Matching ---------------------+
                                                     |
                                                     v
                                        OpenRouter-hosted LLM
                                                     |
                                                     v
                                Answer + Sources + UI Planning Panels
```

Main components:

- `src/nestgpt_agent.py`: backend server, routing, search, retrieval, dataset matching, prompt assembly, and response generation
- `src/app_template.html`: browser UI and client-side planning helpers
- `data/`: benchmark dataset manifests and small sample records
- `src/AGENT.md` and `src/SKILL.md`: prompt rules for answer style, safety, and source prioritization

The model sits at the answer-synthesis stage. Upstream logic is responsible for narrowing the user request, collecting evidence, and formatting a prompt that includes both the user profile and source snippets.

## 4. Data

### Data Sources

The MVP uses two classes of data:

1. Live web sources at runtime
2. Local open-dataset slices stored in `mvp/data/`

Examples of web-source categories:

- government portals
- municipal or immigration office pages
- reputable market guides
- city-service pages

Examples of local open-dataset scope:

- Portugal apartment rent benchmarks
- Portugal real-estate sale samples
- Germany rental samples
- Germany house purchase benchmarks
- Japan apartment rent benchmarks
- Japan property transaction samples

### Size

The local dataset layer is intentionally small. The app loads lightweight evidence slices and caps the number of records injected into prompts. This keeps the MVP fast and understandable while still demonstrating data provenance and dataset-aware retrieval.

### Cleaning And Preprocessing

Preprocessing is documented inside each dataset manifest. Common steps include:

- filtering to supported countries or cities
- removing rows with missing key price fields
- keeping a small number of records as prompt evidence
- preserving source URL, license, dataset type, and preprocessing notes for downstream citation

### Licensing And Data Origin

The app documents dataset origin, source URL, license, and preprocessing notes in the manifests under `data/`. This was included to satisfy the project requirement that external data use be transparent and attributable.

## 5. Models

NestGPT is an agentic workflow built around a hosted frontier language model rather than a fine-tuned checkpoint.

Model strategy:

- baseline mode: direct answer generation from the hosted model without retrieval
- research mode: retrieval-augmented prompting using web excerpts plus local dataset evidence

Workflow-design choices:

- structured user-profile prompting instead of a single free-form text box
- targeted query generation based on city, move reason, and user concern
- source prioritization rules favoring government and municipal pages when available
- cautious answer formatting that highlights uncertainty and missing verification steps
- dataset metadata injection so the model can mention origin, license, and preprocessing when using external data

This means the main contribution is system design and prompt workflow rather than parameter training.

## 6. Evaluation

### Evaluation Approach

Evaluation for this MVP focused on functional and qualitative performance rather than benchmark training metrics, because the project uses a hosted model and a retrieval workflow.

Artifacts used for evaluation:

- `benchmark_cases.md` with three representative relocation scenarios
- side-by-side comparison target: baseline mode versus research mode
- manual inspection of source citation quality, affordability judgments, and uncertainty handling

### Functional Coverage

Current MVP coverage includes:

- 3 supported countries
- 9 supported cities
- 2 answer modes
- 6 local dataset manifests
- UI support for risk scoring, city comparison, action plans, landlord messaging, and scenario saving

### Qualitative Findings

From the project design and current implementation, the retrieval-backed mode is expected to outperform baseline mode on:

- citing source-backed claims
- giving city-specific affordability context
- surfacing required documents or registration issues
- explaining uncertainty when sources are weak or mixed

The baseline mode remains useful as a fast comparison condition, but it is more vulnerable to generic advice and missing local specifics.

### Current Limitation Of Evaluation

This MVP does not yet include an automated evaluation harness or numeric accuracy benchmark. A stronger next phase would save benchmark outputs and score them across fixed rubrics such as:

- affordability judgment present or absent
- citations present or absent
- number of city-specific details
- number of explicit uncertainty statements

## 7. Limitations And Risks

Important limitations:

- live search quality depends on available web results and page extraction quality
- the system is not a legal advisor and should not be treated as authoritative on visas or residency rules
- local dataset slices are small and are meant as benchmark context, not comprehensive market coverage
- example listings are lightweight references rather than live inventory search
- city comparison is currently limited to cities within the selected country

Risk areas:

- stale or conflicting source content
- over-reliance on secondary market guides when primary sources are unavailable
- bias introduced by small benchmark samples
- privacy risk if users paste unusually sensitive personal information into free-text questions

## 8. Next Steps

If given more time, the next steps would be:

1. Add an evaluation that runs benchmark cases automatically and saves outputs for baseline-versus-research comparison.
2. Expand data coverage with more official local housing sources and stronger provenance tracking.
3. Improve the listing layer from a single example card to multiple validated listing references.
4. Add cross-country comparison so users can compare, for example, Berlin versus Lisbon directly.
5. Add export or shareable summary generation for users who want to save a relocation brief.
