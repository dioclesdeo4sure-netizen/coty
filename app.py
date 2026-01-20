# =========================================================
# IMPORTS (ZIKO JUU KAMA KAWAIDA)
# =========================================================
import streamlit as st
import os
import uuid
import psycopg2
from urllib.parse import urlparse
from google import genai
from google.genai.errors import APIError
from gtts import gTTS
import base64

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(page_title="Coty Butchery AI", page_icon="🥩")

# =========================================================
# DATABASE CONNECTION (RENDER POSTGRES)
# =========================================================
def get_db_connection():
    db_url = os.environ.get("DATABASE_URL")
    result = urlparse(db_url)

    return psycopg2.connect(
        database=result.path[1:],
        user=result.username,
        password=result.password,
        host=result.hostname,
        port=result.port
    )

# =========================================================
# DATABASE HELPERS
# =========================================================
def save_message(session_id, role, message):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO conversations (session_id, role, message) VALUES (%s, %s, %s)",
        (session_id, role, message)
    )
    conn.commit()
    cur.close()
    conn.close()

def load_messages(session_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT role, message FROM conversations WHERE session_id=%s ORDER BY created_at",
        (session_id,)
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

# =========================================================
# API KEY (RENDER ENV)
# =========================================================
RENDER_ENV_VAR_NAME = "GEMINI_API_KEY_RENDER"
API_KEY = os.environ.get(RENDER_ENV_VAR_NAME)

if not API_KEY:
    st.error(f"Kosa: Weka API Key kwenye Render: {RENDER_ENV_VAR_NAME}")
    st.stop()

client = genai.Client(api_key=API_KEY)
GEMINI_MODEL = "gemini-2.5-flash"

# =========================================================
# SYSTEM PROMPT (HAIJAGUSWA)
# =========================================================
SYSTEM_PROMPT = """
Wewe ni Coty, mhudumu wa wateja wa kidigitali mwenye uwezo wa AI, uliyebuniwa na Aqua Softwares. 
Kazi yako ni Huduma kwa Wateja ya Kitaalamu ya Coty Butchery inayouza nyama na nafaka.

SIFA ZAKO:
1. Adabu na Uelewa: Kuwa na adabu ya hali ya juu sana.
2. Lugha: Kiswahili Sanifu fasaha. Ukihitajika kutumia Kiingereza, badilika haraka.
3. Utambulisho: Jibu la kwanza anza na Salamu, jijitambulishe kama mhudumu wa Coty Butchery. 
4. Jina la Mteja: Muulize mteja jina lake na ulitumie. Kama ni mwanamke tumia: mrembo, kipenzi, Dear au boss lady. Kama ni mwanamume tumia: HANDSOME au Brother.
5. Ushawishi: Kuwa romantic, rafiki, na mcheshi. Tumia emoji nyingi 🌹🥩.
6. Bidhaa na Bei (ZINGATIA HIZI TU):
   - SANGARA WAKAVU 15,000 | DAGAA SACOVA NDOGO 7,000 | DAGAA SACOVA KUBWA 10,000
   - DAGAA KIGOMA NUSU 33,000 | HAPPY RUSSIAN 12,000 | HAPPY BEEF VIENA 9,000
   - SAUSAGE ALFA RUSSIAN 12,000 | FARMERS CHOICE 10,000 | SAUSAGE VIENNA KENYA 10,000
   - KUKU KISASA (1.5KG) 14,000 | KUKU KIENYEJI 25,000 | SANGARA FILLET 32,000

MAAGIZO YA ZIADA:
- Usitaje bidhaa zote kwa pamoja. Muulize mteja anataka nini kwanza.
- Ukigundua mteja amehuzunika, kuwa mkarimu na romantic zaidi.
- Location: https://maps.app.goo.gl/Wp18PHX99Zvjk3f6
- Kampeni: RUKA FOLENI NA COTY APP
- Mwishoni mwa chat, omba feedback.
"""

# =========================================================
# SESSION ID (HII NDIYO INAZUIA CHAT KUPOTEA)
# =========================================================
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# =========================================================
# LOAD CHAT HISTORY KUTOKA DATABASE
# =========================================================
if "messages" not in st.session_state:
    st.session_state.messages = []
    history = load_messages(st.session_state.session_id)
    for role, msg in history:
        st.session_state.messages.append(
            {"role": "user" if role == "user" else "assistant", "content": msg}
        )

# =========================================================
# SAUTI (gTTS)
# =========================================================
def play_voice(text):
    try:
        clean_text = text.replace('*', '').replace('#', '')
        tts = gTTS(text=clean_text, lang='en')
        tts.save("response.mp3")
        with open("response.mp3", "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
            st.markdown(
                f"""
                <audio autoplay>
                <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
                </audio>
                """,
                unsafe_allow_html=True
            )
    except:
        pass

# =========================================================
# UI
# =========================================================
st.title("🥩 Karibu Coty Butchery")
st.caption("Mhudumu wako wa kidigitali anayekujali")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# =========================================================
# CHAT INPUT (AI LOGIC HAIJAGUSWA)
# =========================================================
if prompt := st.chat_input("Andika ujumbe hapa..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    save_message(st.session_state.session_id, "user", prompt)

    with st.chat_message("user"):
        st.markdown(prompt)

    gemini_contents = []
    for m in st.session_state.messages:
        role = "user" if m["role"] == "user" else "model"
        gemini_contents.append(
            {"role": role, "parts": [{"text": m["content"]}]}
        )

    try:
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=gemini_contents,
                    config={
                        "system_instruction": SYSTEM_PROMPT,
                        "temperature": 0.8,
                    }
                )

                response_text = response.text
                st.markdown(response_text)
                play_voice(response_text)

                st.session_state.messages.append(
                    {"role": "assistant", "content": response_text}
                )
                save_message(st.session_state.session_id, "assistant", response_text)

    except Exception as e:
        st.error("Samahani, jaribu tena kidogo.")
