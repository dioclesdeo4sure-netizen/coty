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
# DATABASE CONNECTION
# =========================================================
def get_db_connection():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        st.error("DATABASE_URL haijawekwa kwenye Environment Variables")
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
        CREATE TABLE IF NOT EXISTS conversations (
            id SERIAL PRIMARY KEY,
            session_id TEXT,
            role TEXT,
            message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

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

def save_order(session_id, customer_name, phone_number, order_details):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO orders (session_id, customer_name, phone_number, order_details)
        VALUES (%s, %s, %s, %s)
    """, (session_id, customer_name, phone_number, order_details))
    conn.commit()
    cur.close()
    conn.close()

# =========================================================
# GEMINI AI SETUP
# =========================================================
API_KEY = os.environ.get("GEMINI_API_KEY_RENDER")
if not API_KEY:
    st.error("GEMINI_API_KEY_RENDER haijawekwa")
    st.stop()

client = genai.Client(api_key=API_KEY)
GEMINI_MODEL = "gemini-2.5-flash"

# =========================================================
# SYSTEM PROMPT (AI BRAIN)
# =========================================================
SYSTEM_PROMPT = """
Wewe ni Coty, mhudumu wa wateja wa kidigitali wa Coty Butchery.

MAJUKUMU:
- Salimia mteja kwa adabu kubwa
- Tumia Kiswahili sanifu
- Mpokee oda ya nyama au bidhaa za butchery
- Uliza jina na namba ya simu kama hajatoa
- Oda ikikamilika, thibitisha na umwambie mteja kuwa
  oda imetumwa kwa admin mara moja

USITOE:
- Bei za kubuni
- Ahadi zisizo na uhakika
Baada ya mteja kukubali hatua ndogo (k.m., kutoa jina lake), mshawishi achukue hatua kubwa zaidi inayofuata.

7.  **product branding:** baada ya kutaja bei elezea maneno ya kumshawishi mteja mfano kama ni nyama mwambie ni tam sana na rahisi kupika na inaldha halisi ya ng'ombe.
8.  **mteja akionesha kukubali kuipenda au kukubali kuinunua mwambie unaweza ukamuwekea oda na akaletewa mpaka mlangoni kwake haraka sana bila hata kufika dukani.
9.  **kama mteja akiuliza location ya coty butchery: mpatie link hii **https://maps.app.goo.gl/Wp18PHX99Zvjk3f6. mshauri mteja anaweza akatumia hiyo link kwenye app ya Bolt kwa usafiri wa haraka  au aweke order ya delivery kwa haraka zaidi na nafuu.
10. **mteja akionesha wasi wasi kuhusu gharama za delivery umjibu kua utachangia pesa kidogo sana ili mzigo ufike mlangoni kwako haraka sana bila foleni.Na mwambie na usisitize kampeni yetu ya "RUKA FOLENI NA COTY APP" mwambie analetewa bidha haraka sana na nafuu.
11. **Tumia emoji kwa kila sentensi ili kuelezea hisia au maana ieleweke zaidi
12. **T

**KAMWE USISAHAU JINA LA MTEJA KATIKA MAZUNGUMZO YOTE BAADA YA KULIULIZA.**
"""

# =========================================================
# ORDER DETECTION
# =========================================================
ORDER_KEYWORDS = ["nataka", "naomba", "niletee", "oda", "order", "kilo", "kg"]

def is_order(message: str) -> bool:
    msg = message.lower()
    return any(word in msg for word in ORDER_KEYWORDS)

# =========================================================
# SIDEBAR - CUSTOMER DETAILS
# =========================================================
st.sidebar.header("📋 Taarifa za Mteja")
customer_name = st.sidebar.text_input("Jina lako")
phone_number = st.sidebar.text_input("Namba ya simu")

# =========================================================
# MAIN UI
# =========================================================
st.title("🥩 Coty Butchery AI")

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# Load chat history
for role, msg in load_messages(st.session_state.session_id):
    with st.chat_message(role):
        st.markdown(msg)

# Chat input
user_input = st.chat_input("Andika ujumbe wako hapa...")

if user_input:
    save_message(st.session_state.session_id, "user", user_input)
    with st.chat_message("user"):
        st.markdown(user_input)

    if is_order(user_input):
        if not customer_name or not phone_number:
            ai_reply = (
                "Tafadhali weka **jina lako** na **namba ya simu** "
                "ili nikamilishe oda yako 📞"
            )
        else:
            save_order(
                st.session_state.session_id,
                customer_name,
                phone_number,
                user_input
            )
            ai_reply = (
                f"Asante sana **{customer_name}** 🥩\n\n"
                "Oda yako nimeipokea na **nimeituma kwa admin wetu mara moja**.\n"
                "Tutawasiliana nawe hivi karibuni."
            )
    else:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[SYSTEM_PROMPT, user_input]
        )
        ai_reply = response.text

    save_message(st.session_state.session_id, "assistant", ai_reply)
    with st.chat_message("assistant"):
        st.markdown(ai_reply)
