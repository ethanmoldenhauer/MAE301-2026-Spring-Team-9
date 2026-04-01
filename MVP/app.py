from __future__ import annotations

import streamlit as st

from src.answering import answer_from_sources, summarize_document, translate_text
from src.api import make_client
from src.citations import format_citations
from src.comparison import compare_apartments
from src.config import APP_TITLE, DISCLAIMER, SUPPORTED_COUNTRIES, TOPICS
from src.data_loader import load_source_chunks
from src.memory import delete_apartment, init_db, list_apartments, load_profile, save_apartment, save_profile
from src.models import Apartment
from src.retrieval import retrieve
from src.ui_helpers import find_logo


def init_session() -> None:
    if "history" not in st.session_state:
        st.session_state.history = []


def render_header() -> None:
    logo = find_logo()
    if logo:
        col_logo, col_title = st.columns([1, 7])
        with col_logo:
            st.image(logo, width=90)
        with col_title:
            st.title(APP_TITLE)
            st.write("AI for finding housing abroad with source-backed answers, citations, and saved comparisons.")
    else:
        st.title("🏠 " + APP_TITLE)
        st.write("AI for finding housing abroad with source-backed answers, citations, and saved comparisons.")
    st.caption(DISCLAIMER)


def sidebar_profile(defaults: dict) -> dict:
    st.sidebar.header("User Profile")
    name = st.sidebar.text_input("Name", value=str(defaults.get("name", "Alex")))
    country = st.sidebar.selectbox(
        "Destination country",
        SUPPORTED_COUNTRIES,
        index=SUPPORTED_COUNTRIES.index(defaults.get("country", SUPPORTED_COUNTRIES[0])) if defaults.get("country") in SUPPORTED_COUNTRIES else 0,
    )

    city_map = {
        "Germany": ["Berlin", "Munich", "Leipzig"],
        "Portugal": ["Lisbon", "Porto", "Coimbra"],
        "Japan": ["Tokyo", "Osaka", "Fukuoka"],
    }
    city_options = city_map[country]
    city = st.sidebar.selectbox(
        "Destination city",
        city_options,
        index=city_options.index(defaults.get("city", city_options[0])) if defaults.get("city") in city_options else 0,
    )
    user_type = st.sidebar.selectbox(
        "Relocation type",
        ["student", "worker", "remote worker", "family move"],
        index=["student", "worker", "remote worker", "family move"].index(defaults.get("user_type", "student")) if defaults.get("user_type") in ["student", "worker", "remote worker", "family move"] else 0,
    )
    language = st.sidebar.selectbox(
        "Preferred landlord message language",
        ["English", "German", "Portuguese", "Japanese"],
        index=["English", "German", "Portuguese", "Japanese"].index(defaults.get("language", "English")) if defaults.get("language") in ["English", "German", "Portuguese", "Japanese"] else 0,
    )
    budget = st.sidebar.number_input("Monthly budget (USD)", min_value=0, value=int(defaults.get("budget", 1800) or 1800), step=100)
    move_in = st.sidebar.text_input("Target move-in", value=str(defaults.get("move_in", "September 2026")))

    profile = {
        "name": name,
        "country": country,
        "city": city,
        "user_type": user_type,
        "language": language,
        "budget": int(budget),
        "move_in": move_in,
    }

    if st.sidebar.button("Save profile", use_container_width=True):
        save_profile(profile)
        st.sidebar.success("Profile saved")

    return profile


def render_chat_history() -> None:
    for item in st.session_state.history:
        with st.chat_message(item["role"]):
            st.markdown(item["content"])


def local_answer_fallback(results) -> str:
    if not results:
        return "I could not find relevant source-backed material in the current document set."
    lines = ["Here is a source-backed fallback answer from the current documents:"]
    for i, chunk in enumerate(results[:3], start=1):
        lines.append(f"[{i}] {chunk.text[:350]}...")
    return "\n\n".join(lines)


