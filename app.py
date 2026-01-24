import streamlit as st
import os
import psycopg2
from urllib.parse import urlparse
from google import genai

# =============================
# PAGE CONFIG
# =============================
st.set_page_config(page_title="Coty AI Customer Chat", page_icon="🥩", layout="wide")

# =============================
# DATABASE CONNECTION
# =============================
def get_db_connection():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        st.error("DATABASE_URL haipo")
        st.stop()
    result = urlparse(db_url)
    return psycopg2.connect(
        database=result.path[1:],
        user=result.username,
        password=result.password,
        host=result.hostname,
        port=result.port
    )

# =============================
# INIT DB TABLES (IF NOT EXISTS)
# =============================
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    # customers with gender
    cur.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        phone_number TEXT PRIMARY KEY,
        customer_name TEXT,
        gender TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # conversations
    cur.execute("""
    CREATE TABLE IF NOT EXISTS conversations (
        id SERIAL PRIMARY KEY,
        phone_number TEXT,
        role TEXT,
        message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # orders with gender
    cur.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id SERIAL PRIMARY KEY,
        phone_number TEXT,
        customer_name TEXT,
        gender TEXT,
        order_details TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()
    cur.close()
    conn.close()

init_db()

# =============================
# HELPER FUNCTIONS
# =============================
def save_customer(phone, name, gender):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO customers (phone_number, customer_name, gender)
        VALUES (%s,%s,%s)
        ON CONFLICT (phone_number) DO UPDATE
        SET customer_name=EXCLUDED.customer_name, gender=EXCLUDED.gender
    """, (phone, name, gender))
    conn.commit()
    cur.close()
    conn.close()

def load_messages(phone):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT role, message FROM conversations
        WHERE phone_number=%s ORDER BY created_at
    """, (phone,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def save_message(phone, role, message):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO conversations (phone_number, role, message)
        VALUES (%s,%s,%s)
    """, (phone, role, message))
    conn.commit()
    cur.close()
    conn.close()

def save_order(phone, name, gender, details):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO orders (phone_number, customer_name, gender, order_details)
        VALUES (%s,%s,%s,%s)
    """, (phone, name, gender, details))
    conn.commit()
    cur.close()
    conn.close()

# =============================
# GEMINI AI INIT
# =============================
GEMINI_KEY = os.environ.get("GEMINI_API_KEY_RENDER")
if not GEMINI_KEY:
    st.error("GEMINI_API_KEY_RENDER haijawekwa")
    st.stop()

client = genai.Client(api_key=GEMINI_KEY)
MODEL = "gemini-2.5-flash"

SYSTEM_PROMPT = """
Wewe ni Coty, mhudumu wa wateja wa Coty Butchery.
Jibu kwa upole na tumia jina la mteja mara kwa mara.
Kumbuka mazungumzo yote ya nyuma.
"""

# =============================
# SESSION STATE
# =============================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "phone" not in st.session_state:
    st.session_state.phone = ""
if "name" not in st.session_state:
    st.session_state.name = ""
if "gender" not in st.session_state:
    st.session_state.gender = ""

# =============================
# LOGIN FORM
# =============================
if not st.session_state.logged_in:
    st.title("🥩 Coty Butchery AI Chat")
    st.write("Tafadhali jaza taarifa zako")

    with st.form("login"):
        name_input = st.text_input("Jina lako")
        phone_input = st.text_input("Namba ya simu")
        gender_input = st.selectbox("Jinsia yako", ["Kiume", "Kike"])
        submit = st.form_submit_button("Endelea")

        if submit:
            if not name_input.strip() or not phone_input.strip():
                st.error("Jina na namba ya simu ni lazima")
            else:
                save_customer(phone_input, name_input, gender_input)
                st.session_state.name = name_input
                st.session_state.phone = phone_input
                st.session_state.gender = gender_input
                st.session_state.logged_in = True
                st.success(f"Karibu {name_input}")
                st.experimental_rerun()

# =============================
# CHAT & INTERACTION
# =============================
if st.session_state.logged_in:
    phone = st.session_state.phone
    name = st.session_state.name
    gender = st.session_state.gender

    st.caption(f"👤 {name} | 📞 {phone} | Jinsia: {gender}")

    # show past history
    chat_history = load_messages(phone)
    for role, msg in chat_history:
        with st.chat_message(role):
            st.markdown(msg)

    # chat input
    message = st.chat_input("Andika ujumbe wako...")

    if message:
        save_message(phone, "user", message)
        with st.chat_message("user"):
            st.markdown(message)

        with st.spinner("🤖 Thinking..."):
            # detect order
            low = message.lower()
            if "oda" in low or "order" in low or "kilo" in low or "kg" in low:
                # highlight this as order
                save_order(phone, name, gender, message)
                reply = f"Asante {name}! Oda yako nimeipokea na nimeituma kwa admin."
            else:
                # prepare context & prompt
                context = "\n".join([f"{r}:{m}" for r, m in chat_history[-10:]])
                prompt = f"""{SYSTEM_PROMPT}

Mteja: {name} (Jinsia: {gender})
Historia:
{context}

Swali: {message}
"""
                # call Gemini
                resp = client.models.generate_content(
                    model=MODEL,
                    contents=prompt
                )
                reply = resp.text

        save_message(phone, "assistant", reply)
        with st.chat_message("assistant"):
            st.markdown(reply)

    # =============================
    # SAFE AUTO-REFRESH
    # =============================
    st_autorefresh(interval=5000, key="chat_refresh")
