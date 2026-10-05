import streamlit as st
from datetime import datetime, date, time, timedelta
import json
import requests

st.set_page_config(page_title="ArogyaMitra AI + Reminder", page_icon="💊", layout="wide")

# ===== AUTHENTICATION SYSTEM =====
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.session_state.family_name = ""

USERS = {
    "bharath": {"password":"arogya123", "family":"Gowda Family - Devanahalli", "role":"Admin"},
    "ajji": {"password":"1234", "family":"Ajji - Devanahalli", "role":"Elder"},
    "amma": {"password":"amma123", "family":"Amma", "role":"Family"},
    "demo": {"password":"demo", "family":"Demo Family", "role":"Demo"},
}

def login_page():
    st.markdown("## 🔐 ArogyaMitra Login - ಕುಟುಂಬ ಲಾಗಿನ್")
    st.caption("Login to save your family medicines securely")
    col1,col2 = st.columns([2,1])
    with col1:
        with st.container(border=True):
            username = st.text_input("Username", placeholder="bharath / ajji / demo")
            password = st.text_input("Password", type="password", placeholder="arogya123")
            c1,c2 = st.columns(2)
            if c1.button("🔓 Login", type="primary", use_container_width=True):
                if username in USERS and USERS[username]["password"] == password:
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.family_name = USERS[username]["family"]
                    st.success(f"Welcome {USERS[username]['family']}!")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("Wrong username/password - Try demo/demo")
            if c2.button("Demo Login", use_container_width=True):
                st.session_state.authenticated = True
                st.session_state.username = "demo"
                st.session_state.family_name = "Demo Family"
                st.rerun()
    with col2:
        st.info("**Demo Accounts:**\n- bharath / arogya123\n- ajji / 1234\n- demo / demo")
        st.warning("In production, connect Firebase Auth")
    st.stop()

if not st.session_state.authenticated:
    login_page()

# Language
lang = st.sidebar.selectbox("Language / ಭಾಷೆ", ["ಕನ್ನಡ", "English"])
def t(en, kn): return kn if lang=="ಕನ್ನಡ" else en

# ===== API KEY SETUP - SIDEBAR =====
st.sidebar.markdown("---")
st.sidebar.markdown(f"### {t('🔑 AI API Setup','🔑 AI API ಸೆಟಪ್')}")
st.sidebar.caption(t("Paste Gemini API key to search ANY medicine in Kannada","ಯಾವುದೇ ಔಷಧಿಯನ್ನು ಕನ್ನಡದಲ್ಲಿ ಹುಡುಕಲು Gemini API key ಹಾಕಿ"))

# API key input - secure
api_key = st.sidebar.text_input(
    t("Gemini API Key","Gemini API Key"), 
    type="password", 
    placeholder="AIzaSy...",
    help="Get free key from aistudio.google.com/app/apikey"
)
# Also support secrets.toml for Streamlit Cloud
if not api_key:
    try:
        api_key = st.secrets.get("GEMINI_API_KEY", "")
        if api_key:
            st.sidebar.success(t("API key loaded from secrets","API key secrets ನಿಂದ ಲೋಡ್ ಆಗಿದೆ"))
    except:
        pass

if api_key:
    st.sidebar.success("✅ API Ready - AI can explain any medicine!")
else:
    st.sidebar.warning(t("No API key - Using local 10 medicines only. Add key for unlimited AI.","API key ಇಲ್ಲ - 10 ಔಷಧಿ ಮಾತ್ರ. ಅನಿಯಮಿತ AI ಗೆ key ಸೇರಿಸಿ."))
    st.sidebar.markdown("[Get Free Gemini API Key](https://aistudio.google.com/app/apikey)")

