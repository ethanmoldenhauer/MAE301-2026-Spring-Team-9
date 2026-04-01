#!/usr/bin/env python3
"""
NestGPT MVP App

A single-file AI relocation assistant prototype inspired by the NestGPT presentation.
This app focuses on a small set of countries and demonstrates an AI agent that can:

- answer housing questions
- explain rental rules and visa basics for supported countries
- estimate living costs from a local knowledge base
- help draft landlord messages
- generate a step-by-step relocation checklist

Designed as a course-project MVP: concrete, runnable, and easy to extend.

Requirements
------------
pip install streamlit openai

Environment
-----------
export OPENROUTER_API_KEY=your_key_here

Run
---
streamlit run nestgpt_mvp_app.py

Notes
-----
- This prototype uses a small built-in knowledge base for a few countries.
- It is not legal advice.
- Replace the sample data with verified sources before presenting it as production-ready.
"""

from __future__ import annotations

import json
import math
import os
import re
from dataclasses import dataclass
from typing import Dict, List, Tuple

import streamlit as st
from openai import OpenAI


# =========================================================
# Configuration
# =========================================================

APP_TITLE = "NestGPT MVP"
MODEL = "openai/gpt-4.1-mini"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

DISCLAIMER = (
    "NestGPT MVP is a planning assistant for housing abroad. "
    "It is not legal advice, immigration advice, or a substitute for official government guidance."
)

SUPPORTED_COUNTRIES = ["Germany", "Portugal", "Japan"]


# =========================================================
# Knowledge base
# =========================================================

COUNTRY_KB: Dict[str, Dict[str, object]] = {
    "Germany": {
        "overview": (
            "Germany is a strong MVP market for international students and workers. "
            "Housing demand is high in major cities, and renters often need documents like proof of income, ID, and SCHUFA or other financial evidence."
        ),
        "visa": [
            "Visa needs depend on nationality and purpose of stay such as study, work, or job seeking.",
            "New arrivals often must complete city registration after moving in.",
            "Longer stays usually require a residence permit workflow after entry or after the initial visa stage.",
        ],
        "housing_rules": [
            "Apartments may be listed as warm rent or cold rent; warm rent includes some utilities while cold rent does not.",
            "Deposits are commonly requested before move-in and should be documented in the lease.",
            "Tenants should carefully review notice periods, furnished versus unfurnished terms, and utility responsibilities.",
        ],
        "required_docs": [
            "Passport or government ID",
            "Proof of income, savings, or sponsor support",
            "Employment letter or university enrollment proof",
            "Recent bank statements",
            "Credit evidence or alternative financial documentation",
        ],
        "cities": {
            "Berlin": {"rent_1br": 1400, "shared_room": 800, "monthly_cost_single": 2400},
            "Munich": {"rent_1br": 1700, "shared_room": 950, "monthly_cost_single": 2800},
            "Leipzig": {"rent_1br": 900, "shared_room": 500, "monthly_cost_single": 1700},
        },
        "landlord_tone": "formal, direct, polite, professional",
        "common_challenges": [
            "High competition in major cities",
            "German-language listings and messages",
            "Need for fast response and organized documents",
        ],
    },
    "Portugal": {
        "overview": (
            "Portugal is popular with students, expats, and remote workers. "
            "Demand is elevated in Lisbon and Porto, and users often need help comparing lease terms and residency pathways."
        ),
        "visa": [
            "Visa pathways vary by nationality and purpose, including study, work, and some long-stay residence routes.",
            "Residency processes may require proof of accommodation, income, and health coverage depending on the case.",
            "Applicants should validate requirements through official Portuguese immigration and consular sources.",
        ],
        "housing_rules": [
            "Lease terms, deposits, and utility handling should be checked carefully before signing.",
            "Short-term furnished rentals and long-term local leases often have different pricing and conditions.",
            "Users should verify whether internet, water, and electricity are included in the quoted monthly price.",
        ],
        "required_docs": [
            "Passport or ID",
            "Proof of income or savings",
            "Employment contract, freelance evidence, or student documents",
            "Tax or guarantor documents when requested",
        ],
        "cities": {
            "Lisbon": {"rent_1br": 1600, "shared_room": 700, "monthly_cost_single": 2300},
            "Porto": {"rent_1br": 1200, "shared_room": 550, "monthly_cost_single": 1800},
            "Coimbra": {"rent_1br": 850, "shared_room": 400, "monthly_cost_single": 1400},
        },
        "landlord_tone": "warm, respectful, concise",
        "common_challenges": [
            "Pricing differences between local and expat-facing listings",
            "Confusion around residency paperwork",
            "Variable listing quality and response speed",
        ],
    },
    "Japan": {
        "overview": (
            "Japan presents a distinctive rental process with strong paperwork expectations and local norms. "
            "International renters often need help understanding guarantor requirements, move-in fees, and housing terminology."
        ),
        "visa": [
            "Visa type depends on study, work, family status, or other purpose of stay.",
            "Residence-card related procedures and address registration are often part of settlement tasks after arrival.",
            "Official immigration and municipal sources should be checked for the latest requirements.",
        ],
        "housing_rules": [
            "Move-in costs can include deposit, key money, agency fee, and first month rent.",
            "Guarantor support may be required depending on the property and landlord.",
            "Listings can differ significantly in size, furnishing, and building rules, so details matter.",
        ],
        "required_docs": [
            "Passport or residence-related ID",
            "Proof of income or sponsor support",
            "Employment or school documentation",
            "Emergency contact and sometimes guarantor information",
        ],
        "cities": {
            "Tokyo": {"rent_1br": 1500, "shared_room": 750, "monthly_cost_single": 2400},
            "Osaka": {"rent_1br": 1000, "shared_room": 550, "monthly_cost_single": 1700},
            "Fukuoka": {"rent_1br": 800, "shared_room": 450, "monthly_cost_single": 1400},
        },
        "landlord_tone": "very polite, respectful, clear, low-pressure",
        "common_challenges": [
            "Complex upfront fees",
            "Language barriers",
            "Limited flexibility for renters without local support",
        ],
    },
}


