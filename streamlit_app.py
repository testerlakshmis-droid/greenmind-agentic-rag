"""Streamlit entrypoint for public deployment on Streamlit Community Cloud."""

import os
import random
import streamlit as st

from src.agent.green_agent import GreenMindAgent


st.set_page_config(
    page_title="GreenMind - Environmental Health Advisor",
    page_icon="🌍",
    layout="wide",
)

st.title("GreenMind 🌍")
st.caption("Agentic RAG for environmental policies, effects, and pollution insights")

# ── Welcome quote (shown once per session on page load) ──────────────────────
_QUOTES = [
    "In every walk with nature, one receives far more than he seeks. — John Muir",
    "The environment is where we all meet; where all have a mutual interest. — Lady Bird Johnson",
    "The greatest threat to our planet is the belief that someone else will save it. — Robert Swan",
    "We do not inherit the earth from our ancestors; we borrow it from our children. — Native American Proverb",
    "The Earth does not belong to us; we belong to the Earth. — Chief Seattle",
    "The future will either be green or not at all. — Bob Brown",
    "What we do to the Earth, we do to ourselves. — Chief Seattle",
]

if "welcome_quote" not in st.session_state:
    st.session_state.welcome_quote = random.choice(_QUOTES)

st.info(f'💬 *"{st.session_state.welcome_quote}"*')
st.markdown("---")

if "agent" not in st.session_state:
    try:
        api_key = st.secrets.get("GOOGLE_API_KEY", os.getenv("GOOGLE_API_KEY", ""))
        if api_key:
            os.environ["GOOGLE_API_KEY"] = api_key
        st.session_state.agent = GreenMindAgent(genai_api_key=api_key)
    except Exception as e:
        st.error(f"Initialization failed: {e}")
        st.info("Add GOOGLE_API_KEY in Streamlit app Settings -> Secrets, then reboot the app.")
        st.stop()

if "history" not in st.session_state:
    st.session_state.history = []

with st.form("query_form", clear_on_submit=False):
    user_query = st.text_area(
        "Ask about environmental topics",
        placeholder="Example: What is the Superfund program in USA?",
        height=110,
    )
    submitted = st.form_submit_button("Get Answer")

if submitted:
    query = (user_query or "").strip()
    if not query:
        st.warning("Please enter a question.")
    else:
        with st.spinner("GreenMind is analyzing your query..."):
            result = st.session_state.agent.chat(query)
            answer = result.get("answer", "No answer available.")
            tools_used = result.get("tools_used", [])
            elapsed_ms = result.get("processing_time_ms", 0)

        st.session_state.history.insert(
            0,
            {
                "query": query,
                "answer": answer,
                "tools": tools_used,
                "elapsed_ms": elapsed_ms,
            },
        )

if st.session_state.history:
    latest = st.session_state.history[0]
    st.subheader("Latest Response")
    st.markdown(latest["answer"])

    with st.expander("Execution Details"):
        st.write(f"Tools used: {', '.join(latest.get('tools', [])) or 'None'}")
        st.write(f"Response time: {latest.get('elapsed_ms', 0)} ms")

    with st.expander("Recent Questions"):
        for item in st.session_state.history[:10]:
            st.markdown(f"**Q:** {item['query']}")
            st.markdown(item["answer"])
            st.caption(
                f"Tools: {', '.join(item.get('tools', [])) or 'None'} | "
                f"Time: {item.get('elapsed_ms', 0)} ms"
            )
            st.markdown("---")
