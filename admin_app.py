import streamlit as st
import psycopg2
import os
from urllib.parse import urlparse

st.set_page_config(page_title="Coty Admin", layout="wide")

def get_db_connection():
    result = urlparse(os.environ["DATABASE_URL"])
    return psycopg2.connect(
        database=result.path[1:],
        user=result.username,
        password=result.password,
        host=result.hostname,
        port=result.port
    )

st.title("🛠️ Coty Butchery - Orders Dashboard")

password = st.text_input("Admin Password", type="password")

if password == os.environ.get("ADMIN_PASSWORD"):

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

    for name, phone, order, time in orders:
        st.markdown(f"""
        ### 🧾 ODA MPYA
        **Jina:** {name}  
        **Simu:** {phone}  
        **Oda:** {order}  
        **Muda:** {time}
        ---
        """)

else:
    st.warning("Weka password sahihi")