# =========================================================
# Client
# =========================================================

def make_client() -> OpenAI:
    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not set.")
    return OpenAI(base_url=OPENROUTER_BASE_URL, api_key=api_key)


# =========================================================
# Retrieval helpers
# =========================================================

def tokenize(text: str) -> List[str]:
    return re.findall(r"[a-zA-Z0-9]+", text.lower())


def flatten_country_context(country: str) -> List[Tuple[str, str]]:
    info = COUNTRY_KB[country]
    chunks: List[Tuple[str, str]] = []

    chunks.append(("overview", str(info["overview"])))
    chunks.append(("visa", " ".join(info["visa"])))
    chunks.append(("housing_rules", " ".join(info["housing_rules"])))
    chunks.append(("required_docs", " ".join(info["required_docs"])))
    chunks.append(("common_challenges", " ".join(info["common_challenges"])))

    city_lines = []
    for city, stats in info["cities"].items():
        city_lines.append(
            f"{city}: 1br rent about ${stats['rent_1br']}/month, shared room about ${stats['shared_room']}/month, single-person monthly living cost about ${stats['monthly_cost_single']}/month"
        )
    chunks.append(("costs", " ".join(city_lines)))
    return chunks


def retrieve_country_context(country: str, query: str, top_k: int = 4) -> List[Tuple[str, str]]:
    query_tokens = set(tokenize(query))
    candidates = flatten_country_context(country)
    scored = []

    for label, text in candidates:
        tokens = set(tokenize(text))
        overlap = len(query_tokens & tokens)
        bonus = 0.25 if label in {"costs", "housing_rules", "visa"} else 0.0
        scored.append((overlap + bonus, label, text))

    scored.sort(reverse=True)
    return [(label, text) for score, label, text in scored[:top_k] if score > 0 or label == "overview"]


# =========================================================
# Agent tools
# =========================================================

def get_country_summary(country: str) -> str:
    info = COUNTRY_KB[country]
    city_examples = ", ".join(info["cities"].keys())
    return (
        f"Country: {country}\n"
        f"Overview: {info['overview']}\n"
        f"Example cities: {city_examples}\n"
        f"Challenges: {', '.join(info['common_challenges'])}"
    )


def estimate_budget(country: str, city: str, housing_type: str) -> str:
    info = COUNTRY_KB[country]
    city_stats = info["cities"].get(city)
    if not city_stats:
        valid = ", ".join(info["cities"].keys())
        return f"Unknown city for {country}. Try one of: {valid}."

    if housing_type == "shared":
        housing_cost = city_stats["shared_room"]
        label = "shared room"
    else:
        housing_cost = city_stats["rent_1br"]
        label = "1-bedroom apartment"

    base_monthly = city_stats["monthly_cost_single"]
    estimate = max(base_monthly, housing_cost + 900)
    return (
        f"Estimated monthly budget for {label} in {city}, {country}: about ${estimate}/month. "
        f"Housing portion: about ${housing_cost}/month. "
        f"Use this as a rough planning estimate, not an official quote."
    )


