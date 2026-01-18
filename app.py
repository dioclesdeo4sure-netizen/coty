import streamlit as st
import os
from google import genai
from google.genai.errors import APIError

# --- 1. Usanidi wa API Client na Models ---
RENDER_ENV_VAR_NAME = "GEMINI_API_KEY_RENDER"

API_KEY = os.environ.get(RENDER_ENV_VAR_NAME)
if not API_KEY:
    st.error(f"❌ Kosa: Key ya Gemini haijapatikana. Tafadhali weka Environment Variable '{RENDER_ENV_VAR_NAME}' kwenye dashibodi ya Render.")
    st.stop()

@st.cache_resource
def initialize_gemini_client(api_key):
    return genai.Client(api_key=api_key)

client = initialize_gemini_client(API_KEY)

# --- 2. Model ---
GEMINI_MODEL = "gemini-2.5-flash"

# --- 3. Streamlit UI Config ---
st.set_page_config(page_title="Aura Chatbot (Gemini Powered)", page_icon="✨", layout="wide")

# CSS ya Chat Bubble ya Kisasa
st.markdown("""
<style>
/* Scrollable chat area */
.chat-container {
    max-height: 600px;
    overflow-y: auto;
    padding: 10px;
}

/* AI Bubble */
.ai-bubble {
    background-color: #2ecc71;  /* Kijani iliyoiva */
    color: white;
    padding: 12px 18px;
    border-radius: 18px;
    margin: 8px 0;
    max-width: 75%;
    box-shadow: 0px 2px 8px rgba(0,0,0,0.2);
}

/* User Bubble */
.user-bubble {
    background-color: #ffffff;
    color: #111111;
    padding: 12px 18px;
    border-radius: 18px;
    margin: 8px 0;
    max-width: 75%;
    align-self: flex-end;
    box-shadow: 0px 2px 8px rgba(0,0,0,0.1);
}

/* Flex container for bubbles */
.bubble-row {
    display: flex;
    flex-direction: column;
}
</style>
""", unsafe_allow_html=True)

st.title("Karibu Coty Butchery")
st.caption("Mtoa huduma wa haraka zaidi wa kidigitali!")

# --- 4. Chat History ---
if "messages" not in st.session_state:
    st.session_state.messages = []

st.markdown('<div class="chat-container">', unsafe_allow_html=True)
for message in st.session_state.messages:
    if message["role"] == "assistant":
        st.markdown(f'<div class="bubble-row"><div class="ai-bubble">{message["content"]}</div></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="bubble-row" style="align-items: flex-end;"><div class="user-bubble">{message["content"]}</div></div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# --- 5. Input Box ---
if prompt := st.chat_input("Uliza swali lako hapa"):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(f'<div class="user-bubble">{prompt}</div>', unsafe_allow_html=True)

    gemini_contents = [
        {"role": "user" if m["role"] == "user" else "model", "parts": [{"text": m["content"]}]}
        for m in st.session_state.messages
    ]

    try:
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                chat_completion = client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=gemini_contents,
                    config={
                        "temperature": 0.8,
                    }
                )
                response = chat_completion.text
                st.markdown(f'<div class="ai-bubble">{response}</div>', unsafe_allow_html=True)

    except APIError as e:
        response = f"Nakuomba radhi, mfumo wa Gemini una changamoto kwa sasa (API Error). Kosa: {e}"
        st.markdown(f'<div class="ai-bubble">{response}</div>', unsafe_allow_html=True)

    except Exception as e:
        response = f"Samahani, kumetokea kosa lisilotarajiwa: {e}"
        st.markdown(f'<div class="ai-bubble">{response}</div>', unsafe_allow_html=True)

    st.session_state.messages.append({"role": "assistant", "content": response})
