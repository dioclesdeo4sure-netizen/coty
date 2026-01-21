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
st.set_page_config(page_title="Coty Butchery AI", page_icon="🥩", layout="wide")

# =========================================================
# DATABASE CONNECTION
# =========================================================
def get_db_connection():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        st.error("DATABASE_URL haijawekwa kwenye Environment Variables!")
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
# INIT DB - CREATE TABLE AUTOMATICALLY
# =========================================================
def init_db():
    conn = g