def build_checklist(country: str, city: str, user_type: str, budget: int) -> str:
    info = COUNTRY_KB[country]
    docs = info["required_docs"]
    city_stats = info["cities"].get(city)

    checklist = [
        f"1. Confirm your relocation path for {user_type} in {country} and verify official visa or residence requirements.",
        f"2. Collect core documents: {', '.join(docs)}.",
        f"3. Set a target monthly housing budget and compare it against local estimates for {city}.",
        f"4. Prepare a short renter profile with your purpose of stay, move-in date, budget, and proof of reliability.",
        f"5. Start contacting landlords or agencies with a country-appropriate message style.",
        f"6. Review lease terms carefully, including deposit, utilities, notice period, and any move-in fees.",
        f"7. After arrival, complete any required local registration or residence follow-up steps.",
    ]

    if city_stats:
        checklist.insert(
            3,
            f"Budget reference for {city}: shared room about ${city_stats['shared_room']}/month, 1-bedroom about ${city_stats['rent_1br']}/month, estimated single-person monthly cost about ${city_stats['monthly_cost_single']}/month.",
        )

    if budget > 0 and city_stats:
        if budget < city_stats["shared_room"] + 600:
            checklist.append("8. Your budget looks tight for this city, so consider shared housing, outer neighborhoods, or a lower-cost city.")
        else:
            checklist.append("8. Your stated budget appears potentially workable for an MVP planning scenario, but you should still verify live listings.")

    return "\n".join(checklist)


def draft_landlord_message(country: str, city: str, name: str, move_in: str, background: str, budget: int, language: str) -> str:
    tone = COUNTRY_KB[country]["landlord_tone"]
    budget_text = f"My monthly housing budget is around ${budget}." if budget > 0 else "I can share my budget range if helpful."

    english = f"""Hello,

My name is {name}. I am planning to move to {city}, {country} around {move_in}. {background}

I am interested in learning whether your property is still available and what documents you would need from me as a prospective tenant. {budget_text}

If possible, I would also appreciate details on rent, deposit, utilities, lease length, and move-in requirements.

Thank you for your time.
Best regards,
{name}

Suggested tone for this market: {tone}."""

    if language.lower() == "english":
        return english

    return (
        english
        + "\n\n"
        + f"Note: In the MVP, non-English support can be added by routing this draft through translation for {language}."
    )


# =========================================================
# LLM layer
# =========================================================

SYSTEM_PROMPT = """You are NestGPT, an AI relocation assistant focused on housing abroad.

Your purpose:
- help users understand rental procedures and housing expectations
- explain visa/residency basics at a high level
- provide rough planning estimates for costs
- help draft respectful landlord messages
- generate practical relocation checklists

Rules:
- Use only the provided country knowledge and tool results.
- Be transparent that the information is MVP-level and may change.
- Never claim legal certainty.
- If the knowledge base lacks something specific, say what is missing.
- Be concise but practical.
"""


def llm_answer(client: OpenAI, prompt: str, context: str) -> str:
    response = client.chat.completions.create(
        model=MODEL,
        temperature=0.2,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"User request:\n{prompt}\n\nAvailable context:\n{context}"},
        ],
    )
    return (response.choices[0].message.content or "").strip()


# =========================================================
# Intent router
# =========================================================

def detect_intent(user_query: str) -> str:
    q = user_query.lower()
    if any(word in q for word in ["message", "email", "landlord", "write to", "draft"]):
        return "message"
    if any(word in q for word in ["checklist", "plan", "steps", "timeline", "prepare"]):
        return "checklist"
    if any(word in q for word in ["budget", "cost", "rent", "afford", "monthly"]):
        return "budget"
    if any(word in q for word in ["visa", "residency", "permit", "legal", "requirements"]):
        return "qa"
    if any(word in q for word in ["housing", "apartment", "lease", "deposit", "rule"]):
        return "qa"
    return "qa"


# =========================================================
# Streamlit UI
# =========================================================

def init_state() -> None:
    if "history" not in st.session_state:
        st.session_state.history = []


def sidebar_profile() -> Dict[str, object]:
    st.sidebar.header("User Profile")
    country = st.sidebar.selectbox("Destination country", SUPPORTED_COUNTRIES)
    city = st.sidebar.selectbox("Destination city", list(COUNTRY_KB[country]["cities"].keys()))
    user_type = st.sidebar.selectbox("Relocation type", ["student", "worker", "remote worker", "family move"])
    housing_type = st.sidebar.selectbox("Housing target", ["shared", "private_1br"])
    budget = st.sidebar.number_input("Monthly budget (USD)", min_value=0, value=1800, step=100)
    move_in = st.sidebar.text_input("Target move-in", value="September 2026")
    name = st.sidebar.text_input("Your name", value="Alex")
    language = st.sidebar.selectbox("Landlord message language", ["English", "German", "Portuguese", "Japanese"])

    st.sidebar.markdown("---")
    st.sidebar.caption(DISCLAIMER)

    return {
        "country": country,
        "city": city,
        "user_type": user_type,
        "housing_type": housing_type,
        "budget": int(budget),
        "move_in": move_in,
        "name": name,
        "language": language,
    }


