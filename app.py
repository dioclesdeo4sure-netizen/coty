import streamlit as st
import os
import psycopg2
from urllib.parse import urlparse
from google import genai

# =============================
# PAGE CONFIG
# =============================
st.set_page_config(page_title="Coty Butchery AI", page_icon="🥩", layout="wide")

# =============================
# DATABASE CONNECTION
# =============================
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

# =============================
# INIT DB
# =============================
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    # Customers table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        phone_number TEXT PRIMARY KEY,
        customer_name TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Conversations table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS conversations (
        id SERIAL PRIMARY KEY,
        phone_number TEXT,
        role TEXT,
        message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Orders table
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

# =============================
# DATABASE HELPERS
# =============================
def save_customer(phone, name):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO customers (phone_number, customer_name)
        VALUES (%s,%s)
        ON CONFLICT (phone_number)
        DO UPDATE SET customer_name=EXCLUDED.customer_name
    """, (phone,name))
    conn.commit()
    cur.close()
    conn.close()

def load_customer(phone):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT customer_name FROM customers WHERE phone_number=%s", (phone,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else None

def save_message(phone, role, message):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO conversations (phone_number, role, message) VALUES (%s,%s,%s)", (phone, role, message))
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

def save_order(phone, name, details):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO orders (phone_number, customer_name, order_details) VALUES (%s,%s,%s)", (phone,name,details))
    conn.commit()
    cur.close()
    conn.close()

# =============================
# GEMINI AI
# =============================
API_KEY = os.environ.get("GEMINI_API_KEY_RENDER")
if not API_KEY:
    st.error("GEMINI_API_KEY_RENDER haijawekwa")
    st.stop()

client = genai.Client(api_key=API_KEY)
MODEL = "gemini-2.5-flash"

SYSTEM_PROMPT = """
Wewe ni Coty, mhudumu wa wateja wa Coty Butchery.
- Usisahau jina la mteja
- Tumia jina mara kwa mara
- Usirudie kuuliza jina au simu
- Kumbuka mazungumzo yote ya nyuma
- Kuwa mcheshi, mpole, na mshawishi
"""

ORDER_WORDS = ["nataka","naomba","kilo","kg","order","oda"]

# =============================
# SESSION STATE INIT
# =============================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "phone" not in st.session_state:
    st.session_state.phone = ""
if "name" not in st.session_state:
    st.session_state.name = ""

# =============================
# LOGIN FORM (MARA 1 TU)
# =============================
if not st.session_state.logged_in:
    st.title("🥩 Coty Butchery AI")
    st.header("📋 Ingiza taarifa zako")
    with st.form(key="login_form", clear_on_submit=False):
        name_input = st.text_input("Jina lako", value=st.session_state.name)
        phone_input = st.text_input("Namba ya simu", value=st.session_state.phone)
        submit_btn = st.form_submit_button("ANZA")

        if submit_btn:
            if not name_input.strip() or not phone_input.strip():
                st.error("Tafadhali jaza jina na namba ya simu sahihi")
            else:
                save_customer(phone_input.strip(), name_input.strip())
                st.session_state.phone = phone_input.strip()
                st.session_state.name = name_input.strip()
                st.session_state.logged_in = True
                st.success(f"Karibu {name_input.strip()} 🥩")
                st.experimental_rerun()

# =============================
# CHAT INTERFACE
# =============================
if st.session_state.logged_in:
    phone = st.session_state.phone
    name = st.session_state.name

    st.caption(f"👤 {name} | 📞 {phone}")

    # Display history
    history = load_messages(phone)
    for role,msg in history:
        with st.chat_message(role):
            st.markdown(msg)

    # Input
    user_input = st.chat_input("Andika ujumbe wako...")

    if user_input:
        save_message(phone,"user",user_input)
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.spinner("🤖 Thinking..."):
            # Check if message contains order keywords
            if any(w in user_input.lower() for w in ORDER_WORDS):
                save_order(phone,name,user_input)
                reply=f"Asante sana {name} 🥩\nOda yako nimeipokea na nimeituma kwa admin wetu mara moja."
            else:
                context="\n".join([f"{r}:{m}" for r,m in history[-10:]])
                response=client.models.generate_content(
                    model=MODEL,
                    contents=[SYSTEM_PROMPT,f"Mteja anaitwa {name}. Historia:\n{context}\n\nSwali: {user_input}"]
                )
                reply=response.text

        save_message(phone,"assistant",reply)
        with st.chat_message("assistant"):
            st.markdown(reply)
