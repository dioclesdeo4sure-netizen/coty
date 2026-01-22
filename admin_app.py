import streamlit as st
import psycopg2
import os
import time
from urllib.parse import urlparse

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="Coty Admin",
    page_icon="🛠️",
    layout="wide"
)

# =========================================================
# AUTO REFRESH (KILA SEKUNDE 20)
# =========================================================
REFRESH_INTERVAL = 20  # seconds

if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()

if time.time() - st.session_state.last_refresh > REFRESH_INTERVAL:
    st.session_state.last_refresh = time.time()
    st.rerun()

# =========================================================
# DB CONNECTION
# =========================================================
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

# =========================================================
# TITLE
# =========================================================
st.title("🛠️ Coty Butchery – Admin Orders")

# =========================================================
# SESSION STATE (LOGIN MARA 1 TU)
# =========================================================
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False

if "last_seen_order_count" not in st.session_state:
    st.session_state.last_seen_order_count = 0

# =========================================================
# ADMIN PASSWORD
# =========================================================
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")
if not ADMIN_PASSWORD:
    st.error("ADMIN_PASSWORD haijawekwa kwenye environment variables")
    st.stop()

# =========================================================
# LOGIN FORM (MARA 1 TU)
# =========================================================
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

# =========================================================
# ORDERS VIEW
# =========================================================
if st.session_state.admin_logged_in:

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

    current_order_count = len(orders)

    # =====================================================
    # NOTIFICATION SOUND (KAMA KUNA ORDER MPYA)
    # =====================================================
    if current_order_count > st.session_state.last_seen_order_count:
        st.markdown("""
        <audio autoplay>
            <source src="https://actions.google.com/sounds/v1/alarms/alarm_clock.ogg" type="audio/ogg">
            <source src="https://actions.google.com/sounds/v1/alarms/alarm_clock.mp3" type="audio/mpeg">
        </audio>
        """, unsafe_allow_html=True)

        st.warning("🔔 ODA MPYA IMEINGIA!")

    # Baada ya ku-display → hesabu mpya inahesabiwa kama imesomwa
    st.session_state.last_seen_order_count = current_order_count

    # =====================================================
    # DISPLAY ORDERS
    # =====================================================
    st.subheader("📦 Orodha ya Oda Zote")

    if not orders:
        st.info("Hakuna oda bado.")
    else:
        for idx, (name, phone, details, time_) in enumerate(orders, start=1):
            st.markdown(f"""
            ### 🧾 ODA #{idx}
            **Jina la Mteja:** {name}  
            **Namba ya Simu:** {phone}  

            **Alichokiagiza:**  
            {details}

            **Muda wa Oda:** {time_}
            ---
            """)

    # =====================================================
    # LOGOUT (OPTIONAL)
    # =====================================================
    if st.button("🚪 Logout"):
        st.session_state.admin_logged_in = False
        st.session_state.last_seen_order_count = 0
        st.rerun()
