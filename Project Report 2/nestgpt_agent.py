import json
import os
import re
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
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
DATASET_DIR = Path("datasets")
MAX_DATASET_RECORDS = 6

HTML = Path("app_template.html").read_text(encoding="utf-8")


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
            "https://investropa.com/blogs/news/lisbon-rents",
            "Recent Lisbon market guide noting that one-bedroom apartments are often around 1300 to 1800 EUR per month.",
        ),
        (
            "Lisbon purchase cost context",
            "https://investropa.com/blogs/news/lisbon-property-market-overpriced-2025",
            "Recent Lisbon market guide with townhouse and villa purchase benchmarks.",
        ),
    ],
    "Porto": [
        (
            "Porto rental cost context",
            "https://investropa.com/blogs/news/average-rent-porto",
            "Recent Porto market guide noting that one-bedroom apartments are often around 900 to 1200 EUR per month.",
        ),
        (
            "Porto purchase cost context",
            "https://investropa.com/blogs/news/average-house-price-porto-portugal",
            "Recent Porto market guide with townhouse and detached-house purchase benchmarks.",
        ),
    ],
    "Faro": [
        (
            "Faro rental cost context",
            "https://investropa.com/blogs/news/algarve-rents",
            "Recent Algarve market guide noting that one-bedroom apartments often fall around 750 to 1150 EUR per month, used here as a Faro-area proxy.",
        ),
        (
            "Faro purchase cost context",
            "https://investropa.com/blogs/news/algarve-housing-prices",
            "Recent Algarve market guide with townhouse and detached-house purchase benchmarks, used here as a Faro-area proxy.",
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
        (
            "Berlin purchase cost context",
            "https://investropa.com/blogs/news/average-house-price-berlin",
            "Recent Berlin market guide with townhouse and house purchase benchmarks.",
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
        (
            "Munich purchase cost context",
            "https://investropa.com/blogs/news/munich-price-forecasts",
            "Recent Munich market guide with family-house purchase benchmarks.",
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
        (
            "Hamburg purchase cost context",
            "https://investropa.com/blogs/news/hamburg-housing-prices",
            "Recent Hamburg market guide with house purchase benchmarks.",
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
        (
            "Tokyo purchase cost context",
            "https://bambooroutes.com/blogs/news/average-property-price-tokyo",
            "Recent Tokyo market guide with detached-house purchase benchmarks.",
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
        (
            "Osaka purchase cost context",
            "https://bambooroutes.com/blogs/news/average-price-per-sqm-osaka",
            "Recent Osaka market guide with city-home and detached-house purchase context.",
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
        (
            "Kyoto purchase cost context",
            "https://bambooroutes.com/blogs/news/how-much-property-kyoto",
            "Recent Kyoto market guide with detached-house purchase benchmarks.",
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


@dataclass
class DatasetEvidence:
    name: str
    source: str
    source_url: str
    license: str
    description: str
    dataset_type: str
    market_type: str
    preprocessing: list[str]
    records: list[dict]


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


def load_json(path: Path) -> dict | list:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def stringify_dataset_record(record: dict) -> str:
    pairs = []
    for key, value in record.items():
        if str(key).startswith("example_listing_"):
            continue
        if value in ("", None, [], {}):
            continue
        label = str(key).replace("_", " ").strip()
        text = collapse_whitespace(str(value))
        if not text:
            continue
        pairs.append(f"{label}: {text}")
    return "; ".join(pairs)


def parse_float(value: object) -> float | None:
    if value in ("", None):
        return None
    try:
        return float(str(value).replace(",", "").strip())
    except ValueError:
        return None


def detect_question_intent(question: str) -> str:
    concern = extract_profile_field(question, "Specific user concern")
    text = concern if concern else question
    lowered = text.lower()
    purchase_terms = [
        "buy",
        "purchase",
        "property",
        "real estate",
        "transaction",
        "home price",
        "sale price",
        "buying",
    ]
    rental_terms = [
        "rent",
        "rental",
        "lease",
        "landlord",
        "apartment",
        "deposit",
        "move in",
    ]
    purchase_score = sum(1 for term in purchase_terms if term in lowered)
    rental_score = sum(1 for term in rental_terms if term in lowered)
    if purchase_score > rental_score:
        return "purchase"
    return "rental"


def summarize_dataset_evidence(
    question: str,
    city: str,
    budget_amount: float | None,
    budget_currency: str,
    source_meta: list[dict],
) -> tuple[list[str], list[str], list[str]]:
    housing_notes = []
    cost_notes = []
    risk_notes = []
    intent = detect_question_intent(question)

    for item in source_meta:
        if item.get("kind") != "dataset":
            continue

        records = item.get("records", [])
        if not isinstance(records, list) or not records:
            continue

        source_idx = item["index"]
        sale_prices = [price for price in (parse_float(record.get("sale_price_eur")) for record in records) if price is not None]
        trade_prices_jpy = [price for price in (parse_float(record.get("trade_price_jpy")) for record in records) if price is not None]
        rent_prices = [price for price in (parse_float(record.get("monthly_rent_eur")) for record in records) if price is not None]
        rent_prices_jpy = [price for price in (parse_float(record.get("monthly_rent_jpy")) for record in records) if price is not None]
        total_rent_prices = [price for price in (parse_float(record.get("total_rent_eur")) for record in records) if price is not None]
        base_rent_prices = [price for price in (parse_float(record.get("base_rent_eur")) for record in records) if price is not None]
        matching_records = []
        for record in records:
            record_city = collapse_whitespace(str(record.get("supported_city", "") or record.get("city", "")))
            if not record_city or record_city.lower() == city.lower():
                matching_records.append(record)

        if sale_prices:
            low = int(min(sale_prices))
            high = int(max(sale_prices))
            if intent == "purchase":
                housing_notes.append(
                    f"The sampled property-sale records for {city} span roughly {low} to {high} EUR, so the dataset suggests a wide purchase market depending on neighborhood and property size [{source_idx}]."
                )
                cost_notes.append(
                    f"In the local dataset slice, observed sale prices for {city} examples ranged from about {low} to {high} EUR [{source_idx}]."
                )
            else:
                risk_notes.append(
                    f"This dataset appears to reflect sale listings rather than rentals, so it should be used for purchase context only and not as direct evidence for monthly rent [{source_idx}]."
                )

        if trade_prices_jpy:
            low = int(min(trade_prices_jpy))
            high = int(max(trade_prices_jpy))
            if intent == "purchase":
                housing_notes.append(
                    f"The sampled property transaction records for {city} span roughly {low} to {high} JPY, which suggests a wide purchase market depending on size, building age, and sub-area [{source_idx}]."
                )
                cost_notes.append(
                    f"In the local dataset slice, observed property transaction prices for {city} examples ranged from about {low} to {high} JPY [{source_idx}]."
                )
            else:
                risk_notes.append(
                    f"This dataset reflects property transaction prices rather than monthly rent, so it should inform purchase context only and not direct rental budgeting [{source_idx}]."
                )

        if rent_prices:
            low = int(min(rent_prices))
            high = int(max(rent_prices))
            if intent == "rental":
                housing_notes.append(
                    f"The sampled rental records for {city} span roughly {low} to {high} {budget_currency or 'EUR'} in the local open dataset [{source_idx}]."
                )
                if budget_amount is not None and budget_currency == "EUR":
                    if budget_amount < low:
                        cost_notes.append(
                            f"Compared with the matched dataset records, a budget of {int(budget_amount)} EUR/month sits below the sampled range of about {low} to {high} EUR/month [{source_idx}]."
                        )
                    elif budget_amount > high:
                        cost_notes.append(
                            f"Compared with the matched dataset records, a budget of {int(budget_amount)} EUR/month sits above the sampled range of about {low} to {high} EUR/month [{source_idx}]."
                        )
                    else:
                        cost_notes.append(
                            f"Compared with the matched dataset records, a budget of {int(budget_amount)} EUR/month falls within the sampled range of about {low} to {high} EUR/month [{source_idx}]."
                        )
            else:
                risk_notes.append(
                    f"This dataset reflects rental prices rather than purchase prices, so it should be used for lease planning and not direct property valuation [{source_idx}]."
                )

        if rent_prices_jpy:
            low = int(min(rent_prices_jpy))
            high = int(max(rent_prices_jpy))
            if intent == "rental":
                housing_notes.append(
                    f"The sampled apartment-rental records for {city} span roughly {low} to {high} JPY/month in the local dataset [{source_idx}]."
                )
                if budget_amount is not None and budget_currency == "JPY":
                    if budget_amount < low:
                        cost_notes.append(
                            f"Compared with the matched dataset records, a budget of {int(budget_amount)} JPY/month sits below the sampled range of about {low} to {high} JPY/month [{source_idx}]."
                        )
                    elif budget_amount > high:
                        cost_notes.append(
                            f"Compared with the matched dataset records, a budget of {int(budget_amount)} JPY/month sits above the sampled range of about {low} to {high} JPY/month [{source_idx}]."
                        )
                    else:
                        cost_notes.append(
                            f"Compared with the matched dataset records, a budget of {int(budget_amount)} JPY/month falls within the sampled range of about {low} to {high} JPY/month [{source_idx}]."
                        )
            else:
                risk_notes.append(
                    f"This dataset reflects apartment rents rather than house purchase prices, so it should be used for leasing context only [{source_idx}]."
                )

        if total_rent_prices or base_rent_prices:
            observed_prices = total_rent_prices or base_rent_prices
            low = int(min(observed_prices))
            high = int(max(observed_prices))
            price_label = "total rent" if total_rent_prices else "base rent"
            if intent == "rental":
                housing_notes.append(
                    f"The sampled rental records for {city} show {price_label} values roughly between {low} and {high} EUR in the local open dataset [{source_idx}]."
                )
                if budget_amount is not None and budget_currency == "EUR":
                    if budget_amount < low:
                        cost_notes.append(
                            f"Compared with the matched dataset records, a budget of {int(budget_amount)} EUR/month sits below the sampled {price_label} range of about {low} to {high} EUR/month [{source_idx}]."
                        )
                    elif budget_amount > high:
                        cost_notes.append(
                            f"Compared with the matched dataset records, a budget of {int(budget_amount)} EUR/month sits above the sampled {price_label} range of about {low} to {high} EUR/month [{source_idx}]."
                        )
                    else:
                        cost_notes.append(
                            f"Compared with the matched dataset records, a budget of {int(budget_amount)} EUR/month falls within the sampled {price_label} range of about {low} to {high} EUR/month [{source_idx}]."
                        )
            else:
                risk_notes.append(
                    f"This dataset reflects rental prices rather than purchase prices, so it should be used for lease planning and not direct property valuation [{source_idx}]."
                )

        sample_line = stringify_dataset_record(matching_records[0] if matching_records else records[0])
        if sample_line and (
            (intent == "purchase" and (sale_prices or trade_prices_jpy))
            or (intent == "rental" and (rent_prices or total_rent_prices or base_rent_prices))
        ):
            housing_notes.append(f"One representative dataset row looks like: {sample_line} [{source_idx}].")

    return housing_notes, cost_notes, risk_notes


def dataset_matches(manifest: dict, country: str, city: str, question: str) -> bool:
    lowered_question = question.lower()
    intent = detect_question_intent(question)
    countries = [str(item).strip().lower() for item in manifest.get("countries", []) if str(item).strip()]
    cities = [str(item).strip().lower() for item in manifest.get("cities", []) if str(item).strip()]
    keywords = [str(item).strip().lower() for item in manifest.get("keywords", []) if str(item).strip()]
    dataset_type = collapse_whitespace(str(manifest.get("dataset_type", "")).lower())
    market_type = collapse_whitespace(str(manifest.get("market_type", "")).lower())

    if countries and country.lower() not in countries:
        return False
    if cities and city.lower() not in cities:
        return False
    if dataset_type and dataset_type != intent:
        return False
    if intent == "rental" and market_type in {"sale", "transaction", "purchase"}:
        return False
    if intent == "purchase" and market_type in {"rent", "rental", "lease"}:
        return False
    if keywords:
        normalized_question = re.sub(r"[^a-z0-9]+", " ", lowered_question)
        normalized_keywords = [re.sub(r"[^a-z0-9]+", " ", keyword).strip() for keyword in keywords]
        if not any(keyword and keyword in normalized_question for keyword in normalized_keywords):
            return False
    return True


def load_open_datasets(question: str, country: str, city: str) -> list[DatasetEvidence]:
    if not DATASET_DIR.exists():
        return []

    datasets = []
    for manifest_path in sorted(DATASET_DIR.glob("*.dataset.json")):
        try:
            manifest = load_json(manifest_path)
        except Exception:
            continue

        if not isinstance(manifest, dict):
            continue
        if not dataset_matches(manifest, country, city, question):
            continue

        raw_records = manifest.get("records")
        if raw_records is None:
            data_file = str(manifest.get("data_file", "")).strip()
            if not data_file:
                continue
            try:
                raw_records = load_json(manifest_path.parent / data_file)
            except Exception:
                continue

        if isinstance(raw_records, dict):
            raw_records = raw_records.get("records", [])
        if not isinstance(raw_records, list):
            continue

        filtered_records = []
        for item in raw_records:
            if not isinstance(item, dict):
                continue
            record_city = collapse_whitespace(str(item.get("supported_city", "") or item.get("city", "")))
            if record_city and record_city.lower() != city.lower():
                continue
            filtered_records.append(item)
        records = filtered_records[:MAX_DATASET_RECORDS]
        if not records:
            continue

        datasets.append(
            DatasetEvidence(
                name=str(manifest.get("name", manifest_path.stem)).strip(),
                source=str(manifest.get("source", "Open dataset")).strip(),
                source_url=str(manifest.get("source_url", "")).strip(),
                license=str(manifest.get("license", "Unknown")).strip(),
                description=str(manifest.get("description", "")).strip(),
                dataset_type=str(manifest.get("dataset_type", "")).strip(),
                market_type=str(manifest.get("market_type", "")).strip(),
                preprocessing=[
                    collapse_whitespace(str(step))
                    for step in manifest.get("preprocessing", [])
                    if collapse_whitespace(str(step))
                ],
                records=records,
            )
        )
    return datasets


def find_source_index(source_meta: list[dict], title_fragment: str) -> int | None:
    fragment = title_fragment.lower()
    for item in source_meta:
        if fragment in item["title"].lower():
            return item["index"]
    return None


def extract_dataset_upstream_sources(records: list[dict]) -> list[tuple[str, str]]:
    seen = set()
    upstream = []
    for record in records:
        if not isinstance(record, dict):
            continue
        name = collapse_whitespace(str(record.get("source_name", "")))
        url = collapse_whitespace(str(record.get("source_url", "")))
        if not name or not url:
            continue
        key = (name.lower(), url.lower())
        if key in seen:
            continue
        seen.add(key)
        upstream.append((name, url))
    return upstream


def format_dataset_source_line(item: dict) -> str:
    upstream = item.get("upstream_sources", [])
    upstream_text = "; ".join(f"{name} - {url}" for name, url in upstream) if upstream else "No upstream benchmark links documented"
    return (
        f"[{item['index']}] {item['title']} - local curated benchmark dataset; "
        f"origin: {item.get('source', 'Open dataset')}; "
        f"license: {item.get('license', 'Unknown')}; "
        f"dataset type: {item.get('dataset_type', 'Unknown')}; "
        f"market type: {item.get('market_type', 'Unknown')}; "
        f"built from: {upstream_text}; "
        f"preprocessing: {'; '.join(item.get('preprocessing', [])) if item.get('preprocessing') else 'None documented'}"
    )


def extract_real_listing(record: dict) -> dict | None:
    if not isinstance(record, dict):
        return None
    title = collapse_whitespace(str(record.get("real_listing_title", "")))
    url = collapse_whitespace(str(record.get("real_listing_url", "")))
    if not title or not url:
        return None
    listing = {
        "title": title,
        "neighborhood": collapse_whitespace(str(record.get("real_listing_neighborhood", ""))),
        "url": url,
        "reference_type": collapse_whitespace(str(record.get("real_listing_reference_type", ""))),
        "retrieved_on": collapse_whitespace(str(record.get("real_listing_retrieved_on", ""))),
    }
    if record.get("real_listing_monthly_rent_eur") not in ("", None):
        listing["price"] = f"{record.get('real_listing_monthly_rent_eur')} EUR/month"
    elif record.get("real_listing_monthly_rent_jpy") not in ("", None):
        listing["price"] = f"{record.get('real_listing_monthly_rent_jpy')} JPY/month"
    elif record.get("real_listing_sale_price_eur") not in ("", None):
        listing["price"] = f"{record.get('real_listing_sale_price_eur')} EUR"
    elif record.get("real_listing_trade_price_jpy") not in ("", None):
        listing["price"] = f"{record.get('real_listing_trade_price_jpy')} JPY"
    else:
        listing["price"] = ""
    size = record.get("real_listing_size_m2")
    listing["size"] = f"{size} m2" if size not in ("", None) else ""
    return listing


def select_real_listing(form_data: dict) -> dict | None:
    country = str(form_data.get("country", "")).strip()
    city = str(form_data.get("city", "")).strip()
    question = build_user_question(form_data)
    datasets = load_open_datasets(question, country, city)
    for dataset in datasets:
        for record in dataset.records:
            listing = extract_real_listing(record)
            if listing:
                return listing
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


def build_source_context(results: list[SearchResult], datasets: list[DatasetEvidence]) -> tuple[str, list[dict]]:
    contexts = []
    source_meta = []
    index = 1
    for result in results[:MAX_PAGES]:
        try:
            page_text = fetch_page_text(result.url)
        except Exception as error:
            page_text = f"Unable to fetch page content: {error}"
        source_meta.append(
            {
                "index": index,
                "title": result.title,
                "url": result.url,
                "kind": "web",
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
        index += 1

    for dataset in datasets:
        source_meta.append(
            {
                "index": index,
                "title": dataset.name,
                "url": dataset.source_url,
                "kind": "dataset",
                "source": dataset.source,
                "license": dataset.license,
                "dataset_type": dataset.dataset_type,
                "market_type": dataset.market_type,
                "preprocessing": dataset.preprocessing,
                "records": dataset.records,
                "upstream_sources": extract_dataset_upstream_sources(dataset.records),
            }
        )
        record_lines = [f"- {stringify_dataset_record(record)}" for record in dataset.records if stringify_dataset_record(record)]
        contexts.append(
            "\n".join(
                [
                    f"[{index}] {dataset.name}",
                    f"Dataset origin: {dataset.source}",
                    f"Source URL: {dataset.source_url or 'Not provided'}",
                    f"License: {dataset.license}",
                    f"Dataset type: {dataset.dataset_type or 'Not provided'}",
                    f"Market type: {dataset.market_type or 'Not provided'}",
                    f"Description: {dataset.description or 'No description provided.'}",
                    f"Preprocessing: {'; '.join(dataset.preprocessing) if dataset.preprocessing else 'None documented.'}",
                    "Sample records:",
                    *(record_lines or ["- No sample records available."]),
                ]
            )
        )
        index += 1
    return "\n\n---\n\n".join(contexts), source_meta


def build_messages(question: str, source_context: str) -> list[dict]:
    agent_md = load_text("AGENT.md")
    skill_md = load_text("SKILL.md")
    concern = extract_profile_field(question, "Specific user concern")
    system_prompt = (
        f"{agent_md}\n\n"
        f"{skill_md}\n\n"
        "Use the numbered sources below as evidence.\n"
        "If the evidence is insufficient, say so instead of guessing.\n\n"
        "Prioritize answering the user's specific concern directly before giving any broader context.\n"
        "If the user asked a narrow question, keep the response narrow and practical.\n\n"
        "If any source is an open dataset, explicitly document its origin, license, and any preprocessing notes when you rely on it.\n\n"
        f"Source excerpts:\n{source_context}"
    )
    user_prompt = (
        f"User question: {question}\n\n"
        f"Primary concern to answer first: {concern or 'Provide the most direct answer supported by the sources.'}\n\n"
        "Answer using the required structure from AGENT.md. "
        "Lead with a direct answer to the primary concern, then include only the supporting sections that are necessary. "
        "Include inline citations like [1]."
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def build_baseline_messages(question: str) -> list[dict]:
    concern = extract_profile_field(question, "Specific user concern")
    system_prompt = (
        "You are a helpful relocation assistant. "
        "Answer the user's housing-abroad question using general model knowledge only. "
        "Do not claim you checked live sources. "
        "Be transparent about uncertainty and avoid making up exact legal requirements. "
        "Start with a direct answer to the user's main concern and avoid turning narrow questions into broad overviews."
    )
    return [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": (
                f"{question}\n\n"
                f"Primary concern to answer first: {concern or 'Answer the most specific question in the profile directly.'}"
            ),
        },
    ]


def extract_openrouter_error(response: requests.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        text = response.text.strip()
        return text or f"HTTP {response.status_code}"

    if isinstance(payload, dict):
        error = payload.get("error")
        if isinstance(error, dict):
            message = error.get("message") or error.get("metadata", {}).get("raw")
            if message:
                return str(message)
        message = payload.get("message")
        if message:
            return str(message)

    return json.dumps(payload)


def model_uses_fixed_temperature(model: str) -> bool:
    normalized = model.strip().lower()
    return normalized.startswith("openai/gpt-5")


def call_openrouter(messages: list[dict]) -> str:
    api_key = load_api_key()
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is missing.")

    payload = {
        "model": MODEL,
        "messages": messages,
    }
    if not model_uses_fixed_temperature(MODEL):
        payload["temperature"] = 0.2

    response = http_post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": f"http://{HOST}:{PORT}",
            "X-Title": "NestGPT",
        },
        json=payload,
        timeout=REQUEST_TIMEOUT,
    )
    if response.status_code == 402:
        raise RuntimeError("OPENROUTER_PAYMENT_REQUIRED")
    if not response.ok:
        detail = extract_openrouter_error(response)
        raise RuntimeError(f"OpenRouter error {response.status_code}: {detail}")

    payload = response.json()
    content = payload["choices"][0]["message"]["content"]
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        text_parts = [
            part.get("text", "")
            for part in content
            if isinstance(part, dict) and part.get("type") == "text"
        ]
        return "\n".join(part for part in text_parts if part).strip()
    return str(content).strip()


def summarize_sources_without_llm(question: str, source_meta: list[dict], source_context: str) -> str:
    bullet_lines = []
    dataset_lines = []
    for item in source_meta:
        if item.get("kind") == "dataset":
            dataset_lines.append(format_dataset_source_line(item))
        else:
            bullet_lines.append(f"[{item['index']}] {item['title']} - {item['url']}")
    country = extract_profile_field(question, "Destination country")
    city = extract_profile_field(question, "Destination city")
    reason = extract_profile_field(question, "Reason for relocating")
    timeline = extract_profile_field(question, "Planned move timeline")
    nationality = extract_profile_field(question, "Nationality or passport")
    concern = extract_profile_field(question, "Specific user concern")
    budget_amount = extract_budget_amount(question)
    budget_currency = extract_budget_currency(question)
    intent = detect_question_intent(question)
    affordability_note = build_affordability_note(city, budget_amount, budget_currency, source_meta)
    city_housing_note = build_city_housing_note(city, source_meta)
    dataset_housing_notes, dataset_cost_notes, dataset_risk_notes = summarize_dataset_evidence(
        question, city, budget_amount, budget_currency, source_meta
    )
    lowered_concern = concern.lower()

    asks_documents = any(term in lowered_concern for term in ["document", "documents", "paperwork", "landlord ask", "application"])
    asks_scams = any(term in lowered_concern for term in ["scam", "scams", "fraud", "fake", "deposit"])
    asks_pre_arrival = any(term in lowered_concern for term in ["before i arrive", "before arrival", "before arriving", "pre-arrival", "pre arrival"])
    asks_visa = any(term in lowered_concern for term in ["visa", "residence", "permit", "registration", "register", "immigration"])

    direct_answer_parts = []
    if asks_visa:
        direct_answer_parts.append(
            "The most likely steps to slow down your housing search are the visa or residence path you qualify for and any registration step that affects when you can fully settle or document your stay."
        )
        direct_answer_parts.append(
            "The best preparation is to confirm your immigration route early, gather the identity and status documents you can already prove, and avoid timing a lease around assumptions that are not yet confirmed."
        )
    elif asks_documents or asks_scams or asks_pre_arrival:
        direct_answer_parts.append(
            "The safest source-backed answer is that you should expect landlords or agents to ask for identity, income, and immigration-related paperwork, but the exact packet still varies by listing and needs to be confirmed directly."
        )
        if asks_scams or asks_pre_arrival:
            direct_answer_parts.append(
                "Because you want to rent before arrival, the main risk is paying too early for a property or sender you have not fully verified."
            )
    elif intent == "rental" and affordability_note:
        direct_answer_parts.append(affordability_note)
    elif intent == "rental":
        direct_answer_parts.append(
            f"The captured sources support a cautious rental plan for {city}, but they do not give enough evidence for a precise budget judgment yet."
        )
    else:
        direct_answer_parts.append(
            f"The captured sources give some useful context for {city}, but key details still need local verification."
        )
    if "neighborhood" in lowered_concern:
        direct_answer_parts.append(
            f"The current sources do not support neighborhood-by-neighborhood recommendations for {city}, so the safest conclusion is to expect flexibility on exact area rather than a precise district callout."
        )
    if "30 days" in lowered_concern or "first 30 days" in lowered_concern:
        direct_answer_parts.append(
            "Your first month should focus on landing temporary housing if needed, verifying your document checklist, and moving quickly on legitimate listings rather than trying to perfect the search on day one."
        )
    short_answer = " ".join(direct_answer_parts)

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
    what_matters = []
    if asks_visa:
        if visa_notes:
            what_matters.extend(visa_notes[:2])
        what_matters.append("Housing timing can slip if you start applying before you know which status, documents, or local registration steps landlords may expect you to show.")
    elif asks_documents or asks_scams or asks_pre_arrival:
        what_matters.append("Expect some version of passport or ID, proof of income or financial support, and visa or residence-related documentation, but confirm the exact checklist with each landlord or agent.")
        if visa_notes:
            what_matters.append(visa_notes[0])
        if asks_scams or asks_pre_arrival:
            what_matters.append("Treat any request for money before identity, property access, and lease details are verified as a red flag.")
    elif city_housing_note:
        what_matters.append(city_housing_note)
    if dataset_cost_notes and not (asks_documents or asks_scams or asks_pre_arrival):
        what_matters.append(dataset_cost_notes[0])
    if country == "Germany" and intent == "rental" and not (asks_documents or asks_scams or asks_pre_arrival):
        what_matters.append("Berlin rentals move quickly, so complete documents and fast replies matter even when your budget is workable.")
    if asks_scams:
        what_matters.append("Do not send money until the landlord, property, and written lease terms are verifiable.")
    if not what_matters and dataset_housing_notes:
        what_matters.append(dataset_housing_notes[0])

    next_steps = []
    if asks_visa:
        next_steps.append("Confirm your visa or residence route before you anchor your housing timeline to a specific move-in plan.")
        next_steps.append("Gather the identity, income, and immigration documents you can already prove so you can respond quickly once landlords ask for them.")
        if visa_notes:
            next_steps.append(visa_notes[0])
    elif asks_documents or asks_scams or asks_pre_arrival:
        next_steps.append("Ask each landlord or agent for their exact required document list in writing before you apply or pay anything.")
        next_steps.append("Verify the property, the sender, and the lease terms before sending a deposit, especially if you have not seen the place in person.")
        if visa_notes:
            next_steps.append(visa_notes[0])
    elif "30 days" in lowered_concern or "first 30 days" in lowered_concern:
        next_steps.append("Week 1: confirm your visa or registration path and gather the landlord documents you can already prove.")
        next_steps.append("Weeks 1-2: line up temporary housing or viewings so you are not forced into a rushed long-term lease.")
        next_steps.append("Weeks 2-4: compare real listings, confirm upfront costs in writing, and move quickly on verified options.")
    else:
        next_steps.append(f"Use your profile of {nationality}, {reason.lower()}, and {timeline.lower()} to ask landlords or agents for their required document list in writing.")
        next_steps.append("Compare several current listings and verify deposit, first-month rent, contract timing, and extra move-in charges before paying.")
    if visa_notes:
        next_steps.append(visa_notes[0])

    watch_out = []
    if intent == "rental":
        if asks_visa:
            watch_out.append("The captured sources do not confirm one exact delay point for your case, so do not assume every landlord or office will treat visa and registration timing the same way.")
            watch_out.append("If your move depends on work authorization, residence approval, or local registration timing, build slack into your housing plan.")
        elif asks_documents or asks_scams or asks_pre_arrival:
            watch_out.append("The captured sources do not confirm one universal landlord document packet, so do not assume the first checklist you see applies everywhere.")
            watch_out.append("Upfront costs, deposit timing, guarantor requirements, and agency fees still need to be checked before you commit.")
        else:
            watch_out.append("The captured sources do not confirm the exact landlord document packet for your case, so verify requirements listing by listing.")
            watch_out.append("Upfront costs such as deposit, agency fees, guarantor needs, and furnished versus unfurnished expectations still need to be checked.")
    if dataset_risk_notes:
        watch_out.append(dataset_risk_notes[0])

    sections = [
        "Mode: NestGPT Research",
        "",
        "OpenRouter credits are unavailable right now, so this is a short research-only fallback.",
        "",
        "Direct answer",
        short_answer,
        *(["", "What matters most", *[f"- {line}" for line in what_matters[:3]]] if what_matters else []),
        *(["", "Realistic next steps", *[f"- {line}" for line in next_steps[:3]]] if next_steps else []),
        *(["", "Watch-outs", *[f"- {line}" for line in watch_out[:2]]] if watch_out else []),
        "",
        "Recommended next steps",
        "- Add OpenRouter credits if you want a fuller synthesized answer instead of the compact fallback.",
        "",
        "Sources used:",
        *bullet_lines[:4],
        *dataset_lines[:2],
    ]
    return "\n".join(sections)


def answer_question(question: str, search_query: str | None = None) -> str:
    country = extract_profile_field(question, "Destination country")
    city = extract_profile_field(question, "Destination city")
    results = search_web(search_query or question)
    if not results:
        curated = []
        for key in [city, country]:
            for title, url, snippet in CURATED_SOURCES.get(key, []):
                curated.append(SearchResult(title=title, url=url, snippet=snippet))
        results = dedupe_results(curated)
    datasets = load_open_datasets(question, country, city)
    if not results and not datasets:
        fallback_query = re.sub(r"\s+", " ", question.replace("\n", " ")).strip()
        return (
            "Mode: NestGPT Research\n\n"
            "I could not find usable search results, curated fallback sources, or matching local open datasets for that request.\n\n"
            f"Search query used: {search_query or fallback_query}\n\n"
            "Try simplifying the question or keeping just the city, country, housing topic, and visa topic."
        )

    source_context, source_meta = build_source_context(results, datasets)
    try:
        answer = call_openrouter(build_messages(question, source_context))
    except RuntimeError as error:
        if str(error) == "OPENROUTER_PAYMENT_REQUIRED":
            return summarize_sources_without_llm(question, source_meta, source_context)
        raise

    source_lines = []
    dataset_lines = []
    for item in source_meta:
        if item.get("kind") == "dataset":
            dataset_lines.append(format_dataset_source_line(item))
        else:
            source_lines.append(f"[{item['index']}] {item['title']} - {item['url']}")
    combined_sources = "\n".join(source_lines + dataset_lines)
    suffix = f"{answer}\n\nSources used:\n{combined_sources}" if combined_sources else f"{answer}\n\nSources used:\nNone"
    return suffix


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
        "Answer the user's specific relocation question directly using the following user profile.",
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
        "First, answer the specific user concern as directly as possible. "
        "Then include only the most relevant housing options, affordability guidance, document requirements, risks, and visa or residency considerations needed to support that answer. "
        "For rental questions, use long-term apartment-rental evidence only unless the user explicitly asks for a different rental type. "
        "Do not answer rental questions with house rentals, room shares, whole-building listings, serviced stays, or hotel-style inventory. "
        "For purchase questions, use individual house, townhouse, or detached-home purchase evidence only. "
        "Do not answer purchase questions with apartment purchases, whole-building deals, commercial property, or large land-only transactions. "
        "Do not turn a narrow question into a full relocation overview unless the user asked for one. "
        "Include a short affordability judgment such as within budget, stretch budget, or likely above budget when the evidence supports it."
    )
    return "\n".join(prompt_parts)


def build_search_query(form_data: dict) -> str:
    country = str(form_data.get("country", "")).strip()
    city = str(form_data.get("city", "")).strip()
    reason = str(form_data.get("reason", "")).strip()
    message = str(form_data.get("message", "")).strip()
    keyword_map = {
        "Work": "rent apartment long term work visa registration landlord documents",
        "Study": "student apartment rent registration landlord documents",
        "Remote work": "rent apartment long term residence visa remote work landlord documents",
        "Family": "family apartment rent residence permit landlord documents",
        "Long-term travel": "long term apartment rent visa landlord documents",
    }
    terms = [city, country, keyword_map.get(reason, "long term apartment rent visa requirements")]
    lowered = message.lower()
    purchase_terms = ["buy", "purchase", "house", "home", "for sale"]
    if any(term in lowered for term in purchase_terms):
        terms = [city, country, "buy detached house townhouse single family home residential prices transaction costs"]
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
        if self.path == "/logo.png":
            logo_path = Path("NestGPT-Logo.png")
            if not logo_path.exists():
                self.send_error(404)
                return
            body = logo_path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
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
            self._send_json(200, {"output": output, "listing": select_real_listing(data)})
        except Exception as error:
            self._send_json(500, {"error": str(error)})

    def log_message(self, format: str, *args) -> None:
        return


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Serving http://{HOST}:{PORT}")
    server.serve_forever()
