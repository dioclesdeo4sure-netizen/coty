import streamlit as st
import os
import psycopg2
from urllib.parse import urlparse
from google import genai

# ===============
# PAGE CONFIG
# ===============
st.set_page_config(page_title="Coty Butchery AI", page_icon="🥩", layout="wide")

# ===============
# DATABASE CONNECT
# ===============
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

# ============
# INIT DB
# ============
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        phone_number TEXT PRIMARY KEY,
        customer_name TEXT,
        gender TEXT,
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
        gender TEXT,
        order_details TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()
    cur.close()
    conn.close()

init_db()

# ============
# DB HELPERS
# ============
def save_customer(phone, name, gender):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO customers (phone_number, customer_name, gender)
        VALUES (%s,%s,%s)
        ON CONFLICT (phone_number)
        DO UPDATE SET customer_name=EXCLUDED.customer_name, gender=EXCLUDED.gender
    """, (phone, name, gender))
    conn.commit()
    cur.close()
    conn.close()

def load_customer(phone):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT customer_name, gender FROM customers WHERE phone_number=%s", (phone,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row if row else (None, None)

def save_message(phone, role, message):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO conversations (phone_number, role, message) VALUES (%s,%s,%s)",
                (phone, role, message))
    conn.commit()
    cur.close()
    conn.close()

def load_messages(phone):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT role,message FROM conversations WHERE phone_number=%s ORDER BY created_at", (phone,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

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

# ============
# GEMINI AI
# ============
API_KEY = os.environ.get("GEMINI_API_KEY_RENDER")
if not API_KEY:
    st.error("GEMINI_API_KEY_RENDER haijawekwa")
    st.stop()

client = genai.Client(api_key=API_KEY)
MODEL = "gemini-2.5-flash"

SYSTEM_PROMPT = """
Wewe ni Coty, mhudumu wa wateja wa Coty Butchery.
Jibu kwa upole na uelewa.
Tumia jina la mteja mara kwa mara.
Usisahau mazungumzo ya nyuma.
"""

# ============
# SESSION STATE
# ============
st.session_state.setdefault("logged_in", False)
st.session_state.setdefault("phone", "")
st.session_state.setdefault("name", "")
st.session_state.setdefault("gender", "")
st.session_state.setdefault("refresh_key", 0)

# ============
# LOGIN FORM
# ============
if not st.session_state.logged_in:
    st.title("🥩 Coty Butchery AI Chat")
    st.write("Tafadhali jaza taarifa zako")
    with st.form("login"):
        name_input = st.text_input("Jina lako")
        phone_input = st.text_input("Namba ya simu")
        gender_input = st.selectbox("Jinsia", ["Kiume", "Kike"])
        submit = st.form_submit_button("Endelea")

        if submit:
            if not name_input or not phone_input:
                st.error("Jina na simu ni lazima")
            else:
                save_customer(phone_input, name_input, gender_input)
                st.session_state.phone = phone_input
                st.session_state.name = name_input
                st.session_state.gender = gender_input
                st.session_state.logged_in = True
                st.success(f"Karibu {name_input}")
                st.experimental_rerun()

# ============
# CHAT INTERFACE
# ============
if st.session_state.logged_in:
    phone = st.session_state.phone
    name = st.session_state.name
    gender = st.session_state.gender

    st.caption(f"👤 {name} | 📞 {phone} | 👤 Jinsia: {gender}")

    # Load history
    history = load_messages(phone)
    for role, msg in history:
        with st.chat_message(role):
            st.markdown(msg)

    # Input area
    user_input = st.chat_input("Andika hapa...")

    if user_input:
        save_message(phone, "user", user_input)
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.spinner("🤖 Thinking..."):
            # If order
            if "oda" in user_input.lower() or "order" in user_input.lower():
                save_order(phone, name, gender, user_input)
                reply = f"Asante {name}! Oda yako nimeipokea na nimeituma kwa admin."
            else:
                # Build context for Gemini
                context = "\n".join([f"{r}:{m}" for r, m in history[-15:]])
                prompt = f"""{SYSTEM_PROMPT}
Mteja: {name}, Jinsia: {gender}
Historia:
{context}

Swali: {user_input}
"""

                response = client.models.generate_content(
                    model=MODEL,
                    contents=prompt
                )
                reply = response.text

        save_message(phone, "assistant", reply)
        with st.chat_message("assistant"):
            st.markdown(reply)

    # Auto refresh UI ya chat kila sekunde 5
    st.experimental_set_query_params(refresh=int(st.session_state.refresh_key))
    st.session_state.refresh_key += 1
    st.experimental_rerun()

