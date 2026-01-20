import streamlit as st
import os
from google import genai
from google.genai.errors import APIError
from gtts import gTTS
import base64

# --- Usanidi wa Ukurasa ---
st.set_page_config(page_title="Coty Butchery AI", page_icon="🥩")

# --- Usanidi wa API Key ---
RENDER_ENV_VAR_NAME = "GEMINI_API_KEY_RENDER"
API_KEY = os.environ.get(RENDER_ENV_VAR_NAME)

if not API_KEY:
    st.error(f"❌ Weka API Key kwenye Render: {RENDER_ENV_VAR_NAME}")
    st.stop()

client = genai.Client(api_key=API_KEY)

# --- MODEL YA JUU (1.5 PRO) ---
GEMINI_MODEL = "gemini-1.5-pro"

# System Prompt yako (Imebaki kama ilivyokuwa lakini imeboreshwa kidogo)
SYSTEM_PROMPT = """
Wewe ni Coty, mhudumu wa wateja wa Coty Butchery. 
[Maelekezo yako yote uliyoyaandika awali yawekwe hapa...]
"""

# --- Kazi ya Sauti (Text-to-Speech) ---
def play_voice(text):
    try:
        # Tunatengeneza sauti (Swahili)
        tts = gTTS(text=text, lang='sw')
        tts.save("response.mp3")
        
        # Kusoma file na kuligeuza kuwa base64 kwa ajili ya HTML audio
        with open("response.mp3", "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
            md = f"""
                <audio autoplay="true">
                <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
                </audio>
                """
            st.markdown(md, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Kosa la sauti: {e}")

# --- UI YA STREAMLIT ---
st.title("🥩 Karibu Coty Butchery")
st.caption("Mhudumu wako wa kidigitali anayekujali!")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Onyesha chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat Input
if prompt := st.chat_input("Uliza chochote..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Maandalizi ya maudhui ya kutuma Gemini
    gemini_contents = [
        {"role": "user" if m["role"] == "user" else "model", "parts": [{"text": m["content"]}]}
        for m in st.session_state.messages
    ]

    try:
        with st.chat_message("assistant"):
            with st.spinner("Coty anafikiria..."):
                chat_completion = client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=gemini_contents,
                    config={
                        "system_instruction": SYSTEM_PROMPT,
                        "temperature": 0.8,
                    }
                )
                
                response_text = chat_completion.text
                st.markdown(response_text)
                
                # Hapa ndipo AI inapoanza kuongea
                play_voice(response_text)
                
                st.session_state.messages.append({"role": "assistant", "content": response_text})

    except Exception as e:
        st.error(f"Samahani, kumetokea kosa: {e}")
