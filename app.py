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
# DATABASE
# =============================
def get_db_connection():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        st.error("DATABASE_URL haipo kwenye environment variables")
        st.stop()
    result = urlparse(db_url)
    return psycopg2.connect(
        database=result.path[1:],
        user=result.username,
        password=result.password,
        host=result.hostname,
        port=result.port
    )

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

def save_customer(phone, name):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO customers (phone_number, customer_name)
        VALUES (%s, %s)
        ON CONFLICT (phone_number) DO UPDATE
        SET customer_name = EXCLUDED.customer_name
    """, (phone, name))
    conn.commit()
    cur.close()
    conn.close()

def load_customer(phone):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT customer_name FROM customers WHERE phone_number = %s", (phone,))
    r = cur.fetchone()
    cur.close()
    conn.close()
    return r[0] if r else None

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
        WHERE phone_number = %s ORDER BY created_at
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
- Kwanza uliza jina la mteja ikiwa haijulikani.
- Kisha ulize namba ya simu ikiwa haijulikani.
- Usirudie kuuliza jina au simu mara nyingi.
- Kumbuka jina na simu yake.
- Mazungumzo yote ya zamani yanasomeka kwenye historia.
- Kama mteja anaandika order/oda, weka kama order.
"""

# =============================
# SESSION STATE
# =============================
if "phone" not in st.session_state:
    st.session_state.phone = ""
if "name" not in st.session_state:
    st.session_state.name = ""

st.title("🥩 Coty AI Customer Chat")

# =============================
# Display chat history if phone known
# =============================
if st.session_state.phone:
    history = load_messages(st.session_state.phone)
    for role, msg in history:
        with st.chat_message(role):
            st.markdown(msg)

# =============================
# Chat user input
# =============================
user_input = st.chat_input("Andika hapa...")

if user_input:
    phone = st.session_state.phone
    name = st.session_state.name

    # If no phone known yet, use placeholder
    if not phone:
        phone = "unknown_phone"

    save_message(phone, "user", user_input)
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.spinner("🤖 Inafikiria..."):
        # If name is not yet known, first ask for it
        if not name:
            prompt = f"""{SYSTEM_PROMPT}
Historia ya mazungumzo:
{user_input}

Uliza jina la mteja na namba ya simu.
"""
            response = client.models.generate_content(
                model=MODEL,
                contents=prompt
            )
            reply = response.text

            # Attempt to parse name and phone from reply text
            # (Optional: better parsing rules can be added)
            tokens = user_input.split()
            if len(tokens) >= 2:
                # Treat first token as name and last as phone
                guessed_name = tokens[0]
                guessed_phone = tokens[-1]
                st.session_state.name = guessed_name
                st.session_state.phone = guessed_phone
                save_customer(guessed_phone, guessed_name)

        else:
            text_lower = user_input.lower()
            # Detect order keywords
            if any(x in text_lower for x in ["oda", "order", "kilo", "kg"]):
                save_order(phone, name, user_input)
                reply = f"Asante {name}! Oda yako nimeipokea na kuipeleka kwa admin."
            else:
                # Build context
                history = load_messages(phone)
                context = "\n".join([f"{r}:{m}" for r, m in history[-15:]])
                prompt = f"""{SYSTEM_PROMPT}
Mteja: {name}, simu: {phone}
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

