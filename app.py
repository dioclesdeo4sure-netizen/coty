# =========================================================
# IMPORTS
# =========================================================
import streamlit as st
import os
import uuid
import psycopg2
from urllib.parse import urlparse
from google import genai
from gtts import gTTS
import base64

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(page_title="Coty Butchery AI", page_icon="🥩", layout="wide")

# =========================================================
# DATABASE CONNECTION
# =========================================================
def get_db_connection():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        st.error("DATABASE_URL haijawekwa!")
        st.stop()

    result = urlparse(db_url)
    return psycopg2.connect(
        database=result.path[1:],
        user=result.username,
        password=result.password,
        host=result.hostname,
        port=result.port
    )

# =========================================================
# INIT DB
# =========================================================
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    # CHAT HISTORY
    cur.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id SERIAL PRIMARY KEY,
            session_id TEXT,
            role TEXT,
            message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # ORDERS
    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id SERIAL PRIMARY KEY,
            session_id TEXT,
            customer_name TEXT,
            phone_number TEXT,
            order_details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()
    cur.close()
    conn.close()

init_db()

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

def save_order(session_id, name, phone, details):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO orders (session_id, customer_name, phone_number, order_details)
        VALUES (%s, %s, %s, %s)
        """,
        (session_id, name, phone, details)
    )
    conn.commit()
    cur.close()
    conn.close()

# =========================================================
# GEMINI SETUP
# =========================================================
API_KEY = os.environ.get("GEMINI_API_KEY_RENDER")
if not API_KEY:
    st.error("Weka GEMINI_API_KEY_RENDER")
    st.stop()

client = genai.Client(api_key=API_KEY)
MODEL = "gemini-2.5-flash"

# =========================================================
# SYSTEM PROMPT
# =========================================================
SYSTEM_PROMPT = """
Wewe ni Coty, mhudumu wa wateja wa kidigitali wa Coty Butchery.

Lugha: Kiswahili Sanifu.
Tabia: Mpole, romantic, mcheshi 🌹🥩.

Bidhaa na bei (ZINGATIA HIZI TU):
- SANGARA WAKAVU 15,000
- DAGAA SACOVA NDOGO 7,000
- DAGAA SACOVA KUBWA 10,000
- DAGAA KIGOMA NUSU 33,000
- HAPPY RUSSIAN 12,000
- HAPPY BEEF VIENA 9,000
- SAUSAGE ALFA RUSSIAN 12,000
- FARMERS CHOICE 10,000
- SAUSAGE VIENNA KENYA 10,000
- KUKU KISASA (1.5KG) 14,000
- KUKU KIENYEJI 25,000
- SANGARA FILLET 32,000

MAAGIZO MUHIMU:
1. Salamu kwanza, jitambulishe.
2. Muulize mteja jina lake.
3. Muulize namba ya simu.
4. Mteja akishachagua bidhaa, thibitisha oda.
5. Usitaje bidhaa zote kwa wakati mmoja.
6. Ukishapata jina + simu + bidhaa, sema:
   "Oda yako imepokelewa kikamilifu 🌹🥩"
"""

# =========================================================
# SESSION
# =========================================================
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

if "customer_name" not in st.session_state:
    st.session_state.customer_name = ""

if "phone_number" not in st.session_state:
    st.session_state.phone_number = ""



# =========================================================
# UI
# =========================================================
st.title("🥩 Coty Butchery AI")
st.caption("Huduma bora, kwa mapenzi 🌹")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Andika ujumbe..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    save_message(st.session_state.session_id, "user", prompt)

    # capture name & phone simple
    if "jina langu" in prompt.lower():
        st.session_state.customer_name = prompt
    if any(char.isdigit() for char in prompt):
        st.session_state.phone_number = prompt

    contents = []
    for m in st.session_state.messages:
        role = "user" if m["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": m["content"]}]})

    response = client.models.generate_content(
        model=MODEL,
        contents=contents,
        config={"system_instruction": SYSTEM_PROMPT}
    )

    reply = response.text

    with st.chat_message("assistant"):
        st.markdown(reply)
        play_voice(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})
    save_message(st.session_state.session_id, "assistant", reply)

    # SAVE ORDER
    if "imepokelewa" in reply.lower():
        save_order(
            st.session_state.session_id,
            st.session_state.customer_name or "Haikutolewa",
            st.session_state.phone_number or "Haikutolewa",
            reply
        )
