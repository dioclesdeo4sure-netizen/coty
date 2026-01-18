import streamlit as st
import os
from google import genai
from google.genai.errors import APIError

# =========================================================
# 1. PAGE CONFIG (MUST BE FIRST)
# =========================================================
st.set_page_config(
    page_title="Coty Butchery | AI Customer Service",
    page_icon="🥩",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# 2. CUSTOM CSS (GREEN AI THEME + FIXED CHAT INPUT)
# =========================================================
st.markdown("""
<style>

/* Global font */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* App background */
.stApp {
    background: linear-gradient(135deg, #020617, #020617);
    color: #f8fafc;
}

/* Headers */
h1, h2, h3 {
    color: #22c55e;
}

/* Chat message base */
[data-testid="stChatMessage"] {
    border-radius: 16px;
    padding: 14px;
    margin-bottom: 12px;
    animation: fadeIn 0.35s ease-in-out;
}

/* USER bubble (blue) */
[data-testid="stChatMessage"][aria-label="user"] {
    background: linear-gradient(135deg, #2563eb, #1e40af);
    color: #ffffff;
}

/* AI bubble (DEEP GREEN + WHITE TEXT) */
[data-testid="stChatMessage"][aria-label="assistant"] {
    background: linear-gradient(135deg, #064e3b, #022c22);
    border: 1px solid #10b981;
    color: #ffffff;
    box-shadow: 0 0 12px rgba(16, 185, 129, 0.35);
}

/* Force AI text to white */
[data-testid="stChatMessage"][aria-label="assistant"] p,
[data-testid="stChatMessage"][aria-label="assistant"] span,
[data-testid="stChatMessage"][aria-label="assistant"] li {
    color: #ffffff !important;
}

/* CHAT INPUT FIX */
[data-testid="stChatInput"] textarea {
    border-radius: 14px !important;
    border: 1px solid #10b981 !important;
    background-color: #020617 !important;
    color: #ffffff !important;
}

/* Buttons */
button {
    border-radius: 12px !important;
    font-weight: 600 !important;
    background: #22c55e !important;
    color: #022c22 !important;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #020617;
    border-right: 1px solid #022c22;
}

/* Animation */
@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(6px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# 3. GEMINI API SETUP (UNCHANGED LOGIC)
# =========================================================
RENDER_ENV_VAR_NAME = "GEMINI_API_KEY_RENDER"

API_KEY = os.environ.get(RENDER_ENV_VAR_NAME)

if not API_KEY:
    st.error(
        f"❌ Kosa: Gemini API Key haijapatikana. "
        f"Weka Environment Variable '{RENDER_ENV_VAR_NAME}' kwenye Render."
    )
    st.stop()

@st.cache_resource
def initialize_gemini_client(api_key):
    return genai.Client(api_key=api_key)

client = initialize_gemini_client(API_KEY)

# =========================================================
# 4. MODEL + SYSTEM PROMPT (UNCHANGED)
# =========================================================
GEMINI_MODEL = "gemini-2.5-flash"

SYSTEM_PROMPT = """
Wewe ni **Coty**, mhudumu wa wateja wa kidigitali mwenye **uwezo na akili mnemba (AI)**,
uliyebuniwa na **Aqua Softwares** kwa ajili ya **Coty Butchery**.

( System prompt yako ndefu imebaki kama ulivyoandika awali – HAIJABADILISHWA )
"""

# =========================================================
# 5. SIDEBAR (UI ONLY)
# =========================================================
with st.sidebar:
    st.markdown("## 🤖 Coty AI")
    st.write("Huduma ya wateja ya kisasa 🟢")

    st.divider()

    st.selectbox("🌍 Lugha", ["Kiswahili", "English"])
    st.toggle("🧠 Smart AI Mode", value=True)

    if st.button("🧹 Futa Mazungumzo"):
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.markdown("📍 **Mahali Yetu:**")
    st.markdown("[📌 Google Maps](https://maps.app.goo.gl/Wp18PHX99Zvjk3f6)")

# =========================================================
# 6. HEADER
# =========================================================
st.markdown("""
<div style="text-align:center; padding: 18px;">
    <h1>🥩 Coty Butchery AI</h1>
    <p style="font-size:18px; color:#d1fae5;">
        Huduma ya wateja ya haraka • ya kuaminika • ya kisasa
    </p>
</div>
""", unsafe_allow_html=True)

# =========================================================
# 7. CHAT STATE
# =========================================================
if "messages" not in st.session_state:
    st.session_state.messages = []

# =========================================================
# 8. SHOW CHAT HISTORY
# =========================================================
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# =========================================================
# 9. CHAT INPUT (MUST BE LAST)
# =========================================================
prompt = st.chat_input("💬 Andika ujumbe wako hapa...")

if prompt:
    st.session_state.messages.append(
        {"role": "user", "content": prompt}
    )

    with st.chat_message("user"):
        st.markdown(prompt)

    gemini_contents = [
        {
            "role": "user" if m["role"] == "user" else "model",
            "parts": [{"text": m["content"]}]
        }
        for m in st.session_state.messages
    ]

    try:
        with st.chat_message("assistant"):
            with st.spinner("🤖 Coty anafikiria..."):

                chat_completion = client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=gemini_contents,
                    config={
                        "system_instruction": SYSTEM_PROMPT,
                        "temperature": 0.8
                    }
                )

                response = chat_completion.text
                st.markdown(response)

    except APIError as e:
        response = f"Samahani 😔 kuna changamoto ya mfumo kwa sasa. ({e})"
        st.markdown(response)

    except Exception as e:
        response = f"Kuna kosa lisilotarajiwa 😥 ({e})"
        st.markdown(response)

  st.session_state.messages.append(
    {"role": "assistant", "content": response}
)
