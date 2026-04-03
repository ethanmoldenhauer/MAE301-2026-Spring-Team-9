import json
import os
import re
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Iterable
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup


HOST = "127.0.0.1"
PORT = 8000
MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-5.4")
MAX_SEARCH_RESULTS = 5
MAX_PAGES = 4
MAX_PAGE_CHARS = 2500
REQUEST_TIMEOUT = 20

HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>NestGPT</title>
  <style>
    :root {
      --bg: #f5efe3;
      --panel: #fffaf2;
      --ink: #1f1f1c;
      --muted: #5f5a50;
      --accent: #0e6b5c;
      --accent-2: #cc6b3d;
      --border: #d8ccb5;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(204,107,61,.12), transparent 30%),
        radial-gradient(circle at bottom right, rgba(14,107,92,.16), transparent 32%),
        var(--bg);
    }
    .wrap {
      max-width: 880px;
      margin: 48px auto;
      padding: 0 18px;
    }
    .card {
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 18px;
      padding: 24px;
      box-shadow: 0 12px 40px rgba(31,31,28,.08);
    }
    h1 {
      margin: 0 0 8px;
      font-size: clamp(2rem, 5vw, 3.2rem);
      line-height: 1.05;
    }
    p {
      color: var(--muted);
      margin: 0 0 18px;
      font-size: 1rem;
    }
    .intro {
      padding: 18px;
      border-radius: 16px;
      background: linear-gradient(135deg, rgba(14,107,92,.09), rgba(204,107,61,.08));
      border: 1px solid var(--border);
      margin-bottom: 20px;
    }
    .intro strong {
      display: block;
      margin-bottom: 8px;
      font-size: 1.05rem;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 14px;
      margin-bottom: 14px;
    }
    .field {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .field.full {
      grid-column: 1 / -1;
    }
    label {
      font-weight: 700;
      font-size: .96rem;
    }
    select, input {
      width: 100%;
      font: inherit;
      padding: 12px 14px;
      border-radius: 14px;
      border: 1px solid var(--border);
      background: white;
      color: var(--ink);
    }
    textarea {
      width: 100%;
      min-height: 150px;
      resize: vertical;
      font: inherit;
      padding: 14px;
      border-radius: 14px;
      border: 1px solid var(--border);
      background: white;
      color: var(--ink);
    }
    .actions {
      display: flex;
      gap: 12px;
      margin-top: 14px;
      flex-wrap: wrap;
    }
    button {
      border: 0;
      border-radius: 999px;
      padding: 12px 18px;
      font: inherit;
      cursor: pointer;
    }
    .primary {
      background: var(--accent);
      color: white;
    }
    .secondary {
      background: #ece3d3;
      color: var(--ink);
    }
    pre {
      white-space: pre-wrap;
      word-break: break-word;
      background: #fff;
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 16px;
      min-height: 220px;
      line-height: 1.45;
      overflow-x: auto;
    }
    .status {
      margin: 14px 0;
      color: var(--accent-2);
      min-height: 1.5em;
      font-weight: 600;
    }
    .hint {
      color: var(--muted);
      font-size: .94rem;
      margin: 2px 0 0;
    }
    @media (max-width: 700px) {
      .grid {
        grid-template-columns: 1fr;
      }
    }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="card">
      <h1>NestGPT</h1>
      <p>AI-powered housing and relocation guidance for people planning to live abroad.</p>
      <div class="intro">
        <strong>What NestGPT helps with</strong>
        <p>NestGPT is designed for people moving abroad who need clearer information about housing, rental laws, relocation steps, and visa-related housing barriers. It gathers information from multiple sources and turns it into practical guidance that is easier to understand.</p>
        <p class="hint">This MVP focuses on Japan, Germany, and Portugal so the information can stay more structured and useful.</p>
      </div>
      <div class="grid">
        <div class="field">
          <label for="country">Country</label>
          <select id="country"></select>
        </div>
        <div class="field">
          <label for="city">City</label>
          <select id="city"></select>
        </div>
        <div class="field">
          <label for="budget">Monthly Housing Budget</label>
          <input id="budget" type="text" placeholder="Example: 1400">
        </div>
        <div class="field">
          <label for="currency">Currency</label>
          <select id="currency">
            <option value="EUR">EUR</option>
            <option value="JPY">JPY</option>
            <option value="USD">USD</option>
          </select>
        </div>
        <div class="field">
          <label for="reason">Reason for Relocating</label>
          <select id="reason">
            <option value="Work">Work</option>
            <option value="Study">Study</option>
            <option value="Remote work">Remote work</option>
            <option value="Family">Family</option>
            <option value="Long-term travel">Long-term travel</option>
          </select>
        </div>
        <div class="field">
          <label for="timeline">Planned Move Timeline</label>
          <select id="timeline">
            <option value="Within 1 month">Within 1 month</option>
            <option value="1 to 3 months">1 to 3 months</option>
            <option value="3 to 6 months">3 to 6 months</option>
            <option value="6 to 12 months">6 to 12 months</option>
            <option value="More than 1 year">More than 1 year</option>
          </select>
        </div>
        <div class="field">
          <label for="nationality">Nationality or Passport</label>
          <input id="nationality" type="text" placeholder="Example: U.S. citizen">
        </div>
        <div class="field">
          <label for="mode">Answer Mode</label>
          <select id="mode">
            <option value="research">NestGPT Research Mode</option>
            <option value="baseline">Baseline AI Mode</option>
          </select>
        </div>
        <div class="field full">
          <label for="message">Specific Question or Concern</label>
          <textarea id="message" placeholder="Example: I want to rent before I arrive. What documents do landlords usually ask for, and what scams should I watch out for?"></textarea>
        </div>
      </div>
      <div class="actions">
        <button class="primary" id="askButton">Research</button>
        <button class="secondary" id="clearButton">Clear</button>
      </div>
      <div class="status" id="status">Idle.</div>
      <pre id="output"></pre>
    </div>
  </div>
  <script>
    const locationOptions = {
      "Japan": ["Tokyo", "Osaka", "Kyoto"],
      "Germany": ["Berlin", "Munich", "Hamburg"],
      "Portugal": ["Lisbon", "Porto", "Faro"]
    };

    const askButton = document.getElementById("askButton");
    const clearButton = document.getElementById("clearButton");
    const country = document.getElementById("country");
    const city = document.getElementById("city");
    const budget = document.getElementById("budget");
    const currency = document.getElementById("currency");
    const reason = document.getElementById("reason");
    const timeline = document.getElementById("timeline");
    const nationality = document.getElementById("nationality");
    const mode = document.getElementById("mode");
    const message = document.getElementById("message");
    const output = document.getElementById("output");
    const status = document.getElementById("status");

    function populateCountries() {
      Object.keys(locationOptions).forEach((name) => {
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        country.appendChild(option);
      });
      country.value = "Japan";
      populateCities();
      currency.value = "JPY";
    }

    function populateCities() {
      const cities = locationOptions[country.value] || [];
      city.innerHTML = "";
      cities.forEach((name) => {
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        city.appendChild(option);
      });
      if (country.value === "Japan") {
        currency.value = "JPY";
      } else if (country.value === "Germany" || country.value === "Portugal") {
        currency.value = "EUR";
      }
    }

    country.addEventListener("change", populateCities);

    askButton.addEventListener("click", async () => {
      if (!budget.value.trim() || !nationality.value.trim()) {
        status.textContent = "Add your budget and nationality first.";
        return;
      }
      status.textContent = mode.value === "baseline"
        ? "Drafting a baseline AI answer..."
        : "Researching sources and drafting an answer...";
      output.textContent = "";
      try {
        const response = await fetch("/ask", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            country: country.value,
            city: city.value,
            budget: budget.value.trim(),
            currency: currency.value,
            reason: reason.value,
            timeline: timeline.value,
            nationality: nationality.value.trim(),
            mode: mode.value,
            message: message.value.trim()
          })
        });
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.error || "Request failed.");
        }
        output.textContent = data.output;
        status.textContent = "Done.";
      } catch (error) {
        status.textContent = "Request failed.";
        output.textContent = String(error);
      }
    });

    clearButton.addEventListener("click", () => {
      country.value = "Japan";
      populateCities();
      budget.value = "";
      currency.value = "JPY";
      reason.value = "Work";
      timeline.value = "Within 1 month";
      nationality.value = "";
      mode.value = "research";
      message.value = "";
      output.textContent = "";
      status.textContent = "Idle.";
    });

    populateCountries();
  </script>
