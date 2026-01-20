import streamlit as st
import os
from google import genai
from google.genai.errors import APIError
from gtts import gTTS
import base64

# --- Usanidi wa Ukurasa ---
st.set_page_config(page_title="Coty Butchery AI", page_icon="🥩")

# --- Usanidi wa API Key kutoka Render ---
RENDER_ENV_VAR_NAME = "GEMINI_API_KEY_RENDER"
API_KEY = os.environ.get(RENDER_ENV_VAR_NAME)

if not API_KEY:
    st.error(f"❌ Kosa: Weka API Key kwenye Render kwa jina: {RENDER_ENV_VAR_NAME}")
    st.stop()

# Initialize Gemini Client
client = genai.Client(api_key=API_KEY)
GEMINI_MODEL = "gemini-2.5-flash"

# --- LOGIC YAKO YA COTY BUTCHERY (SYSTEM PROMPT) ---
SYSTEM_PROMPT = """
Wewe ni Coty, mhudumu wa wateja wa kidigitali mwenye uwezo wa AI, uliyebuniwa na Aqua Softwares. 
Kazi yako ni Huduma kwa Wateja ya Kitaalamu ya Coty Butchery inayouza nyama na nafaka.

SIFA ZAKO:
1. Adabu na Uelewa: Kuwa na adabu ya hali ya juu sana.
2. Lugha: Kiswahili Sanifu fasaha. Ukihitajika kutumia Kiingereza, badilika haraka.
3. Utambulisho: Jibu la kwanza anza na Salamu, jijitambulishe kama mhudumu wa Coty Butchery. 
4. Jina la Mteja: Muulize mteja jina lake na ulitumie. Kama ni mwanamke tumia: mrembo, kipenzi, Dear au boss lady. Kama ni mwanamume tumia: HANDSOME au Brother.
5. Ushawishi: Kuwa romantic, rafiki, na mcheshi. Tumia emoji nyingi 🌹🥩.
6. Bidhaa na Bei (ZINGATIA HIZI TU):
   - SANGARA WAKAVU 15,000 | DAGAA SACOVA NDOGO 7,000 | DAGAA SACOVA KUBWA 10,000
   - DAGAA KIGOMA NUSU 33,000 | HAPPY RUSSIAN 12,000 | HAPPY BEEF VIENA 9,000
   - SAUSAGE ALFA RUSSIAN 12,000 | FARMERS CHOICE 10,000 | SAUSAGE VIENNA KENYA 10,000
   - KUKU KISASA (1.5KG) 14,000 | KUKU KIENYEJI 25,000 | SANGARA FILLET 32,000
   - [Bidhaa nyingine zote ulizoorodhesha...]

MAAGIZO YA ZIADA:
- Usitaje bidhaa zote kwa pamoja. Muulize mteja anataka nini kwanza.
- Ukigundua mteja amehuzunika, kuwa mkarimu na romantic zaidi.
- Location: Mpe link ya https://maps.app.goo.gl/Wp18PHX99Zvjk3f6
- Kampeni: "RUKA FOLENI NA COTY APP". Ahadi ya delivery haraka mlangoni.
- Mwishoni mwa chat, omba feedback kuhusu huduma yako.
"""

# --- Kazi ya Sauti (gTTS) ---
def play_voice(text):
    try:
        # Safisha maandishi (ondoa emoji kwa ajili ya sauti bora)
        clean_text = text.replace('*', '').replace('#', '')
        tts = gTTS(text=clean_text, lang='eng')
        tts.save("response.mp3")
        
        with open("response.mp3", "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
            md = f"""
                <audio autoplay="true">
                <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
                </audio>
                """
            st.markdown(md, unsafe_allow_html=True)
    except Exception as e:
        pass # Usisumbue mteja kama sauti ikifeli

# --- UI YA STREAMLIT ---
st.title("🥩 Karibu Coty Butchery")
st.caption("Mhudumu wako wa kidigitali anayekujali!")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Onyesha chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat Input
if prompt := st.chat_input("Andika ujumbe hapa..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Convert history to Gemini format
    gemini_contents = []
    for m in st.session_state.messages:
        role = "user" if m["role"] == "user" else "model"
        gemini_contents.append({"role": role, "parts": [{"text": m["content"]}]})

    try:
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                chat_completion = client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=gemini_contents,
                    config={
                        "system_instruction": SYSTEM_PROMPT,
                        "temperature": 0.8,
                    }
                )
                
                response_text = chat_completion.text
                st.markdown(response_text)
                
                # AI inasoma jibu lake
                play_voice(response_text)
                
                st.session_state.messages.append({"role": "assistant", "content": response_text})

    except Exception as e:
        st.error(f"Samahani, jaribu tena kidogo. (Error: {e})")
