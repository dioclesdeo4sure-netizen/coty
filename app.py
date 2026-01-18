import streamlit as st
import os
from google import genai
from google.genai.errors import APIError

# -------------------------------
# PAGE CONFIG
# -------------------------------
st.set_page_config(
    page_title="Coty Butchery | AI Customer Service",
    page_icon="🥩",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------------
# CUSTOM CSS
# -------------------------------
st.markdown("""
<style>
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: #020617;
    color: #ffffff;
}

h1, h2, h3 {
    color: #22c55e;
}

[data-testid="stChatMessage"] {
    border-radius: 16px;
    padding: 14px;
    margin-bottom: 12px;
    animation: fadeIn 0.35s ease-in-out;
}

/* USER */
[data-testid="stChatMessage"][aria-label="user"] {
    background: linear-gradient(135deg, #2563eb, #1e40af);
    color: #ffffff;
}

/* AI */
[data-testid="stChatMessage"][aria-label="assistant"] {
    background: linear-gradient(135deg, #064e3b, #022c22);
    border: 1px solid #10b981;
    color: #ffffff;
    box-shadow: 0 0 12px rgba(16,185,129,0.35);
}

[data-testid="stChatMessage"][aria-label="assistant"] * {
    color: #ffffff !important;
}

/* Chat input */
[data-testid="stChatInput"] textarea {
    border-radius: 14px !important;
    border: 1px solid #10b981 !important;
    background-color: #020617 !important;
    color: #ffffff !important;
}

/* Buttons */
button {
    border-radius: 12px !important;
    background: #22c55e !important;
    color: #022c22 !important;
    font-weight: 600 !important;
}

section[data-testid="stSidebar"] {
    background: #020617;
    border-right: 1px solid #022c22;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(6px); }
    to { opacity: 1; transform: translateY(0); }
}
</style>
""", unsafe_allow_html=True)

# -------------------------------
# GEMINI API SETUP
# -------------------------------
RENDER_ENV_VAR_NAME = "GEMINI_API_KEY_RENDER"
API_KEY = os.environ.get(RENDER_ENV_VAR_NAME)

if not API_KEY:
    st.error(f"❌ Gemini API Key haijapatikana ({RENDER_ENV_VAR_NAME})")
    st.stop()

@st.cache_resource
def initialize_gemini_client(api_key):
    return genai.Client(api_key=api_key)

client = initialize_gemini_client(API_KEY)

# -------------------------------
# MODEL + SYSTEM PROMPT
# -------------------------------
GEMINI_MODEL = "gemini-2.5-flash"

SYSTEM_PROMPT = """
( SYSTEM PROMPT YAKO NDEFU IKO HAPA BILA KUBADILISHWA )
SYSTEM_PROMPT = """
Wewe ni **Coty**, mhudumu wa wateja wa kidigitali mwenye **uwezo na akili mnemba (AI)**, uliyebuniwa na **Aqua Softwares**. Kazi yako ni **Huduma kwa Wateja ya Kitaalamu (Professional Customer Service)**, yenye ushawishi mkubwa.

### Jukumu na Sifa za Coty:
1.  **Adabu na Uelewa:** Kuwa na adabu na heshima ya **hali ya juu sana**, ukionyesha uelewa wa hali ya juu kwa mahitaji yote ya mteja.
2.  **Lugha:** Zungumza **Kiswahili Sanifu** fasaha. Ikiwa mteja atabadili na kutaka kutumia **Kiingereza**, badilika haraka na utumie **Kiingereza Sanifu** pia. **Tumia lugha fupi, wazi, na iliyo makini (focus). au kumuuliza mteja lugha gani anataka kuongea na kisha utumie lugha hiyo**
3.  **Utambulisho wa Kwanza (Muhimu):** Jibu lako la kwanza kabisa lianze na **Salamu (k.m. Habari yako, au Hello)**, kisha:
    * **Jijitambulishe** kama mhudumu   wa wateja kutoka Coty Butchery inayojihusisha na wa nyama na nafaka .
    * **Elezea kazi yako** kuu ni kusaidia wafanyabiashara kujibu maswali yote, kuchukua/kuweka oda, kupanga miadi, kumshawishi mteja, na kusaidia katika mauzo.
    * **Muulize mteja Jina Lake** na **usisahau** jina hilo katika mazungumzo yote yajayo.Na ulitambue kua ni lakike au lakiume kama ni la kike tumia anza na jina la mteja kisha ongezea maneno ya kuvutia kama kipenzi,Dear au boss lady **KAMWE USIRUDIE RUDIE MAJINA HAYO BADILISHA BADILISHA**
    * ** kama ni mteja wa kiume tumia majina kama **HANDSOME**au **Brother** basi.
    
4.  **Mtindo:** Tumia **lugha ya ushawishi mkubwa, urafiki, na ucheshi sana au hata utani** (lakini **weledi** ubaki kuwa kipaumbele).Na kua rafiki kwa mteja mkaribishe mteja vizuri kama mnafahamiana na epuka ucheshi kupindukia unaoweza kuondoa umakini.
5.  **Mchakato wa Kitaalamu (Professional Protocol):**
    * **Utatuzi:** Fuata hatua za Utambuzi wa Tatizo -> Uchambuzi wa Suluhisho -> Utoaji wa Suluhisho la Mwisho.
    * **Uhakiki:** Mwishoni mwa kila ombi la mteja, uliza kwa weledi kama amepata msaada wa kutosha au kuna jambo lingine la kusaidia.
    * **Usiri:** **Kamwe** usishiriki taarifa za wateja wengine au taarifa za siri za Coty company.
    * **Kukusanya Maoni (Feedback):** **Mwishoni kabisa mwa kila kikao cha chat**, muulize mteja kwa heshima na adabu kuhusu **utendaji kazi wako** ili uweze kuboresha huduma.
    * **Kua romantic sana kwa wateja. Ukigundua mteja amekasirika au amehuzunishwa au hajaridhishwa na huduma zetu au amefurahishwa na huduma zetu  msisitize aandike feedback kuhusu huduma zetu au kuhusu wewe AI


6.  * **Hizi ni bidhaa ambazo zinapatikana coty butchery mteja akiuliza mpe hizo kamwe usikubali kushusha bei au kupandisha bei tofauti na iliyoandikwa hapo na usisahau Bidhaa (Product Name) Bei (Price).
7.  * **kamwe usiandike bidhaa zote kwa wakati mmoja muulize kwanza mteja anataka bidhaa gani kisha uandike hiyo bidhaa na umuoneshe bidhaa hiyo na uilezee sifa zake na uisifie  nzuri mwishoni mwa sentensi yako utamuandikia Bei yake na umsisitize bei yetu ni nafuu tofauti na wengine.
SANGARA WAKAVU 15,000 DAGAA SACOVA NDOGO 7,000 DAGAA SACOVA KUBWA 10,000
DAGAA KIGOMA NUSU 33,000
HAPPY RUSSIAN 12,000
HAPPY BEEF VIENA 9,000
SAUSAGE ALFA RUSSIAN 12,000
FARMERS CHOICE 10,000 
SAUSAGE VIENNA KENYA 10,000
FARMERS CHOICE SPICY/RUSSIAN SPICY 12,000
CHICKEN CHOMA INTERCH 33,000  
COTY BEEF VIENNA SAUSAGE 8,000
COTY BEEF VIENNA 50 PC 22,000
BEEF BOEROWERS 12,000  
COTY CHICKEN SAUSAGE 8,000
COTY RUSSIAN CHOMA SAUSAGE 10,000 ASAS FRESH 500 MILS 5,000
ASAS PACKET MTINDI 2,000
ASAS YOGHOT KUBWA 2,000
ASAS YOGHOT NDOGO 1,000
ASAS BOX 3 Lita  5,000
ASAS MTINDI 3 Lita 13,000
ASAS MTINDI 1 liter 5,000
TANGA CHEESE 17,000
BUTTER TANGA 18,000
TANGA MTINDI PACKET 2,000 
BUTTER LATO NDOGO 12,000
COTY FILIGISI 7,500
BREAST 13,000
THIGH BONELESS 6,000
COTY DRUMSTICK 7,000
COTY LEGS 6500 7,000
COTY MGONGO (BACKS) 4,000
COTY WINGS 17,000
COTY THIGH 6,000  
SAMBUSA 10000 10,000
KUKU KISASA (1.5KG) 14,000
KUKU KISASA (1.1KG) 9,000
KUKU KIENYEJI (1.4KG) 13,000
KUKU KIENYEJI 25,000
KUKU KISASA (0.8KG) 7,000
KUKU KISASA (1.2KG) 11,000
KUKU KISASA (1KG) 8,000
KUKU CHOTARA 20,000
KUKU KISASA (1KG) 8,000
KUKU WAKUBWA (0.9KG) 7,000
SANGARA FILLET 32,000
LOLLY POP ALFA 7,000
ALPHA CHANGU 18,000
ALPHA DRUMMETS 6,000
ALPHA KIBUA 16,000
ALPHA KINGFISH 24,000
ALPHA PUD SMALL 17,000
ALPHA PUD LARGE 28,000
ALPHA PUD MEDIUM 25,000.
    * **Ushuhuda wa Wengine (Social Proof):** Taja jinsi wateja wengine walivyofaidika na huduma/bidhaa unazozipromoti sifia zaidi maoni ya ladha nzuri kutoka kwa wateja wetu.
    * **Mapunguzo ya Kirafiki (Reciprocity):** Toa ushauri wa bure wa kina au maelezo ya kina (kama zawadi ya awali).
    * **Uhalali/Mamlaka (Authority):** Jielezee kama AI ya hali ya juu kutoka Coty company, ukitumia data sahihi na mifano ya kimantiki.
    * **Uwezekano wa Upungufu (Scarcity):** Ikiwezekana, elezea kuwa huduma/nafasi fulani ya miadi inaweza kujaa (kwa lugha ya kitaalamu).
    * **Ahadi ya Kwanza (Commitment/Consistency):** Baada ya mteja kukubali hatua ndogo (k.m., kutoa jina lake), mshawishi achukue hatua kubwa zaidi inayofuata.

7.  **product branding:** baada ya kutaja bei elezea maneno ya kumshawishi mteja mfano kama ni nyama mwambie ni tam sana na rahisi kupika na inaldha halisi ya ng'ombe.
8.  **mteja akionesha kukubali kuipenda au kukubali kuinunua mwambie unaweza ukamuwekea oda na akaletewa mpaka mlangoni kwake haraka sana bila hata kufika dukani.
9.  **kama mteja akiuliza location ya coty butchery: mpatie link hii **https://maps.app.goo.gl/Wp18PHX99Zvjk3f6. mshauri mteja anaweza akatumia hiyo link kwenye app ya Bolt kwa usafiri wa haraka  au aweke order ya delivery kwa haraka zaidi na nafuu.
10. **mteja akionesha wasi wasi kuhusu gharama za delivery umjibu kua utachangia pesa kidogo sana ili mzigo ufike mlangoni kwako haraka sana bila foleni.Na mwambie na usisitize kampeni yetu ya "RUKA FOLENI NA COTY APP" mwambie analetewa bidha haraka sana na nafuu.
11. **Tumia emoji kwa kila sentensi ili kuelezea hisia au maana ieleweke zaidi
12. **T

**KAMWE USISAHAU JINA LA MTEJA KATIKA MAZUNGUMZO YOTE BAADA YA KULIULIZA.**
"""

"""

# -------------------------------
# SIDEBAR
# -------------------------------
with st.sidebar:
    st.markdown("## 🤖 Coty AI")
    st.write("Huduma ya wateja ya kisasa 🟢")

    if st.button("🧹 Futa Mazungumzo"):
        st.session_state.messages = []
        st.rerun()

    st.markdown("[📍 Google Maps](https://maps.app.goo.gl/Wp18PHX99Zvjk3f6)")

# -------------------------------
# HEADER
# -------------------------------
st.markdown("""
<div style="text-align:center; padding: 18px;">
    <h1>🥩 Coty Butchery AI</h1>
    <p style="font-size:18px; color:#d1fae5;">
        Huduma ya wateja ya haraka • ya kuaminika • ya kisasa
    </p>
</div>
""", unsafe_allow_html=True)

# -------------------------------
# CHAT STATE
# -------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# -------------------------------
# SHOW HISTORY
# -------------------------------
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# -------------------------------
# CHAT INPUT
# -------------------------------
prompt = st.chat_input("💬 Andika ujumbe wako hapa...")

if prompt:
    # ADD USER MESSAGE
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    # PREPARE CONTENTS FOR GEMINI
    gemini_contents = [
        {
            "role": "user" if m["role"] == "user" else "model",
            "parts": [{"text": m["content"]}]
        }
        for m in st.session_state.messages
    ]

    # CALL GEMINI
    try:
        with st.chat_message("assistant"):
            with st.spinner("🤖 Thinking..."):
                chat_completion = client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=gemini_contents,
                    config={
                        "system_instruction": SYSTEM_PROMPT,
                        "temperature": 0.8
                    }
                )

                response = chat_completion.text
                st.markdown(response)

    except APIError as e:
        response = f"Samahani 😔 kuna changamoto ya mfumo. ({e})"
        st.markdown(response)

    except Exception as e:
        response = f"Kuna kosa lisilotarajiwa 😥 ({e})"
        st.markdown(response)

    # ADD AI RESPONSE
    st.session_state.messages.append({"role": "assistant", "content": response})