def render_history() -> None:
    for item in st.session_state.history:
        with st.chat_message(item["role"]):
            st.markdown(item["content"])


def build_context_for_query(profile: Dict[str, object], user_query: str) -> str:
    country = str(profile["country"])
    city = str(profile["city"])
    housing_type = str(profile["housing_type"])
    user_type = str(profile["user_type"])
    budget = int(profile["budget"])

    retrieved = retrieve_country_context(country, user_query)
    parts = [f"User profile: country={country}, city={city}, user_type={user_type}, housing_type={housing_type}, budget=${budget}"]

    for label, text in retrieved:
        parts.append(f"[{label}] {text}")

    parts.append("[summary] " + get_country_summary(country))
    parts.append("[budget_estimate] " + estimate_budget(country, city, housing_type))
    return "\n\n".join(parts)


def run_agent(client: OpenAI, profile: Dict[str, object], user_query: str) -> str:
    country = str(profile["country"])
    city = str(profile["city"])
    user_type = str(profile["user_type"])
    budget = int(profile["budget"])
    move_in = str(profile["move_in"])
    name = str(profile["name"])
    language = str(profile["language"])
    housing_type = str(profile["housing_type"])

    intent = detect_intent(user_query)

    if intent == "message":
        background = f"I am relocating as a {user_type} and I am currently planning my housing search."
        draft = draft_landlord_message(country, city, name, move_in, background, budget, language)
        return draft

    if intent == "checklist":
        checklist = build_checklist(country, city, user_type, budget)
        intro = f"Here is a practical relocation checklist for {city}, {country}:\n\n"
        return intro + checklist

    context = build_context_for_query(profile, user_query)
    return llm_answer(client, user_query, context)


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, page_icon="🏠", layout="wide")
    init_state()

    st.title("🏠 NestGPT MVP")
    st.write("AI for finding housing abroad — focused on a small-country MVP.")
    st.caption(DISCLAIMER)

    profile = sidebar_profile()

    col1, col2 = st.columns([1.5, 1])
    with col1:
        st.subheader("Ask NestGPT")
        render_history()

        suggested = st.container()
        with suggested:
            st.markdown("**Example questions**")
            st.markdown(
                "- What do I need to rent an apartment in Germany?\n"
                "- Give me a relocation checklist for Lisbon.\n"
                "- Can I afford Tokyo with a $2200 monthly budget?\n"
                "- Draft a landlord message for my move to Porto."
            )

        user_query = st.chat_input("Ask about housing, costs, visa basics, landlord messages, or relocation planning")
        if user_query:
            st.session_state.history.append({"role": "user", "content": user_query})
            with st.chat_message("user"):
                st.markdown(user_query)

            try:
                client = make_client()
                answer = run_agent(client, profile, user_query)
            except Exception as exc:
                answer = f"Error: {exc}"

            st.session_state.history.append({"role": "assistant", "content": answer})
            with st.chat_message("assistant"):
                st.markdown(answer)

    with col2:
        st.subheader("Current destination snapshot")
        st.code(get_country_summary(str(profile["country"])))

        st.subheader("Budget estimate")
        st.info(
            estimate_budget(
                str(profile["country"]),
                str(profile["city"]),
                str(profile["housing_type"]),
            )
        )

        st.subheader("One-click actions")
        if st.button("Generate relocation checklist"):
            result = build_checklist(
                str(profile["country"]),
                str(profile["city"]),
                str(profile["user_type"]),
                int(profile["budget"]),
            )
            st.session_state.history.append({"role": "assistant", "content": result})
            st.rerun()

        if st.button("Draft landlord message"):
            result = draft_landlord_message(
                str(profile["country"]),
                str(profile["city"]),
                str(profile["name"]),
                str(profile["move_in"]),
                f"I am relocating as a {profile['user_type']} and I want to introduce myself clearly.",
                int(profile["budget"]),
                str(profile["language"]),
            )
            st.session_state.history.append({"role": "assistant", "content": result})
            st.rerun()

        if st.button("Show planning context"):
            st.text(build_context_for_query(profile, "housing visa rent message checklist"))

        st.markdown("---")
        st.markdown("**How to extend this MVP**")
        st.markdown(
            "1. Replace built-in country data with verified sources.\n"
            "2. Add retrieval over official housing and visa documents.\n"
            "3. Add translation and document summarization tools.\n"
            "4. Add citation links and source freshness checks.\n"
            "5. Add user memory and saved apartment comparisons."
        )


if __name__ == "__main__":
    main()