def call_gemini_ai(medicine_name, api_key, lang):
    """Call Gemini to explain medicine in Kannada + English"""
    if not api_key:
        return None
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        prompt = f"""
You are a helpful medical assistant for Karnataka rural elders.
Explain medicine: {medicine_name}
Give answer in BOTH Kannada and English, simple language for elders (18px big text style).

Format strictly as JSON (no extra text):
{{
  "use": "Fever / ಜ್ವರ (short)",
  "kn": "Simple Kannada explanation in 2 lines, dosage when to take, e.g., ಜ್ವರಕ್ಕೆ, ಬೆಳಿಗ್ಗೆ 1 ಮಾತ್ರೆ...",
  "en": "Simple English explanation in 2 lines",
  "tip": "How to take: After food / ಊಟದ ನಂತರ",
  "side": "Side effect in Kannada + English short"
}}

Keep Kannada simple, no medical jargon.
"""
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        headers = {"Content-Type": "application/json"}
        resp = requests.post(url, json=payload, headers=headers, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            text = data['candidates'][0]['content']['parts'][0]['text']
            # Clean JSON
            text = text.replace("```json","").replace("```","").strip()
            return json.loads(text)
        else:
            st.error(f"API Error {resp.status_code}: {resp.text[:200]}")
            return None
    except Exception as e:
        st.error(f"AI Error: {e}")
        return None

# AI KB - 10 medicines (fallback)
MED_KB = {
    "paracetamol": {"use":"Fever / ಜ್ವರ", "kn":"ಜ್ವರ ಮತ್ತು ನೋವಿಗೆ. 6 ಗಂಟೆ ಅಂತರದಲ್ಲಿ 1 ಮಾತ್ರೆ, ದಿನಕ್ಕೆ 4 ಕ್ಕಿಂತ ಹೆಚ್ಚು ಬೇಡ. ಊಟದ ನಂತರ ತೆಗೆದುಕೊಳ್ಳಿ.", "en":"For fever and pain. 1 tab every 6 hours, max 4 per day, after food.", "tip":"After food / ಊಟದ ನಂತರ", "side":"No side if correct dose"},
    "dolo": {"use":"Fever / ಜ್ವರ", "kn":"Dolo 650 - ಜ್ವರ ಮತ್ತು ಮೈಕೈ ನೋವಿಗೆ. ಬೆಳಿಗ್ಗೆ 1, ರಾತ್ರಿ 1, 3 ದಿನ.", "en":"Dolo 650 for fever, body pain. Morning 1, Night 1.", "tip":"After food", "side":"No sleepiness"},
    "cetirizine": {"use":"Cold Allergy / ಶೀತ ಅಲರ್ಜಿ", "kn":"ಶೀತ, ಸೀನುವಿಕೆ, ಅಲರ್ಜಿಗೆ. ನಿದ್ದೆ ಬರಬಹುದು, ರಾತ್ರಿ ಮಾತ್ರ.", "en":"For cold, sneezing. May cause sleepiness, night only.", "tip":"Night only", "side":"Sleepiness / ನಿದ್ದೆ"},
    "azithromycin": {"use":"Infection / ಸೋಂಕು", "kn":"ಗಂಟಲು ಸೋಂಕಿಗೆ ಪ್ರತಿಜೀವಕ. ಪೂರ್ತಿ ಕೋರ್ಸ್ 3-5 ದಿನ ಮುಗಿಸಿ.", "en":"Antibiotic for throat infection. Complete course.", "tip":"Before food 1hr", "side":"Stomach upset"},
    "amoxicillin": {"use":"Infection / ಸೋಂಕು", "kn":"ಪ್ರತಿಜೀವಕ, ಹಲ್ಲು ನೋವು, ಗಂಟಲು ಸೋಂಕಿಗೆ. ಊಟದ ನಂತರ.", "en":"Antibiotic for tooth, throat.", "tip":"After food", "side":"Allergy check"},
    "omeprazole": {"use":"Acidity / ಆಸಿಡಿಟಿ", "kn":"ಗ್ಯಾಸ್, ಆಸಿಡಿಟಿ, ಹೊಟ್ಟೆ ಉರಿಗೆ. ಬೆಳಿಗ್ಗೆ ಖಾಲಿ ಹೊಟ್ಟೆಯಲ್ಲಿ.", "en":"For gas, acidity. Before breakfast.", "tip":"Before breakfast", "side":"Long use consult doctor"},
    "metformin": {"use":"Diabetes / ಸಕ್ಕರೆ", "kn":"ಮಧುಮೇಹಕ್ಕೆ, ಸಕ್ಕರೆ ನಿಯಂತ್ರಣ. ಊಟದ ನಂತರ ತಪ್ಪದೆ.", "en":"For diabetes sugar control. After food daily.", "tip":"After food daily", "side":"Take regularly"},
    "atorvastatin": {"use":"Cholesterol / ಕೊಬ್ಬು", "kn":"ಕೊಲೆಸ್ಟ್ರಾಲ್, ಹೃದಯ ರಕ್ಷಣೆಗೆ. ರಾತ್ರಿ.", "en":"For cholesterol, heart protection. Night.", "tip":"Night", "side":"Muscle pain"},
    "amlodipine": {"use":"BP / ರಕ್ತದೊತ್ತಡ", "kn":"ರಕ್ತದೊತ್ತಡಕ್ಕೆ. ಬೆಳಿಗ್ಗೆ ಒಂದೇ ಸಮಯಕ್ಕೆ.", "en":"For BP. Same time morning.", "tip":"Morning same time", "side":"Ankle swelling"},
    "pantoprazole": {"use":"Acidity / ಆಸಿಡಿಟಿ", "kn":"ಆಸಿಡಿಟಿ, ಹೊಟ್ಟೆ ಹುಣ್ಣಿಗೆ. ಬೆಳಿಗ್ಗೆ ಖಾಲಿ ಹೊಟ್ಟೆ.", "en":"Acidity, ulcer. Empty stomach morning.", "tip":"Empty stomach", "side":"Consult if long use"},
}

st.title(t("💊 ArogyaMitra Pro - AI + Reminder", "💊 ಆರೋಗ್ಯಮಿತ್ರ ಪ್ರೊ - AI + ರಿಮೈಂಡರ್"))
st.caption(t("Paste API key in sidebar → Search ANY medicine in Kannada", "ಸೈಡ್‌ಬಾರ್‌ನಲ್ಲಿ API key ಹಾಕಿ → ಯಾವುದೇ ಔಷಧಿ ಕನ್ನಡದಲ್ಲಿ ಹುಡುಕಿ"))

# Session states
if "meds" not in st.session_state:
    st.session_state.meds = [
        {"name":"Dolo 650","m":1,"n":0,"ni":1,"days":3,"mt":time(8,0),"nt":time(21,0)},
        {"name":"Cetirizine","m":0,"n":0,"ni":1,"days":2,"mt":time(8,0),"nt":time(21,30)},
    ]
if "taken" not in st.session_state:
    st.session_state.taken = {}
if "reminder_times" not in st.session_state:
    st.session_state.reminder_times = {"morning":time(8,0),"noon":time(13,0),"night":time(21,0)}

# Show logged in user + logout
st.sidebar.success(f"👤 {{st.session_state.family_name}} ({{st.session_state.username}})")
if st.sidebar.button("🚪 Logout"):
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.rerun()

# Sidebar - Reminder Setup
st.sidebar.markdown(f"### {t('⚙️ Reminder Setup','⚙️ ರಿಮೈಂಡರ್ ಸೆಟಪ್')}")
st.session_state.reminder_times["morning"] = st.sidebar.time_input(t("Morning","ಬೆಳಿಗ್ಗೆ"), st.session_state.reminder_times["morning"])
st.session_state.reminder_times["noon"] = st.sidebar.time_input(t("Noon","ಮಧ್ಯಾಹ್ನ"), st.session_state.reminder_times["noon"])
st.session_state.reminder_times["night"] = st.sidebar.time_input(t("Night","ರಾತ್ರಿ"), st.session_state.reminder_times["night"])

tab1, tab2, tab3 = st.tabs([t("📋 My Medicines","📋 ನನ್ನ ಔಷಧಿಗಳು"), t("🤖 AI Search (with API key)","🤖 AI ಹುಡುಕಾಟ"), t("⏰ Reminders","⏰ ರಿಮೈಂಡರ್")])

with tab1:
    st.subheader(t("Add Medicine with Reminder","ರಿಮೈಂಡರ್ ಜೊತೆ ಔಷಧಿ ಸೇರಿಸಿ"))
    with st.form("add_med"):
        c1,c2 = st.columns(2)
        name = c1.text_input(t("Medicine Name","ಔಷಧಿ ಹೆಸರು"), placeholder="Dolo 650")
        days = c2.number_input(t("Days","ದಿನಗಳು"),1,90,3)
        c1,c2,c3 = st.columns(3)
        m = c1.number_input("🌅 "+t("Morning","ಬೆಳಿಗ್ಗೆ"),0,4,1)
        n = c2.number_input("☀️ "+t("Noon","ಮಧ್ಯಾಹ್ನ"),0,4,0)
        ni = c3.number_input("🌙 "+t("Night","ರಾತ್ರಿ"),0,4,1)
        c1,c2 = st.columns(2)
        mt = c1.time_input(t("Morning reminder","ಬೆಳಿಗ್ಗೆ ರಿಮೈಂಡರ್"), time(8,0))
        nt = c2.time_input(t("Night reminder","ರಾತ್ರಿ ರಿಮೈಂಡರ್"), time(21,0))
        if st.form_submit_button(t("➕ Add","➕ ಸೇರಿಸಿ")) and name:
            st.session_state.meds.insert(0, {"name":name,"m":m,"n":n,"ni":ni,"days":days,"mt":mt,"nt":nt})
            st.success(f"{name} added!"); st.balloons()
    st.divider()
    for i, med in enumerate(st.session_state.meds):
        with st.container(border=True):
            st.markdown(f"### {med['name']} | {med['days']} days")
            st.write(f"🌅 {med['m']} at {med['mt']} | 🌙 {med['ni']} at {med['nt']}")
            voice = f"{med['name']}. ಬೆಳಿಗ್ಗೆ {med['m']} ಮಾತ್ರೆ {med['mt'].strftime('%I:%M %p')} ಗೆ"
            st.code(voice)
            if st.button("🗑️ Remove", key=f"del{i}"):
                st.session_state.meds.pop(i); st.rerun()

with tab2:
    st.subheader(t("🤖 AI Search - Any Medicine in Kannada","🤖 AI ಹುಡುಕಾಟ - ಯಾವುದೇ ಔಷಧಿ ಕನ್ನಡದಲ್ಲಿ"))
    if not api_key:
        st.info(t("👈 Paste Gemini API key in sidebar to enable AI for ANY medicine. Without key, only 10 local medicines work.","👈 ಸೈಡ್‌ಬಾರ್‌ನಲ್ಲಿ Gemini API key ಹಾಕಿದರೆ ಯಾವುದೇ ಔಷಧಿ AI ವಿವರಿಸುತ್ತದೆ. Key ಇಲ್ಲದಿದ್ದರೆ 10 ಮಾತ್ರ."))
    
    q = st.text_input(t("Medicine name","ಔಷಧಿ ಹೆಸರು"), placeholder="E.g., Telma 40, Ecosprin, Vitamin D...")
    col1, col2 = st.columns([1,2])
    search_clicked = col1.button(t("🔍 AI Explain (Kannada)","🔍 AI ವಿವರಿಸು"), type="primary")
    
    if search_clicked and q:
        ql = q.lower().strip()
        # First check local KB
        found_local = None
        for k in MED_KB:
            if k in ql or ql in k:
                found_local = k; break
        
        if api_key:
            with st.spinner(t(f"AI searching {q} in Kannada...","AI {0} ಅನ್ನು ಕನ್ನಡದಲ್ಲಿ ಹುಡುಕುತ್ತಿದೆ...").format(q)):
                ai_result = call_gemini_ai(q, api_key, lang)
            if ai_result:
                st.success(f"**{q.upper()}** - {ai_result['use']} (AI)")
                st.markdown(f"### {t('Kannada:','ಕನ್ನಡದಲ್ಲಿ:')} {ai_result['kn']}")
                st.markdown(f"**English:** {ai_result['en']}")
                st.info(f"💊 {ai_result['tip']} | ⚠️ {ai_result['side']}")
                st.code(f"{q} - {ai_result['kn']}")
                if st.button(f"➕ Add {q} to Reminders"):
                    st.session_state.meds.insert(0, {"name":q.title(),"m":1,"n":0,"ni":1,"days":3,"mt":time(8,0),"nt":time(21,0)})
                    st.success("Added!")
            elif found_local:
                d = MED_KB[found_local]
                st.success(f"**{q.upper()}** - {d['use']} (Local KB)")
                st.markdown(f"### {d['kn']}")
                st.markdown(f"**{d['en']}**")
                st.info(f"💊 {d['tip']} | ⚠️ {d['side']}")
        else:
            if found_local:
                d = MED_KB[found_local]
                st.success(f"**{q.upper()}** - {d['use']}")
                st.markdown(f"### {d['kn']}")
                st.markdown(f"**{d['en']}**")
            else:
                st.warning(t(f"'{q}' not in local DB. Add Gemini API key in sidebar to search ANY medicine.","ಸ್ಥಳೀಯ DB ನಲ್ಲಿ ಇಲ್ಲ. ಸೈಡ್‌ಬಾರ್‌ನಲ್ಲಿ API key ಹಾಕಿ ಯಾವುದೇ ಔಷಧಿ ಹುಡುಕಿ."))
    
    st.markdown("---")
    st.write(t("Try popular:","ಪ್ರಯತ್ನಿಸಿ:"))
    cols = st.columns(5)
    for i, k in enumerate(list(MED_KB.keys())[:5]):
        with cols[i]:
            if st.button(k.title(), key=f"pop_{k}"):
                st.session_state['q'] = k
                st.info(MED_KB[k]['kn'])

with tab3:
    st.subheader(t("⏰ Today's Schedule","⏰ ಇಂದಿನ ವೇಳಾಪಟ್ಟಿ"))
    now = datetime.now().time()
    today_str = date.today().isoformat()
    todays = []
    for med in st.session_state.meds:
        if med['m']>0: todays.append({"time":med['mt'],"name":med['name'],"dose":med['m'],"period":"Morning","icon":"🌅"})
        if med['n']>0: todays.append({"time":st.session_state.reminder_times['noon'],"name":med['name'],"dose":med['n'],"period":"Noon","icon":"☀️"})
        if med['ni']>0: todays.append({"time":med['nt'],"name":med['name'],"dose":med['ni'],"period":"Night","icon":"🌙"})
    todays = sorted(todays, key=lambda x: x['time'])
    
    next_dose = next((d for d in todays if d['time'] > now), None)
    if next_dose:
        delta = datetime.combine(date.today(), next_dose['time']) - datetime.combine(date.today(), now)
        mins = int(delta.total_seconds()//60)
        st.success(f"Next: {next_dose['name']} at {next_dose['time'].strftime('%I:%M %p')} in {mins} min")
        if 0 <= mins <= 15:
            st.toast(f"⏰ Take {next_dose['name']} now!", icon="💊")
    
    taken_count=0
    for idx, d in enumerate(todays):
        key = f"{today_str}_{d['name']}_{d['time']}"
        is_taken = st.session_state.taken.get(key, False)
        c1,c2,c3 = st.columns([1,3,1])
        c1.write(f"**{d['time'].strftime('%I:%M %p')}**")
        c2.write(f"{d['icon']} {d['name']} - {d['dose']}")
        checked = c3.checkbox("Taken", value=is_taken, key=f"chk_{idx}")
        if checked != is_taken:
            st.session_state.taken[key]=checked
            if checked: st.balloons()
        if checked: taken_count+=1
    if todays:
        st.progress(taken_count/len(todays), text=f"{taken_count}/{len(todays)} taken")

st.sidebar.markdown("---")
st.sidebar.caption("Built by Bharath Gowda | v4.0 API Key Enabled")
