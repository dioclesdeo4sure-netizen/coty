import streamlit as st
import psycopg2
import os
from urllib.parse import urlparse
import time

st.set_page_config(page_title="Coty Admin", page_icon="🛠️", layout="wide")

# ===========================
# DATABASE CONNECTION
# ===========================
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

# ===========================
# SESSION STATE
# ===========================
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False
if "last_confirmed_order_count" not in st.session_state:
    st.session_state.last_confirmed_order_count = 0
if "notification_active" not in st.session_state:
    st.session_state.notification_active = False

# ===========================
# ADMIN PASSWORD
# ===========================
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")
if not ADMIN_PASSWORD:
    st.error("ADMIN_PASSWORD haijawekwa")
    st.stop()

# ===========================
# LOGIN FORM (MARA 1 TU)
# ===========================
if not st.session_state.admin_logged_in:
    with st.form("login_form"):
        password_input = st.text_input("🔐 Weka Admin Password", type="password")
        login_btn = st.form_submit_button("INGIA")

        if login_btn:
            if password_input.strip() == ADMIN_PASSWORD.strip():
                st.session_state.admin_logged_in = True
                st.success("Login successful ✅")
                st.experimental_rerun()
            else:
                st.error("Password si sahihi ❌")

# ===========================
# MAIN ADMIN PAGE
# ===========================
if st.session_state.admin_logged_in:

    st.title("🛠️ Coty Butchery – Admin Orders")

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

    total_orders = len(orders)

    # ===========================
    # NOTIFICATION LOGIC
    # ===========================
    new_orders = total_orders - st.session_state.last_confirmed_order_count
    if new_orders > 0:
        st.session_state.notification_active = True

    if st.session_state.notification_active:
        st.markdown("""
        <audio autoplay loop>
            <source src="https://assets.mixkit.co/sfx/preview/mixkit-alarm-digital-clock-beep-989.mp3" type="audio/mpeg">
        </audio>
        """, unsafe_allow_html=True)
        st.error(f"🔔 Kuna Oda mpya: {new_orders}")

    # ===========================
    # CONFIRM BUTTON
    # ===========================
    if st.button("✅ CONFIRM ORDER (ZIMA SAUTI)"):
        st.session_state.last_confirmed_order_count = total_orders
        st.session_state.notification_active = False
        st.success("Oda zimethibitishwa. Notification zimezimwa 🔕")
        st.experimental_rerun()

    # ===========================
    # DISPLAY ORDERS
    # ===========================
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

    # ===========================
    # LOGOUT BUTTON
    # ===========================
    if st.button("🚪 Logout"):
        st.session_state.admin_logged_in = False
        st.session_state.last_confirmed_order_count = 0
        st.session_state.notification_active = False
        st.experimental_rerun()

    # ===========================
    # AUTO REFRESH KILA 5s
    # ===========================
    time.sleep(5)
    st.experimental_rerun()
