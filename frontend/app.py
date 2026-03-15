"""Streamlit chat frontend for the LLM Task Manager."""

import os
import uuid

import httpx
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://fastapi-app:8000")

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Task Manager",
    page_icon="✅",
    layout="centered",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    .stChatMessage { border-radius: 12px; }
    .stChatInput textarea { border-radius: 10px !important; }
    header { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Session state ─────────────────────────────────────────────────────────────
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "👋 Hi! I'm your task manager assistant.\n\n"
                "Try saying:\n"
                "- *Create a list called Groceries*\n"
                "- *Add milk to Groceries*\n"
                "- *Show my Groceries list*\n"
                "- *Delete the Groceries list*"
            ),
        }
    ]

# ── Header ────────────────────────────────────────────────────────────────────
st.title("✅ Task Manager")
st.caption("Powered by LLM + ADK · talk to your lists")

# ── Chat history ──────────────────────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ── Input ─────────────────────────────────────────────────────────────────────
if prompt := st.chat_input("Ask me anything about your task lists…"):
    # Show user message immediately
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Call backend
    with st.chat_message("assistant"):
        with st.spinner("Thinking…"):
            try:
                resp = httpx.post(
                    f"{BACKEND_URL}/api/chat",
                    json={
                        "message": prompt,
                        "session_id": st.session_state.session_id,
                    },
                    timeout=30.0,
                )
                resp.raise_for_status()
                reply = resp.json()["reply"]
            except httpx.HTTPStatusError as exc:
                reply = f"⚠️ Backend error {exc.response.status_code}: {exc.response.text}"
            except Exception as exc:
                reply = f"⚠️ Could not reach the backend: {exc}"

        st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Session")
    st.code(st.session_state.session_id[:16] + "…", language=None)

    if st.button("🔄 New session"):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.header("Quick commands")
    QUICK = [
        "What lists do I have?",
        "Create a list called Work",
        "Show my Work list",
        "Add 'Buy coffee' to Work",
        "Delete the Work list",
    ]
    for q in QUICK:
        if st.button(q, use_container_width=True):
            st.session_state._quick_prompt = q
            st.rerun()

    st.divider()
    st.markdown("**Backend:** " + BACKEND_URL)