def main() -> None:
    logo = find_logo() or "🏠"
    st.set_page_config(page_title=APP_TITLE, page_icon=logo, layout="wide")
    init_db()
    init_session()
    render_header()

    try:
        client, api_mode, model = make_client()
        api_status = f"API connected via {api_mode}"
    except Exception as exc:
        client = None
        model = None
        api_status = f"API unavailable: {exc}"

    chunks = load_source_chunks()
    profile = sidebar_profile(load_profile())

    tab1, tab2, tab3, tab4 = st.tabs([
        "Ask NestGPT",
        "Translate / Summarize",
        "Saved Apartments",
        "About Sources",
    ])

    with tab1:
        st.caption(api_status)
        render_chat_history()

        col_filter1, col_filter2 = st.columns(2)
        with col_filter1:
            topic = st.selectbox("Focus topic", TOPICS, index=3)
        with col_filter2:
            force_country = st.checkbox("Restrict retrieval to selected country", value=True)

        st.markdown("**Example questions**")
        st.markdown(
            "- What documents should I prepare before contacting landlords in Germany?\n"
            "- What should I verify before signing a lease in Portugal?\n"
            "- What are common move-in costs in Japan?"
        )

        user_query = st.chat_input("Ask a source-backed question about housing, visas, or moving abroad")
        if user_query:
            st.session_state.history.append({"role": "user", "content": user_query})
            with st.chat_message("user"):
                st.markdown(user_query)

            results = retrieve(
                query=user_query,
                chunks=chunks,
                country=profile["country"] if force_country else None,
                topic=topic,
            )

            try:
                answer = answer_from_sources(client, model, user_query, results)
            except Exception:
                answer = local_answer_fallback(results)

            citations = format_citations(results)
            full_answer = answer + "\n\n---\n**Sources**\n\n" + citations
            st.session_state.history.append({"role": "assistant", "content": full_answer})
            with st.chat_message("assistant"):
                st.markdown(full_answer)

    with tab2:
        st.subheader("Translate text")
        translate_input = st.text_area("Paste text to translate", height=160, key="translate_input")
        target_language = st.selectbox("Translate to", ["English", "German", "Portuguese", "Japanese"], key="translate_lang")
        if st.button("Translate", use_container_width=True):
            if not translate_input.strip():
                st.warning("Paste some text first.")
            else:
                try:
                    output = translate_text(client, model, translate_input, target_language)
                    st.success("Translation complete")
                    st.text_area("Translated text", value=output, height=220)
                except Exception as exc:
                    st.error(f"Translation unavailable: {exc}")

        st.markdown("---")
        st.subheader("Summarize a lease, visa page, or landlord message")
        summarize_input = st.text_area("Paste text to summarize", height=200, key="summarize_input")
        if st.button("Summarize", use_container_width=True):
            if not summarize_input.strip():
                st.warning("Paste some text first.")
            else:
                try:
                    summary = summarize_document(client, model, summarize_input)
                    st.text_area("Summary", value=summary, height=250)
                except Exception as exc:
                    st.error(f"Summarization unavailable: {exc}")

    with tab3:
        st.subheader("Save an apartment")
        with st.form("apartment_form"):
            title = st.text_input("Listing title")
            city = st.text_input("City", value=profile["city"])
            country = st.text_input("Country", value=profile["country"])
            rent = st.number_input("Monthly rent", min_value=0.0, value=1200.0, step=50.0)
            deposit = st.number_input("Deposit", min_value=0.0, value=1200.0, step=50.0)
            furnished = st.checkbox("Furnished")
            utilities_included = st.checkbox("Utilities included")
            url = st.text_input("Listing URL")
            notes = st.text_area("Notes")
            submitted = st.form_submit_button("Save apartment")
            if submitted:
                save_apartment(
                    Apartment(
                        title=title,
                        city=city,
                        country=country,
                        rent=rent,
                        deposit=deposit,
                        furnished=furnished,
                        utilities_included=utilities_included,
                        url=url,
                        notes=notes,
                    )
                )
                st.success("Apartment saved")

        st.markdown("---")
        st.subheader("Saved apartments")
        apartments = list_apartments()
        if not apartments:
            st.info("No apartments saved yet.")
        else:
            for apt in apartments:
                with st.expander(f"#{apt['id']} - {apt['title']} ({apt['city']}, {apt['country']})"):
                    st.write(f"Rent: ${apt['rent']}")
                    st.write(f"Deposit: ${apt['deposit']}")
                    st.write(f"Furnished: {'Yes' if apt['furnished'] else 'No'}")
                    st.write(f"Utilities included: {'Yes' if apt['utilities_included'] else 'No'}")
                    if apt["url"]:
                        st.write(f"URL: {apt['url']}")
                    if apt["notes"]:
                        st.write(f"Notes: {apt['notes']}")
                    if st.button(f"Delete apartment #{apt['id']}", key=f"delete_{apt['id']}"):
                        delete_apartment(int(apt["id"]))
                        st.rerun()

            st.markdown("---")
            st.subheader("Comparison")
            selected_ids = st.multiselect(
                "Choose apartments to compare",
                options=[apt["id"] for apt in apartments],
                format_func=lambda apt_id: next(
                    f"#{apt['id']} - {apt['title']} ({apt['city']})" for apt in apartments if apt["id"] == apt_id
                ),
            )
            selected = [apt for apt in apartments if apt["id"] in selected_ids]
            if selected:
                st.text(compare_apartments(selected))

    with tab4:
        st.subheader("Loaded source documents")
        st.write(f"Loaded {len(chunks)} source chunks from `data/processed/`.")
        for chunk in chunks:
            with st.expander(f"{chunk.chunk_id} — {chunk.title}"):
                st.write(f"Country: {chunk.country}")
                st.write(f"Topic: {chunk.topic}")
                st.write(f"Publisher: {chunk.publisher}")
                st.write(f"Last checked: {chunk.last_checked}")
                st.write(f"URL: {chunk.url}")
                st.write(chunk.text)


if __name__ == "__main__":
    main()
