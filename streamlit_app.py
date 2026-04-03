"""Streamlit entrypoint for public deployment on Streamlit Community Cloud."""

import streamlit as st

from greenmind_web import chatbot_response


st.set_page_config(
    page_title="GreenMind - Environmental Health Advisor",
    page_icon="🌍",
    layout="wide",
)

st.title("GreenMind")
st.caption("Agentic RAG for environmental policies, effects, and pollution insights")

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
            answer, logs, _history = chatbot_response(query)
        st.session_state.history.insert(0, {"query": query, "answer": answer, "logs": logs})


if st.session_state.history:
    latest = st.session_state.history[0]
    st.subheader("Latest Response")
    st.markdown(latest["answer"])

    with st.expander("Execution Logs"):
        st.text(latest["logs"])

    with st.expander("Recent Questions"):
        for item in st.session_state.history[:10]:
            st.markdown(f"**Q:** {item['query']}")
            st.markdown(item["answer"])
            st.markdown("---")
