import streamlit as st
import psycopg2
import os
from urllib.parse import urlparse

st.set_page_config(page_title="Coty Admin", layout="wide")

# ==============================
# DB CONNECTION
# ==============================
def get_db_connection():
    result = urlparse(os.environ["DATABASE_URL"])
    return psycopg2.connect(
        database=result.path[1:],
        user=result.username,
        password=result.password,
        host=result.hostname,
        port=result.port
    )

st.title("🛠️ Coty Butchery - Admin Dashboard")

# ==============================
# SESSION STATE
# ==============================
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False

# ==============================
# LOGIN FORM
# ==============================
if not st.session_state.admin_logged_in:

    with st.form("admin_login_form"):
        password = st.text_input("🔐 Ingiza Admin Password", type="password")
        login_btn = st.form_submit_button("INGIA")

        if login_btn:
            if password == os.environ.get("ADMIN_PASSWORD"):
                st.session_state.admin_logged_in = True
                st.success("Login successful ✅")
                st.experimental_rerun()
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
        for i, (name, phone, order, time) in enumerate(orders, start=1):
            st.markdown(f"""
            ### 🧾 ODA #{i}
            **Jina:** {name}  
            **Simu:** {phone}  
            **Maelezo ya Oda:**  
            {order}  

            **Muda:** {time}
            ---
            """)

    if st.button("🚪 Toka (Logout)"):
        st.session_state.admin_logged_in = False
        st.experimental_rerun()
