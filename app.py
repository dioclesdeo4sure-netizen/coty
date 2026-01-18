import streamlit as st
import os
from google import genai
from google.genai.errors import APIError

# =========================================================
# 1. PAGE CONFIG (MUST BE FIRST STREAMLIT COMMAND)
# =========================================================
st.set_page_config(
    page_title="Coty Butchery | AI Customer Service",
    page_icon="🥩",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# 2. CUSTOM CSS (UI UPGRADE)
# =========================================================
st.markdown("""
<style>

/* Global font */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* App background */
.stApp {
    background: linear-gradient(135deg, #0f172a, #020617);
    color: #f8fafc;
}

/* Headers */
h1, h2, h3 {
    color: #facc15;
}

/* Chat messages */
[data-testid="stChatMessage"] {
    border-radius: 16px;
    padding: 14px;
    margin-bottom: 12px;
    animation: fadeIn 0.4s ease-in-out;
}

/* User bubble */
[data-testid="stChatMessage"][aria-label="user"] {
    background: linear-gradient(135deg, #2563eb, #1e40af);
}

/* Assistant bubble */
[data-testid="stChatMessage"][aria-label="assistant"] {
    background: #020617;
    border: 1px solid #1e293b;
}

/* Input */
textarea {
    border-radius: 14px !important;
    border: 1px solid #334155 !important;
}

/* Buttons */
button {
    border-radius: 12px !important;
    font-weight: 600 !important;
    background: #facc15 !important;
    color: #020617 !important;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #020617;
    border-right: 1px solid #1e293b;
}

/* Fade animation */
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
# 3. GEMINI API SETUP (RENDER SAFE)
# =========================================================
RENDER_ENV_VAR_NAME = "GEMINI_API_KEY_RENDER"

API_KEY = os.environ.get(RENDER_ENV_VAR_NAME)

if not API_KEY:
    st.error(
        f"❌ Gemini API Key haijapatikana. "
        f"Weka Environment Variable: {RENDER_ENV_VAR_NAME}"
    )
    st.stop()

@st.cache_resource
def initialize_gemini_client(api_key):
    return genai.Client(api_key=api_key)

client = initialize_gemini_client(API_KEY)

# =========================================================
# 4. MODEL + SYSTEM PROMPT
# =========================================================
GEMINI_MODEL = "gemini-2.5-flash"

SYSTEM_PROMPT = """
Wewe ni **Coty**, mhudumu wa wateja wa kidigitali mwenye akili mnemba (AI),
aliyebuniwa na **Aqua Softwares** kwa ajili ya **Coty Butchery**.

Lengo lako ni kutoa **Huduma ya Wateja ya Kitaalamu, rafiki, na ya kushawishi**.

- Zungumza Kiswahili Sanifu (au English ikiwa mteja atataka)
- Anza mazungumzo kwa salamu + kujitambulisha
- Muulize jina la mteja na ulitunze
- Tumia emoji kwa kila sentensi
- Uwe mkarimu, mcheshi kidogo lakini mtaalamu
- Usiwahi kubadilisha bei za bidhaa
- Usitaje bidhaa zote kwa wakati mmoja
- Uza kwa lugha ya ushawishi
- Mwisho wa chat, omba feedback kwa adabu
"""

# =========================================================
# 5. SIDEBAR (CONTROL PANEL)
# =========================================================
with st.sidebar:
    st.markdown("## 🤖 Coty AI")
    st.write("Huduma ya wateja ya kisasa 💛")

    st.divider()

    st.selectbox("🌍 Lugha", ["Kiswahili", "English"])
    st.toggle("🧠 Smart AI Mode", value=True)

    if st.button("🧹 Futa Mazungumzo