</body>
</html>
"""


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0 Safari/537.36 NestGPT/0.1"
)

HTTP = requests.Session()
HTTP.trust_env = False

CURATED_SOURCES = {
    "Portugal": [
        (
            "Portugal visas and residence",
            "https://www2.gov.pt/en/migrantes-viver-e-trabalhar-em-portugal/migrantes-vistos-e-autorizacoes-para-entrar-e-viver-em-portugal",
            "Official Portugal government page about visas and authorization to enter and live in Portugal.",
        ),
        (
            "Portugal government services",
            "https://www2.gov.pt/en/",
            "Official Portugal government portal with housing and migration topics.",
        ),
    ],
    "Lisbon": [
        (
            "Lisbon housing information",
            "https://www.lisboa.pt/en/themes/housing/entry",
            "Official Lisbon city page for housing-related information and services.",
        ),
        (
            "Lisbon rental cost context",
            "https://www.idealista.pt/en/news/financial-advice-in-portugal/2026/01/20/72090-the-cost-of-retiring-in-portugal-a-comprehensive-guide-for-2026",
            "Recent idealista market guide noting that Lisbon one-bedroom city-centre rents are often around 1300 to 1800 EUR per month.",
        ),
    ],
    "Porto": [
        (
            "Porto rental cost context",
            "https://investropa.com/blogs/news/average-rent-porto",
            "Recent Porto market guide noting that one-bedroom apartments are often around 900 to 1200 EUR per month.",
        ),
    ],
    "Faro": [
        (
            "Faro rental cost context",
            "https://investropa.com/blogs/news/algarve-rents",
            "Recent Algarve market guide noting that one-bedroom apartments often fall around 750 to 1150 EUR per month, used here as a Faro-area proxy.",
        ),
    ],
    "Germany": [
        (
            "Housing and registration in Germany",
            "https://www.make-it-in-germany.com/en/living-in-germany/housing-mobility/housing-registration",
            "Official guide for finding housing and registration in Germany.",
        ),
        (
            "Visa and residence in Germany",
            "https://www.make-it-in-germany.com/en/visa-residence",
            "Official guide to visa and residence pathways in Germany.",
        ),
    ],
    "Berlin": [
        (
            "Berlin Immigration Office",
            "https://www.berlin.de/einwanderung/en/",
            "Official Berlin immigration office information for residence and employment-related permits.",
        ),
        (
            "Berlin rental cost context",
            "https://investropa.com/blogs/news/average-rent-berlin",
            "Recent Berlin market guide noting that one-bedroom apartments are often around 750 to 1400 EUR per month.",
        ),
    ],
    "Munich": [
        (
            "Munich housing and registration",
            "https://stadt.muenchen.de/en/buergerservice/wohnen-meldewesen.html",
            "Official Munich page for housing, renting, and registration topics.",
        ),
        (
            "Munich rental cost context",
            "https://investropa.com/blogs/news/munich-rents",
            "Recent Munich market guide noting that one-bedroom apartments are often around 850 to 1500 EUR per month.",
        ),
    ],
    "Hamburg": [
        (
            "Hamburg housing stock policy",
            "https://www.hamburg.com/publicservice/info/111034970/",
            "Official Hamburg housing regulation and housing protection information.",
        ),
        (
            "Hamburg rental cost context",
            "https://investropa.com/blogs/news/hamburg-rents",
            "Recent Hamburg market guide noting that one-bedroom apartments are often around 500 to 850 EUR per month.",
        ),
    ],
    "Japan": [
        (
            "Japan visa information",
            "https://www.mofa.go.jp/j_info/visit/visa/index.html",
            "Official Ministry of Foreign Affairs page for Japan visa information.",
        ),
    ],
    "Tokyo": [
        (
            "Tokyo residents information",
            "https://www.english.metro.tokyo.lg.jp/for-residents",
            "Official Tokyo Metropolitan Government information for residents.",
        ),
        (
            "Tokyo rental cost context",
            "https://bambooroutes.com/blogs/news/tokyo-rents",
            "Recent Tokyo market guide noting that one-bedroom apartments are often around 165000 to 230000 JPY per month.",
        ),
    ],
    "Osaka": [
        (
            "Osaka information for foreign students",
            "https://www.city.osaka.lg.jp/contents/wdu020/enjoy/en/content_h.html",
            "Official Osaka city page with accommodation information for foreign students.",
        ),
        (
            "Osaka rental cost context",
            "https://bambooroutes.com/blogs/news/osaka-rents",
            "Recent Osaka market guide noting that one-bedroom apartments are often around 65000 to 135000 JPY per month.",
        ),
    ],
    "Kyoto": [
        (
            "Kyoto living guide for foreign residents",
            "https://www.city.kyoto.lg.jp/sogo/page/0000062673.html",
            "Official Kyoto information page pointing foreign residents to the Kyoto City living guide with housing and visa topics.",
        ),
        (
            "Kyoto rental cost context",
            "https://bambooroutes.com/blogs/news/kyoto-rents",
            "Recent Kyoto market guide noting that one-bedroom apartments are often around 55000 to 100000 JPY per month.",
        ),
    ],
}

CITY_RENT_CONTEXT = {
    "Lisbon": {
        "currency": "EUR",
        "low": 1300,
        "high": 1800,
        "unit": "central Lisbon one-bedroom apartment",
        "source_fragment": "Lisbon rental cost context",
        "note": "",
    },
    "Porto": {
        "currency": "EUR",
        "low": 900,
        "high": 1200,
        "unit": "Porto one-bedroom apartment",
        "source_fragment": "Porto rental cost context",
        "note": "",
    },
    "Faro": {
        "currency": "EUR",
        "low": 750,
        "high": 1150,
        "unit": "Faro-area or Algarve one-bedroom apartment",
        "source_fragment": "Faro rental cost context",
        "note": "This uses Algarve regional rent context as a proxy for Faro.",
    },
    "Berlin": {
        "currency": "EUR",
        "low": 750,
        "high": 1400,
        "unit": "Berlin one-bedroom apartment",
        "source_fragment": "Berlin rental cost context",
        "note": "",
    },
    "Munich": {
        "currency": "EUR",
        "low": 850,
        "high": 1500,
        "unit": "Munich one-bedroom apartment",
        "source_fragment": "Munich rental cost context",
        "note": "",
    },
    "Hamburg": {
        "currency": "EUR",
        "low": 500,
        "high": 850,
        "unit": "Hamburg one-bedroom apartment",
        "source_fragment": "Hamburg rental cost context",
        "note": "",
    },
    "Tokyo": {
        "currency": "JPY",
        "low": 165000,
        "high": 230000,
        "unit": "Tokyo one-bedroom apartment",
        "source_fragment": "Tokyo rental cost context",
        "note": "",
    },
    "Osaka": {
        "currency": "JPY",
        "low": 65000,
        "high": 135000,
        "unit": "Osaka one-bedroom apartment",
        "source_fragment": "Osaka rental cost context",
        "note": "",
    },
    "Kyoto": {
        "currency": "JPY",
        "low": 55000,
        "high": 100000,
        "unit": "Kyoto one-bedroom apartment",
        "source_fragment": "Kyoto rental cost context",
        "note": "",
    },
}

CITY_INFO_SOURCE = {
    "Lisbon": "Lisbon housing information",
    "Berlin": "Berlin Immigration Office",
    "Munich": "Munich housing and registration",
    "Hamburg": "Hamburg housing stock policy",
    "Tokyo": "Tokyo residents information",
    "Osaka": "Osaka information for foreign students",
    "Kyoto": "Kyoto living guide for foreign residents",
}

COUNTRY_SOURCE_FRAGMENTS = {
    "Portugal": ["Portugal visas and residence", "Portugal government services"],
    "Germany": ["Housing and registration in Germany", "Visa and residence in Germany"],
    "Japan": ["Japan visa information"],
}


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str


def load_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as file:
        return file.read()


def load_api_key() -> str:
    return os.getenv("OPENROUTER_API_KEY", "").strip()


def collapse_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    if "duckduckgo.com" in parsed.netloc and parsed.path.startswith("/l/"):
        redirected = parse_qs(parsed.query).get("uddg", [""])[0]
        if redirected:
            return redirected
    if parsed.scheme and parsed.netloc:
        return url
    return ""


def extract_profile_field(question: str, label: str) -> str:
    pattern = rf"{re.escape(label)}:\s*(.+)"
    match = re.search(pattern, question)
    return match.group(1).strip() if match else ""


def extract_budget_amount(question: str) -> float | None:
    budget_line = extract_profile_field(question, "Monthly housing budget")
    match = re.search(r"([\d,.]+)", budget_line)
    if not match:
        return None
    value = match.group(1).replace(",", "")
    try:
        return float(value)
    except ValueError:
        return None


def extract_budget_currency(question: str) -> str:
    budget_line = extract_profile_field(question, "Monthly housing budget")
    match = re.search(r"\b([A-Z]{3})\b", budget_line)
    return match.group(1) if match else ""


def find_source_index(source_meta: list[dict], title_fragment: str) -> int | None:
    fragment = title_fragment.lower()
    for item in source_meta:
        if fragment in item["title"].lower():
            return item["index"]
    return None


def build_affordability_note(city: str, budget_amount: float | None, budget_currency: str, source_meta: list[dict]) -> str:
    context = CITY_RENT_CONTEXT.get(city)
    if not context or budget_amount is None:
        return ""
    if budget_currency != context["currency"]:
        return ""

    source_idx = find_source_index(source_meta, context["source_fragment"])
    if not source_idx:
        return ""

    low = context["low"]
    high = context["high"]
    unit = context["unit"]
    if budget_amount < low:
        verdict = (
            f"At {int(budget_amount)} {budget_currency}/month, this budget looks below the cited range for a {unit} "
            f"of roughly {int(low)} to {int(high)} {budget_currency}, so central or newer options are likely to be above budget [{source_idx}]."
        )
    elif budget_amount <= high:
        verdict = (
            f"At {int(budget_amount)} {budget_currency}/month, this budget is within the cited range for a {unit} "
            f"of roughly {int(low)} to {int(high)} {budget_currency}, but it may still feel tight once deposits, fees, or competition are factored in [{source_idx}]."
        )
    else:
        verdict = (
            f"At {int(budget_amount)} {budget_currency}/month, this budget is above the cited range for a {unit} "
            f"of roughly {int(low)} to {int(high)} {budget_currency}, so you should have more flexibility on size, condition, or location [{source_idx}]."
        )

    if context["note"]:
        verdict += f" {context['note']}"
    return verdict


def build_city_housing_note(city: str, source_meta: list[dict]) -> str:
    title_fragment = CITY_INFO_SOURCE.get(city, "")
    if not title_fragment:
        return ""

    source_idx = find_source_index(source_meta, title_fragment)
    if not source_idx:
        return ""

    city_notes = {
        "Lisbon": f"The Lisbon municipal housing page is a good city-level starting point for local housing information and services [{source_idx}].",
        "Berlin": f"The Berlin immigration office page is a useful city-specific checkpoint for residence and work-permit logistics that can affect housing timing [{source_idx}].",
        "Munich": f"The Munich city page is a useful official starting point for housing, renting, and registration topics [{source_idx}].",
        "Hamburg": f"The Hamburg housing page is a useful official source for local housing regulation and tenant-related issues [{source_idx}].",
        "Tokyo": f"The Tokyo residents page is a useful city-level starting point for local living information relevant to relocation planning [{source_idx}].",
        "Osaka": f"The Osaka city page includes foreign-student accommodation information and is a helpful local starting point for housing research [{source_idx}].",
        "Kyoto": f"The Kyoto living guide source is a helpful city-level starting point for foreign residents planning daily life and housing research [{source_idx}].",
    }
    return city_notes.get(city, "")


def dedupe_results(results: Iterable[SearchResult]) -> list[SearchResult]:
    seen = set()
    unique = []
    for result in results:
        key = result.url
        if not key or key in seen:
            continue
        seen.add(key)
        unique.append(result)
    return unique


def parse_duckduckgo_results(html_text: str, max_results: int) -> list[SearchResult]:
    soup = BeautifulSoup(html_text, "html.parser")
    results = []

    # Preferred selectors for DuckDuckGo HTML pages.
    for node in soup.select(".result, .result.results_links, .web-result"):
        link = node.select_one(".result__title a, .result-link, a[href]")
        snippet_node = node.select_one(".result__snippet, .result-snippet")
        if not link:
            continue
        url = normalize_url(link.get("href", "").strip())
        if not url:
            continue
        title = collapse_whitespace(link.get_text(" ", strip=True))
        snippet = collapse_whitespace(snippet_node.get_text(" ", strip=True)) if snippet_node else ""
        if title:
            results.append(SearchResult(title=title, url=url, snippet=snippet))
        if len(results) >= max_results:
            return dedupe_results(results)

    # Fallback parser for simpler result layouts.
    for link in soup.select("a[href]"):
        url = normalize_url(link.get("href", "").strip())
        title = collapse_whitespace(link.get_text(" ", strip=True))
        if not url or not title:
            continue
        if "duckduckgo.com" in urlparse(url).netloc:
            continue
        if len(title) < 12:
            continue
        results.append(SearchResult(title=title, url=url, snippet=""))
        if len(results) >= max_results:
            break
    return dedupe_results(results)


def http_get(url: str, **kwargs) -> requests.Response:
    return HTTP.get(url, **kwargs)


def http_post(url: str, **kwargs) -> requests.Response:
    return HTTP.post(url, **kwargs)


def search_web(query: str, max_results: int = MAX_SEARCH_RESULTS) -> list[SearchResult]:
    requests_to_try = [
        ("POST", "https://html.duckduckgo.com/html/", {"data": {"q": query}}),
        ("GET", "https://lite.duckduckgo.com/lite/", {"params": {"q": query}}),
    ]

    for method, url, extra in requests_to_try:
        try:
            response = HTTP.request(
                method,
                url,
                headers={"User-Agent": USER_AGENT},
                timeout=REQUEST_TIMEOUT,
                **extra,
            )
            response.raise_for_status()
            results = parse_duckduckgo_results(response.text, max_results=max_results)
            if results:
                return results
        except requests.RequestException:
            continue
    return []


def fetch_page_text(url: str, max_chars: int = MAX_PAGE_CHARS) -> str:
    response = http_get(
        url,
        headers={"User-Agent": USER_AGENT},
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg", "img", "form"]):
        tag.decompose()

    blocks = []
    for node in soup.select("h1, h2, h3, p, li"):
        text = collapse_whitespace(node.get_text(" ", strip=True))
        if len(text) >= 40:
            blocks.append(text)
        if sum(len(block) for block in blocks) >= max_chars:
            break
    return "\n".join(blocks)[:max_chars]


def build_source_context(results: list[SearchResult]) -> tuple[str, list[dict]]:
    contexts = []
    source_meta = []
    for index, result in enumerate(results[:MAX_PAGES], start=1):
        try:
            page_text = fetch_page_text(result.url)
        except Exception as error:
            page_text = f"Unable to fetch page content: {error}"
        source_meta.append(
            {
                "index": index,
                "title": result.title,
                "url": result.url,
            }
        )
        contexts.append(
            "\n".join(
                [
                    f"[{index}] {result.title}",
                    f"URL: {result.url}",
                    f"Search snippet: {result.snippet}",
                    f"Page excerpt: {page_text}",
                ]
            )
        )
    return "\n\n---\n\n".join(contexts), source_meta


def build_messages(question: str, source_context: str) -> list[dict]:
    agent_md = load_text("AGENT.md")
    skill_md = load_text("SKILL.md")
    system_prompt = (
        f"{agent_md}\n\n"
        f"{skill_md}\n\n"
        "Use the numbered sources below as evidence.\n"
        "If the evidence is insufficient, say so instead of guessing.\n\n"
        f"Source excerpts:\n{source_context}"
    )
    user_prompt = (
        f"User question: {question}\n\n"
        "Answer using the required structure from AGENT.md. "
        "Include inline citations like [1]."
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def build_baseline_messages(question: str) -> list[dict]:
    system_prompt = (
        "You are a helpful relocation assistant. "
        "Answer the user's housing-abroad question using general model knowledge only. "
        "Do not claim you checked live sources. "
        "Be transparent about uncertainty and avoid making up exact legal requirements."
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question},
    ]


def call_openrouter(messages: list[dict]) -> str:
    api_key = load_api_key()
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is missing.")

    response = http_post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": MODEL,
            "messages": messages,
            "temperature": 0.2,
        },
        timeout=REQUEST_TIMEOUT,
    )
    if response.status_code == 402:
        raise RuntimeError("OPENROUTER_PAYMENT_REQUIRED")
    response.raise_for_status()

    payload = response.json()
    return payload["choices"][0]["message"]["content"].strip()


def summarize_sources_without_llm(question: str, source_meta: list[dict], source_context: str) -> str:
    bullet_lines = [f"[{item['index']}] {item['title']} - {item['url']}" for item in source_meta]
    country = extract_profile_field(question, "Destination country")
    city = extract_profile_field(question, "Destination city")
    budget_line = extract_profile_field(question, "Monthly housing budget")
    reason = extract_profile_field(question, "Reason for relocating")
    timeline = extract_profile_field(question, "Planned move timeline")
    nationality = extract_profile_field(question, "Nationality or passport")
    concern = extract_profile_field(question, "Specific user concern")
    budget_amount = extract_budget_amount(question)
    budget_currency = extract_budget_currency(question)
    affordability_note = build_affordability_note(city, budget_amount, budget_currency, source_meta)
    city_housing_note = build_city_housing_note(city, source_meta)

    short_answer = (
        f"The research pipeline found relevant {country} and {city} sources, but OpenRouter credits are unavailable, "
        "so this answer is a structured source-based fallback."
    )
    if affordability_note:
        short_answer += " " + affordability_note

    housing_notes = []
    if city_housing_note:
        housing_notes.append(city_housing_note)
    if affordability_note:
        housing_notes.append(affordability_note)
    else:
        housing_notes.append("The currently captured sources do not give a strong city-specific rent range for this case, so affordability still needs separate verification.")
    if "before arriving" in concern.lower():
        housing_notes.append("Because you want to rent before arrival, treat any request for payment before identity, property, and contract verification as high risk.")
    if country == "Germany":
        housing_notes.append("Large German cities are competitive rental markets, so response speed and complete application documents can matter even when a budget is reasonable.")
    if country == "Japan":
        housing_notes.append("Japan rentals often involve extra apartment-specific conditions, so guarantor, key money, and language support still need listing-level confirmation.")
    if country == "Portugal":
        housing_notes.append("Portuguese housing availability can vary sharply by neighborhood and whether the property is aimed at long-term locals or international movers.")

    visa_notes = []
    for fragment in COUNTRY_SOURCE_FRAGMENTS.get(country, []):
        source_idx = find_source_index(source_meta, fragment)
        if not source_idx:
            continue
        if fragment == "Portugal visas and residence":
            visa_notes.append(f"Portugal's government visa and residence page is the official place to confirm the work or study route you need before relying on housing plans [{source_idx}].")
        elif fragment == "Portugal government services":
            visa_notes.append(f"The main Portugal government portal is also useful for follow-on services and appointments once you know the right immigration path [{source_idx}].")
        elif fragment == "Housing and registration in Germany":
            visa_notes.append(f"Germany's official housing and registration guide is a strong baseline source for relocation logistics that can affect when and how you secure housing [{source_idx}].")
        elif fragment == "Visa and residence in Germany":
            visa_notes.append(f"Germany's visa and residence guide is the official place to confirm the residence path linked to your relocation reason [{source_idx}].")
        elif fragment == "Japan visa information":
            visa_notes.append(f"Japan's Ministry of Foreign Affairs visa page is the official place to confirm the visa route tied to your relocation reason before making housing commitments [{source_idx}].")
    if not visa_notes:
        visa_notes.append("No official visa source was captured in this fallback, so immigration details still need checking.")

    risks = [
        "The captured sources do not clearly list the exact landlord document packet for your case, so document requirements still need to be confirmed listing by listing.",
        "The current fallback also does not confirm exact upfront costs such as deposit, advance rent, guarantor needs, agency fees, or move-in charges from a directly applicable official source.",
    ]
    if country == "Japan":
        risks.append("For Japan in particular, key money, guarantor requirements, and agency fees can materially change move-in cost even when monthly rent looks affordable.")
    if country == "Germany":
        risks.append("For Germany, registration timing, furnished versus unfurnished expectations, and proof-of-income expectations can differ across landlords and buildings.")
    if "scam" in concern.lower():
        risks.append("For remote rental searches, avoid sending money until the landlord or agent, property, and written lease terms are verifiable through a trusted platform or official identity details.")

    next_steps = []
    if city_housing_note:
        city_idx = find_source_index(source_meta, CITY_INFO_SOURCE.get(city, ""))
        if city_idx:
            next_steps.append(f"Start with the main {city} source for local housing or relocation context [{city_idx}].")
    for fragment in COUNTRY_SOURCE_FRAGMENTS.get(country, []):
        source_idx = find_source_index(source_meta, fragment)
        if source_idx:
            next_steps.append(f"Confirm your {country} immigration path before committing to a lease timeline [{source_idx}].")
            break
    next_steps.append(f"Use your profile of {nationality}, {reason.lower()}, and {timeline.lower()} to ask landlords or agents for their required document list in writing.")
    next_steps.append("Compare several current listings and verify deposit, first-month rent, contract timing, and any extra move-in charges before paying.")

    sections = [
        "Mode: NestGPT Research",
        "",
        "OpenRouter credits are unavailable right now, so this is a structured research-only fallback instead of a model-written answer.",
        "",
        "Short answer",
        short_answer,
        "",
        "Housing and rental notes",
        *[f"- {line}" for line in housing_notes],
        "",
        "Visa or residency notes",
        *[f"- {line}" for line in visa_notes],
        "",
        "Risks or unknowns",
        *[f"- {line}" for line in risks],
        "",
        "Recommended next steps",
        *[f"- {line}" for line in next_steps],
        "",
        "Sources used:",
        *bullet_lines,
        "",
        "Next step: add OpenRouter credits or switch models if you want a synthesized final recommendation.",
    ]
    return "\n".join(sections)


def answer_question(question: str, search_query: str | None = None) -> str:
    results = search_web(search_query or question)
    if not results:
        country = extract_profile_field(question, "Destination country")
        city = extract_profile_field(question, "Destination city")
        curated = []
        for key in [city, country]:
            for title, url, snippet in CURATED_SOURCES.get(key, []):
                curated.append(SearchResult(title=title, url=url, snippet=snippet))
        results = dedupe_results(curated)
    if not results:
        fallback_query = re.sub(r"\s+", " ", question.replace("\n", " ")).strip()
        return (
            "Mode: NestGPT Research\n\n"
            "I could not find usable search results or curated fallback sources for that request.\n\n"
            f"Search query used: {search_query or fallback_query}\n\n"
            "Try simplifying the question or keeping just the city, country, housing topic, and visa topic."
        )

    source_context, source_meta = build_source_context(results)
    try:
        answer = call_openrouter(build_messages(question, source_context))
    except RuntimeError as error:
        if str(error) == "OPENROUTER_PAYMENT_REQUIRED":
            return summarize_sources_without_llm(question, source_meta, source_context)
        raise

    sources = "\n".join(
        f"[{item['index']}] {item['title']} - {item['url']}"
        for item in source_meta
    )
    return f"{answer}\n\nSources used:\n{sources}"


def build_user_question(form_data: dict) -> str:
    country = str(form_data.get("country", "")).strip()
    city = str(form_data.get("city", "")).strip()
    budget = str(form_data.get("budget", "")).strip()
    currency = str(form_data.get("currency", "")).strip()
    reason = str(form_data.get("reason", "")).strip()
    timeline = str(form_data.get("timeline", "")).strip()
    nationality = str(form_data.get("nationality", "")).strip()
    message = str(form_data.get("message", "")).strip()
    mode = str(form_data.get("mode", "research")).strip()

    prompt_parts = [
        "Create practical relocation guidance using the following user profile.",
        f"Destination country: {country}",
        f"Destination city: {city}",
        f"Monthly housing budget: {budget} {currency}",
        f"Reason for relocating: {reason}",
        f"Planned move timeline: {timeline}",
        f"Nationality or passport: {nationality}",
        f"Requested answer mode: {mode}",
    ]
    if message:
        prompt_parts.append(f"Specific user concern: {message}")
    else:
        prompt_parts.append(
            "Specific user concern: Provide a beginner-friendly overview of housing, rental process, likely costs, visa-related housing issues, and common risks."
        )
    prompt_parts.append(
        "Focus the answer on housing options, likely affordability for the stated budget, documents, process, risks, and relevant visa or residency considerations. "
        "Include a short affordability judgment such as within budget, stretch budget, or likely above budget when the evidence supports it."
    )
    return "\n".join(prompt_parts)


def build_search_query(form_data: dict) -> str:
    country = str(form_data.get("country", "")).strip()
    city = str(form_data.get("city", "")).strip()
    reason = str(form_data.get("reason", "")).strip()
    message = str(form_data.get("message", "")).strip()
    keyword_map = {
        "Work": "rent apartment work visa registration landlord documents",
        "Study": "student housing rent registration landlord documents",
        "Remote work": "rent apartment residence visa remote work landlord documents",
        "Family": "family housing rent residence permit landlord documents",
        "Long-term travel": "temporary housing rent visa landlord documents",
    }
    terms = [city, country, keyword_map.get(reason, "housing rent visa requirements")]
    lowered = message.lower()
    if "scam" in lowered:
        terms.append("rental scam fraud")
    if "document" in lowered:
        terms.append("required documents")
    if "cost" in lowered or "budget" in lowered:
        terms.append("rent deposit upfront costs")
    return " ".join(term for term in terms if term)


def answer_baseline(question: str) -> str:
    answer = call_openrouter(build_baseline_messages(question))
    return (
        "Mode: Baseline AI\n\n"
        f"{answer}\n\n"
        "Note: This answer is generated without live retrieval, so it may miss recent or location-specific changes."
    )


def answer_research(question: str, search_query: str | None = None) -> str:
    answer = answer_question(question, search_query=search_query)
    if answer.startswith("Mode: "):
        return answer
    return f"Mode: NestGPT Research\n\n{answer}"


def route_answer(form_data: dict) -> str:
    question = build_user_question(form_data)
    mode = str(form_data.get("mode", "research")).strip().lower()
    if mode == "baseline":
        return answer_baseline(question)
    return answer_research(question, build_search_query(form_data))


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path != "/":
            self.send_error(404)
            return
        body = HTML.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        if self.path != "/ask":
            self.send_error(404)
            return

        length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(length)
        try:
            data = json.loads(raw_body.decode("utf-8"))
        except json.JSONDecodeError:
            self._send_json(400, {"error": "Invalid JSON."})
            return

        required_fields = ["country", "city", "budget", "currency", "reason", "timeline", "nationality", "mode"]
        missing = [field for field in required_fields if not str(data.get(field, "")).strip()]
        if missing:
            self._send_json(400, {"error": f"Missing required fields: {', '.join(missing)}"})
            return

        try:
            output = route_answer(data)
            self._send_json(200, {"output": output})
        except Exception as error:
            self._send_json(500, {"error": str(error)})

    def log_message(self, format: str, *args) -> None:
        return


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Serving http://{HOST}:{PORT}")
    server.serve_forever()
