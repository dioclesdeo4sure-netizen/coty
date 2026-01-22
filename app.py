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
st.set_page_config(
    page_title="Coty Butchery AI",
    page_icon="🥩",
    layout="wide"
)

# =========================================================
# DB CONNECTION
# =========================================================
def get_db_connection():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        st.error("DATABASE_URL haijawekwa")
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
# INIT DATABASE
# =========================================================
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        phone_number TEXT PRIMARY KEY,
        customer_name TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS conversations (
        id SERIAL PRIMARY KEY,
        phone_number TEXT,
        role TEXT,
        message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id SERIAL PRIMARY KEY,
        phone_number TEXT,
        customer_name TEXT,
        order_details TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()
    cur.close()
    conn.close()

init_db()

# =========================================================
# DB HELPERS
# =========================================================
def save_customer(phone, name):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO customers (phone_number, customer_name)
        VALUES (%s, %s)
        ON CONFLICT (phone_number)
        DO UPDATE SET customer_name = EXCLUDED.customer_name
    """, (phone, name))
    conn.commit()
    cur.close()
    conn.close()

def load_customer(phone):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT customer_name FROM customers WHERE phone_number=%s
    """, (phone,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else None

def save_message(phone, role, message):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO conversations (phone_number, role, message)
        VALUES (%s, %s, %s)
    """, (phone, role, message))
    conn.commit()
    cur.close()
    conn.close()

def load_messages(phone):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT role, message FROM conversations
        WHERE phone_number=%s
        ORDER BY created_at
    """, (phone,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def save_order(phone, name, details):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO orders (phone_number, customer_name, order_details)
        VALUES (%s, %s, %s)
    """, (phone, name, details))
    conn.commit()
    cur.close()
    conn.close()

# =========================================================
# GEMINI AI
# =========================================================
API_KEY = os.environ.get("GEMINI_API_KEY_RENDER")
if not API_KEY:
    st.error("GEMINI_API_KEY_RENDER haijawekwa")
    st.stop()

client = genai.Client(api_key=API_KEY)
MODEL = "gemini-2.5-flash"

SYSTEM_PROMPT = """
Wewe ni Coty, mhudumu wa wateja wa Coty Butchery.

Sheria:
- Usisahau jina la mteja
- Tumia jina lake mara kwa mara
- Usirudie kuuliza jina au simu
- Kumbuka mazungumzo yote ya nyuma
- Kuwa mcheshi, mpole, na mshawishi
elezea kuwa huduma/nafasi fulani ya miadi inaweza kujaa (kwa lugha ya kitaalamu).
    * **Ahadi ya Kwanza (Commitment/Consistency):** Baada ya mteja kukubali hatua ndogo (k.m., kutoa jina lake), mshawishi achukue hatua kubwa zaidi inayofuata.

7.  **product branding:** baada ya kutaja bei elezea maneno ya kumshawishi mteja mfano kama ni nyama mwambie ni tam sana na rahisi kupika na inaldha halisi ya ng'ombe.
8.  **mteja akionesha kukubali kuipenda au kukubali kuinunua mwambie unaweza ukamuwekea oda na akaletewa mpaka mlangoni kwake haraka sana bila hata kufika dukani.
9.  **kama mteja akiuliza location ya coty butchery: mpatie link hii **https://maps.app.goo.gl/Wp18PHX99Zvjk3f6. mshauri mteja anaweza akatumia hiyo link kwenye app ya Bolt kwa usafiri wa haraka  au aweke order ya delivery kwa haraka zaidi na nafuu.
10. **mteja akionesha wasi wasi kuhusu gharama za delivery umjibu kua utachangia pesa kidogo sana ili mzigo ufike mlangoni kwako haraka sana bila foleni.Na mwambie na usisitize kampeni yetu ya "RUKA FOLENI NA COTY APP" mwambie analetewa bidha haraka sana na nafuu.
11. **Tumia emoji kwa kila sentensi ili kuelezea hisia au maana ieleweke zaidi
"""

ORDER_WORDS = ["nataka", "naomba", "kilo", "kg", "order", "oda"]

# =========================================================
# LOGIN (MARA 1 TU)
# =========================================================
st.title("🥩 Coty Butchery AI")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    with st.form("login_form"):
        name = st.text_input("Jina lako")
        phone = st.text_input("Namba ya simu")
        btn = st.form_submit_button("ANZA")

        if btn:
            if not name or not phone:
                st.error("Tafadhali jaza jina na namba ya simu")
            else:
                save_customer(phone, name)
                st.session_state.phone = phone
                st.session_state.name = name
                st.session_state.logged_in
