import streamlit as st
import os
from google import genai
from google.genai.errors import APIError

# -------------------------------
# PAGE CONFIG
# -------------------------------
st.set_page_config(
    page_title="Coty Butchery | AI Customer Service",
    page_icon="🥩",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------------
# CUSTOM CSS
# -------------------------------
st.markdown("""
<style>
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: #020617;
    color: #ffffff;
}

h1, h2, h3 {
    color: #22c55e;
}

[data-testid="stChatMessage"] {
    border-radius: 16px;
    padding: 14px;
    margin-bottom: 12px;
    animation: fadeIn 0.35s ease-in-out;
}

/* USER */
[data-testid="stChatMessage"][aria-label="user"] {
    background: linear-gradient(135deg, #2563eb, #1e40af);
    color: #ffffff;
}

/* AI */
[data-testid="stChatMessage"][aria-label="assistant"] {
    background: linear-gradient(135deg, #064e3b, #022c22);
    border: 1px solid #10b981;
    color: #ffffff;
    box-shadow: 0 0 12px rgba(16,185,129,0.35);
}

[data-testid="stChatMessage"][aria-label="assistant"] * {
    color: #ffffff !important;
}
</style>
""", unsafe_allow_html=True)

# -------------------------------
# GEMINI API SETUP
# -------------------------------
RENDER_ENV_VAR_NAME = "GEMINI_API_KEY_RENDER"
API_KEY = os.environ.get(RENDER_ENV_VAR_NAME)

if not API_KEY:
    st.error(f"❌ Gemini API Key haijapatikana ({RENDER_ENV_VAR_NAME})")
    st.stop()

@st.cache_resource
def initialize_gemini_client(api_key):
    return genai.Client(api_key=api_key)

client = initialize_gemini_client(API_KEY)

# -------------------------------
# MODEL + SYSTEM PROMPT
# -------------------------------
GEMINI_MODEL = "gemini-2.5-flash"

SYSTEM_PROMPT = """
* **SANGARA WAKAVU – bei shilingi elfu kumi na tano
* **DAGAA SACOVA NDOGO – bei shilingi elfu saba
* **DAGAA SACOVA KUBWA – bei shilingi elfu kumi
* **DAGAA KIGOMA NUSU – bei shilingi elfu thelathini na tatu
* **HAPPY RUSSIAN – bei shilingi elfu kumi na mbili
* **HAPPY BEEF VIENA – bei shilingi elfu tisa
* **SAUSAGE ALFA RUSSIAN – bei shilingi elfu kumi na mbili
* **FARMERS CHOICE – bei shilingi elfu kumi
* **SAUSAGE VIENNA KENYA – bei shilingi elfu kumi
* **FARMERS CHOICE SPICY/RUSSIAN SPICY – bei shilingi elfu kumi na mbili
* **CHICKEN CHOMA INTERCH – bei shilingi elfu thelathini na tatu
* **COTY BEEF VIENNA SAUSAGE – bei shilingi elfu nane
* **COTY BEEF VIENNA 50 PC – bei shilingi elfu ishirini na mbili
* **BEEF BOEROWERS – bei shilingi elfu kumi na mbili
* **COTY CHICKEN SAUSAGE – bei shilingi elfu nane
* **COTY RUSSIAN CHOMA SAUSAGE – bei shilingi elfu kumi
* **ASAS FRESH 500 MILS – bei shilingi elfu tano
* **ASAS PACKET MTINDI – bei shilingi elfu mbili
* **ASAS YOGHOT KUBWA – bei shilingi elfu mbili
* **ASAS YOGHOT NDOGO – bei shilingi elfu moja
* **ASAS BOX 3 Lita – bei shilingi elfu tano
* **ASAS MTINDI 3 Lita – bei shilingi elfu kumi na tatu
* **ASAS MTINDI 1 liter – bei shilingi elfu tano
* **TANGA CHEESE – bei shilingi elfu kumi na saba
* **BUTTER TANGA – bei shilingi elfu kumi na nane
* **TANGA MTINDI PACKET – bei shilingi elfu mbili
* **BUTTER LATO NDOGO – bei shilingi elfu kumi na mbili
* **COTY FILIGISI – bei shilingi elfu saba na mia tano
* **BREAST – bei shilingi elfu kumi na tatu
* **THIGH BONELESS – bei shilingi elfu sita
* **COTY DRUMSTICK – bei shilingi elfu saba
* **COTY LEGS – bei shilingi elfu saba
* **COTY MGONGO (BACKS) – bei shilingi elfu nne
* **COTY WINGS – bei shilingi elfu kumi na saba
* **COTY THIGH – bei shilingi elfu sita
* **SAMBUSA – bei shilingi elfu kumi
* **KUKU KISASA (1KG) – bei shilingi elfu kumi na nne
* **KUKU KIENYEJI – bei shilingi elfu ishirini na tano
* **SANGARA FILLET – bei shilingi elfu thelathini na mbili
"""

# -------------------------------
# (SEHEMU ZINGINE ZOTE ZIMEACHWA KAMA ZILIVYO)
# -------------------------------
