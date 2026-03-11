from urllib import response
import streamlit as st
import requests
import random
import time
from streamlit.runtime.scriptrunner import get_script_run_ctx


# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []


def get_session_id():
    ctx = get_script_run_ctx()
    return ctx.session_id if ctx else "default_user"
# Initialize Session State
if "session_id" not in st.session_state:
    st.session_state.session_id = get_session_id()

st.title("Stateful AI Agent")
st.caption(f"Connected as Session: {st.session_state.session_id[:8]}..")



# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("How Can I help you?"):
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        # Define a generator to handle the streaming response
        def stream_backend_response():
            # stream=True is critical for keeping the connection open
            # We pass the session_id in the JSON body
            payload = {
                "prompt": prompt,
                "user_id": st.session_state.session_id
            }
            with requests.post(
                "http://backend:8000/generate", 
                json=payload, 
                stream=True
            ) as response:
                for line in response.iter_lines(decode_unicode=True):
                    if not line:
                        continue

                    # Strip SSE prefix
                    if line.startswith("data:"):
                        yield line.replace("data:", "", 1).strip()

        # st.write_stream consumes the generator and handles the UI rendering
        full_response = st.write_stream(stream_backend_response())
        st.session_state.messages.append({"role": "assistant", "content": full_response})

