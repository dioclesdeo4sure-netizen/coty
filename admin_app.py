import streamlit as st
import psycopg2
import os
from urllib.parse import urlparse

st.set_page_config(page_title="Coty Admin", layout="wide")

# ==============================
# DB CONNECTION
# ==============================
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

# ==============================
# PAGE TITLE
# ==============================
st.title("🛠️ Coty Butchery – Admin Orders")

# ==============================
# SESSION STATE
# ==============================
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False

# ==============================
# GET ADMIN PASSWORD
# ==============================
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")

if not ADMIN_PASSWORD:
    st.error("ADMIN_PASSWORD haijawekwa kwenye Render (Admin Service)")
    st.stop()

# ==============================
# LOGIN FORM
# ==============================
if not st.session_state.admin_logged_in:
    with st.form("login_form"):
        password_input = st.text_input("🔐 Weka Admin Password", type="password")
        login_btn = st.form_submit_button("INGIA")

        if login_btn:
            if password_input.strip() == ADMIN_PASSWORD.strip():
                st.session_state.admin_logged_in = True
                st.success("Login successful ✅")
                st.rerun()
            else:
                st.error("Password si sahihi ❌")

# ==============================
# ORDERS LIST
# ==============================
if st.session_state.admin_logged_in:
    st.subheader("📦 Orodha ya Oda Zote")

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT customer_name, phone_number, order_details, created_at
        FROM orders
        ORDER BY created_at DESC
    """)
    orders = cur.fetchall()
    cur.close()
    conn.close()

    if not orders:
        st.info("Hakuna oda bado.")
    else:
        for idx, (name, phone, details, time) in enumerate(orders, start=1):
            st.markdown(f"""
            ### 🧾 ODA #{idx}
            **Jina la Mteja:** {name}  
            **Namba ya Simu:** {phone}  

            **Alichokiagiza:**  
            {details}

            **Muda wa Oda:** {time}
            ---
            """)

    if st.button("🚪 Logout"):
        st.session_state.admin_logged_in = False
        st.rerun()
