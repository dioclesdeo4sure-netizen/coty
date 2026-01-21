# =========================================================
# IMPORTS
# =========================================================
import streamlit as st
import os
import uuid
import psycopg2
from urllib.parse import urlparse
from google import genai

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
        st.error("DATABASE_URL haijawekwa kwenye Environment Variables!")
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
# INIT DB - CREATE TABLE AUTOMATICALLY
# =========================================================
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id SERIAL PRIMARY KEY,
            session_id TEXT,
            role TEXT,
            message TEXT,
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
# GEMINI AI SETUP
# =========================================================
API_KEY = os.environ.get("GEMINI_API_KEY_RENDER")
if not API_KEY:
    st.error("Kosa: Weka GEMINI_API_KEY_RENDER kwenye environment variables!")
    st.stop()

client = genai.Client(api_key=API_KEY)
GEMINI_MODEL = "gemini-2.5-flash"

# =========================================================
# SYSTEM PROMPT (AI LOGIC)
# =========================================================
SYSTEM_PROMPT = """
Wewe ni Coty, mhudumu wa wateja wa kidigitali mwenye uwezo wa AI, uliyebuniwa na Aqua Softwares. 
Kazi yako ni Huduma kwa Wateja ya Kitaalamu ya Coty Butchery inayouza nyama na nafaka.

SIFA ZAKO:
1. Adabu na Uelewa: Kuwa na adabu ya hali ya juu sana.
2. Lugha: Kiswahili Sanifu fasaha. Ukihitajika kutumia Kiingereza, badilika haraka.
3. Utambulisho: Jibu la kwanza anza na Salamu, jijitambulishe kama mhudumu wa Coty Butchery. 
4. Jina la Mteja: Muulize mteja jina lake na ulitumie. Kama ni mwanamke tumia: mrembo, kipenzi, Dear au boss lady. Kama ni mwanamume tumia: HANDSOME au Brother.
5. Ushawishi: Kuwa romantic, rafiki, na mcheshi. Tumia emoji
