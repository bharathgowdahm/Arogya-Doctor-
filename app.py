import streamlit as st
from datetime import datetime, date, time, timedelta
import json

st.set_page_config(page_title="ArogyaMitra AI + Reminder", page_icon="💊", layout="wide")

# Language
lang = st.sidebar.selectbox("Language / ಭಾಷೆ", ["ಕನ್ನಡ", "English"])
def t(en, kn): return kn if lang=="ಕನ್ನಡ" else en

# AI KB - 10 medicines
MED_KB = {
    "paracetamol": {"use":"Fever / ಜ್ವರ", "kn":"ಜ್ವರ ಮತ್ತು ನೋವಿಗೆ. 6 ಗಂಟೆ ಅಂತರದಲ್ಲಿ 1 ಮಾತ್ರೆ, ದಿನಕ್ಕೆ 4 ಕ್ಕಿಂತ ಹೆಚ್ಚು ಬೇಡ. ಊಟದ ನಂತರ ತೆಗೆದುಕೊಳ್ಳಿ.", "en":"For fever and pain. 1 tab every 6 hours, max 4 per day, after food.", "tip":"After food / ಊಟದ ನಂತರ", "side":"No side if correct dose / ಸರಿಯಾದ ಪ್ರಮಾಣದಲ್ಲಿ ಅಡ್ಡಪರಿಣಾಮ ಇಲ್ಲ"},
    "dolo": {"use":"Fever / ಜ್ವರ", "kn":"Dolo 650 - ಜ್ವರ ಮತ್ತು ಮೈಕೈ ನೋವಿಗೆ. ಬೆಳಿಗ್ಗೆ 1, ರಾತ್ರಿ 1, 3 ದಿನ.", "en":"Dolo 650 for fever, body pain. Morning 1, Night 1.", "tip":"After food", "side":"Sleepy? No / ನಿದ್ದೆ ಬರುವುದಿಲ್ಲ"},
    "cetirizine": {"use":"Cold Allergy / ಶೀತ ಅಲರ್ಜಿ", "kn":"ಶೀತ, ಸೀನುವಿಕೆ, ಅಲರ್ಜಿಗೆ. ನಿದ್ದೆ ಬರಬಹುದು, ರಾತ್ರಿ ಮಾತ್ರ ತೆಗೆದುಕೊಳ್ಳಿ.", "en":"For cold, sneezing. May cause sleepiness, take at night.", "tip":"Night only", "side":"Sleepiness / ನಿದ್ದೆ"},
    "azithromycin": {"use":"Infection / ಸೋಂಕು", "kn":"ಗಂಟಲು ಸೋಂಕಿಗೆ ಪ್ರತಿಜೀವಕ. ಪೂರ್ತಿ ಕೋರ್ಸ್ 3-5 ದಿನ ಮುಗಿಸಿ.", "en":"Antibiotic for throat infection. Complete 3-5 days course.", "tip":"Before food 1hr", "side":"Stomach upset possible"},
    "amoxicillin": {"use":"Infection / ಸೋಂಕು", "kn":"ಪ್ರತಿಜೀವಕ, ಹಲ್ಲು ನೋವು, ಗಂಟಲು ಸೋಂಕಿಗೆ. ಊಟದ ನಂತರ.", "en":"Antibiotic for tooth, throat.", "tip":"After food", "side":"Allergy check"},
    "omeprazole": {"use":"Acidity / ಆಸಿಡಿಟಿ", "kn":"ಗ್ಯಾಸ್, ಆಸಿಡಿಟಿ, ಹೊಟ್ಟೆ ಉರಿಗೆ. ಬೆಳಿಗ್ಗೆ ಖಾಲಿ ಹೊಟ್ಟೆಯಲ್ಲಿ.", "en":"For gas, acidity. Before breakfast empty stomach.", "tip":"Before breakfast", "side":"Long use consult doctor"},
    "metformin": {"use":"Diabetes / ಸಕ್ಕರೆ", "kn":"ಮಧುಮೇಹಕ್ಕೆ, ಸಕ್ಕರೆ ನಿಯಂತ್ರಣ. ಊಟದ ನಂತರ ತಪ್ಪದೆ ತೆಗೆದುಕೊಳ್ಳಿ.", "en":"For diabetes sugar control. After food daily.", "tip":"After food daily", "side":"Take regularly"},
    "atorvastatin": {"use":"Cholesterol / ಕೊಬ್ಬು", "kn":"ಕೊಲೆಸ್ಟ್ರಾಲ್, ಹೃದಯ ರಕ್ಷಣೆಗೆ. ರಾತ್ರಿ ತೆಗೆದುಕೊಳ್ಳಿ.", "en":"For cholesterol, heart protection. Night time.", "tip":"Night", "side":"Muscle pain inform doctor"},
    "amlodipine": {"use":"BP / ರಕ್ತದೊತ್ತಡ", "kn":"ರಕ್ತದೊತ್ತಡಕ್ಕೆ. ಬೆಳಿಗ್ಗೆ ಒಂದೇ ಸಮಯಕ್ಕೆ.", "en":"For BP. Same time morning.", "tip":"Morning same time", "side":"Ankle swelling possible"},
    "pantoprazole": {"use":"Acidity / ಆಸಿಡಿಟಿ", "kn":"ಆಸಿಡಿಟಿ, ಹೊಟ್ಟೆ ಹುಣ್ಣಿಗೆ. ಬೆಳಿಗ್ಗೆ ಖಾಲಿ ಹೊಟ್ಟೆ.", "en":"Acidity, ulcer. Empty stomach morning.", "tip":"Empty stomach", "side":"Consult if long use"},
}

st.title(t("💊 ArogyaMitra Pro - AI + Reminder", "💊 ಆರೋಗ್ಯಮಿತ್ರ ಪ್ರೊ - AI + ರಿಮೈಂಡರ್"))
st.caption(t("AI Medicine Search + Daily Reminders in Kannada", "AI ಔಷಧಿ ಹುಡುಕಾಟ + ದಿನನಿತ್ಯದ ರಿಮೈಂಡರ್ ಕನ್ನಡದಲ್ಲಿ"))

# Session states
if "meds" not in st.session_state:
    st.session_state.meds = [
        {"name":"Dolo 650","m":1,"n":0,"ni":1,"days":3,"mt":time(8,0),"nt":time(21,0),"village":"Devanahalli"},
        {"name":"Cetirizine","m":0,"n":0,"ni":1,"days":2,"mt":time(8,0),"nt":time(21,30),"village":""},
    ]
if "taken" not in st.session_state:
    st.session_state.taken = {} # key: date_medicine_time
if "reminder_times" not in st.session_state:
    st.session_state.reminder_times = {"morning":time(8,0),"noon":time(13,0),"night":time(21,0)}

# Sidebar - Setup
st.sidebar.markdown(f"### {t('⚙️ Reminder Setup','⚙️ ರಿಮೈಂಡರ್ ಸೆಟಪ್')}")
st.session_state.reminder_times["morning"] = st.sidebar.time_input(t("Morning time","ಬೆಳಿಗ್ಗೆ ಸಮಯ"), st.session_state.reminder_times["morning"])
st.session_state.reminder_times["noon"] = st.sidebar.time_input(t("Noon time","ಮಧ್ಯಾಹ್ನ ಸಮಯ"), st.session_state.reminder_times["noon"])
st.session_state.reminder_times["night"] = st.sidebar.time_input(t("Night time","ರಾತ್ರಿ ಸಮಯ"), st.session_state.reminder_times["night"])
st.sidebar.info(t("App checks every time you open. In pro version, browser notifications + sound.","ಪ್ರತಿ ಬಾರಿ ತೆರೆದಾಗ ಪರಿಶೀಲಿಸುತ್ತದೆ. ಪ್ರೊ ನಲ್ಲಿ ನೋಟಿಫಿಕೇಶನ್ + ಸೌಂಡ್."))

tab1, tab2, tab3 = st.tabs([t("📋 My Medicines","📋 ನನ್ನ ಔಷಧಿಗಳು"), t("🤖 AI Search","🤖 AI ಹುಡುಕಾಟ"), t("⏰ Today's Reminders","⏰ ಇಂದಿನ ರಿಮೈಂಡರ್")])

with tab1:
    st.subheader(t("Add Medicine with Reminder Time","ರಿಮೈಂಡರ್ ಸಮಯದೊಂದಿಗೆ ಔಷಧಿ ಸೇರಿಸಿ"))
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
        if st.form_submit_button(t("➕ Add with Reminder","➕ ರಿಮೈಂಡರ್ ಜೊತೆ ಸೇರಿಸಿ")) and name:
            st.session_state.meds.insert(0, {"name":name,"m":m,"n":n,"ni":ni,"days":days,"mt":mt,"nt":nt,"village":""})
            st.success(t(f"{name} added with reminders!","ಸೇರಿಸಲಾಗಿದೆ!")); st.balloons()

    st.divider()
    st.subheader(t("My Medicines Dashboard","ನನ್ನ ಔಷಧಿ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್"))
    for i, med in enumerate(st.session_state.meds):
        with st.container(border=True):
            col1,col2 = st.columns([3,1])
            col1.markdown(f"## {med['name']} | {med['days']} {t('days','ದಿನ')}")
            col1.write(f"🌅 {med['m']} at {med['mt'].strftime('%I:%M %p')} | 🌙 {med['ni']} at {med['nt'].strftime('%I:%M %p')}")
            # Voice text
            voice = f"{med['name']}. ಬೆಳಿಗ್ಗೆ {med['m']} ಮಾತ್ರೆ {med['mt'].strftime('%I:%M %p')} ಗೆ, ರಾತ್ರಿ {med['ni']} ಮಾತ್ರೆ {med['nt'].strftime('%I:%M %p')} ಗೆ, {med['days']} ದಿನ."
            col1.code(voice)
            if col2.button(t("🗑️ Remove","ತೆಗೆದುಹಾಕಿ"), key=f"del{i}"):
                st.session_state.meds.pop(i); st.rerun()

with tab2:
    st.subheader(t("🤖 AI Medicine Search - Kannada Explanation","🤖 AI ಔಷಧಿ ಹುಡುಕಾಟ - ಕನ್ನಡ ವಿವರಣೆ"))
    q = st.text_input(t("Type medicine name","ಔಷಧಿ ಹೆಸರು ಬರೆಯಿರಿ"), placeholder="Paracetamol, Metformin, Dolo...")
    c1,c2 = st.columns([1,3])
    if c1.button(t("🔍 AI Explain","🔍 AI ವಿವರಿಸು")) and q:
        ql = q.lower().strip()
        found = None
        for k in MED_KB:
            if k in ql or ql in k:
                found = k; break
        if found:
            d = MED_KB[found]
            st.success(f"**{q.upper()}** - {d['use']}")
            st.markdown(f"### {t('Kannada:','ಕನ್ನಡದಲ್ಲಿ:')} {d['kn']}")
            st.markdown(f"**English:** {d['en']}")
            st.info(f"💊 {t('How to take:','ತೆಗೆದುಕೊಳ್ಳುವುದು:')} {d['tip']} | ⚠️ {t('Side:','ಅಡ್ಡಪರಿಣಾಮ:')} {d['side']}")
            st.code(f"{q} - {d['kn']} - {d['tip']}")
            if st.button(t(f"➕ Add {q} to My Medicines","ನನ್ನ ಔಷಧಿಗಳಿಗೆ ಸೇರಿಸಿ")):
                st.session_state.meds.insert(0, {"name":q.title(),"m":1,"n":0,"ni":1,"days":3,"mt":time(8,0),"nt":time(21,0),"village":""})
                st.success(t("Added to reminders!","ರಿಮೈಂಡರ್‌ಗೆ ಸೇರಿಸಲಾಗಿದೆ!"))
        else:
            st.warning(t(f"'{q}' not in local AI DB. Try: Dolo, Metformin, Omeprazole, etc. In pro, connect Gemini API for any medicine.","ಸ್ಥಳೀಯ DB ನಲ್ಲಿ ಇಲ್ಲ. Dolo, Metformin ಪ್ರಯತ್ನಿಸಿ. ಪ್ರೊ ನಲ್ಲಿ Gemini API ಯಾವುದೇ ಔಷಧಿಗೆ ಉತ್ತರಿಸುತ್ತದೆ."))

    st.markdown("---")
    st.write(t("Popular - Click to explain:","ಜನಪ್ರಿಯ - ಕ್ಲಿಕ್ ಮಾಡಿ:"))
    cols = st.columns(4)
    for i, (k,v) in enumerate(MED_KB.items()):
        with cols[i%4]:
            with st.container(border=True):
                st.write(f"**{k.title()}**")
                st.caption(v['use'][:20])
                if st.button(t("Explain","ವಿವರಿಸು"), key=f"pop_{k}"):
                    st.session_state['last_q']=k
                    st.info(f"{k}: {v['kn']}")

with tab3:
    st.subheader(t("⏰ Today's Reminder Schedule","⏰ ಇಂದಿನ ರಿಮೈಂಡರ್ ವೇಳಾಪಟ್ಟಿ"))
    now = datetime.now().time()
    today_str = date.today().isoformat()
    
    # Generate today's doses
    todays = []
    for med in st.session_state.meds:
        if med['m']>0:
            todays.append({"time":med['mt'],"name":med['name'],"dose":med['m'],"period":"Morning","icon":"🌅"})
        if med['n']>0:
            todays.append({"time":st.session_state.reminder_times['noon'],"name":med['name'],"dose":med['n'],"period":"Noon","icon":"☀️"})
        if med['ni']>0:
            todays.append({"time":med['nt'],"name":med['name'],"dose":med['ni'],"period":"Night","icon":"🌙"})
    
    todays = sorted(todays, key=lambda x: x['time'])
    
    # Next dose countdown
    next_dose = None
    for d in todays:
        if d['time'] > now:
            next_dose = d; break
    if next_dose:
        delta = datetime.combine(date.today(), next_dose['time']) - datetime.combine(date.today(), now)
        mins = int(delta.total_seconds()//60)
        st.success(t(f"Next: {next_dose['name']} at {next_dose['time'].strftime('%I:%M %p')} in {mins} min - {next_dose['icon']} {next_dose['period']}","ಮುಂದಿನದು: {0} {1} ಕ್ಕೆ {2} ನಿಮಿಷದಲ್ಲಿ").format(next_dose['name'], next_dose['time'].strftime('%I:%M %p'), mins))
        if mins <= 15 and mins >=0:
            st.toast(t(f"⏰ Time to take {next_dose['name']}!","⏰ {0} ತೆಗೆದುಕೊಳ್ಳುವ ಸಮಯ!").format(next_dose['name']), icon="💊")
            st.warning(t(f"🔔 Reminder: Take {next_dose['name']} now!","🔔 ರಿಮೈಂಡರ್: ಈಗ {0} ತೆಗೆದುಕೊಳ್ಳಿ!").format(next_dose['name']))
    else:
        st.info(t("All doses done for today! Great job!","ಇಂದಿನ ಎಲ್ಲಾ ಔಷಧಿಗಳು ಮುಗಿದವು!"))
    
    # Today's list with checkboxes
    taken_count = 0
    for idx, d in enumerate(todays):
        key = f"{today_str}_{d['name']}_{d['time']}"
        is_taken = st.session_state.taken.get(key, False)
        col1,col2,col3 = st.columns([1,3,1])
        with col1:
            st.write(f"**{d['time'].strftime('%I:%M %p')}**")
        with col2:
            st.write(f"{d['icon']} **{d['name']}** - {d['dose']} {t('tab','ಮಾತ್ರೆ')} ({d['period']})")
        with col3:
            checked = st.checkbox(t("Taken","ತೆಗೆದುಕೊಂಡೆ"), value=is_taken, key=f"chk_{idx}_{key}")
            if checked != is_taken:
                st.session_state.taken[key]=checked
                if checked:
                    st.balloons()
        if is_taken: taken_count+=1
    
    # Progress
    if todays:
        pct = taken_count/len(todays)
        st.progress(pct, text=t(f"{taken_count}/{len(todays)} doses taken today","ಇಂದು {0}/{1} ಔಷಧಿ ತೆಗೆದುಕೊಳ್ಳಲಾಗಿದೆ").format(taken_count, len(todays)))
    
    st.divider()
    st.caption(t("Setup: Set reminder times in sidebar. App will remind you when you open. For phone notifications, allow in browser. This is clean working version, can add plyer/beep in desktop app.","ಸೆಟಪ್: ಸೈಡ್‌ಬಾರ್‌ನಲ್ಲಿ ಸಮಯ ಹೊಂದಿಸಿ. ತೆರೆದಾಗ ರಿಮೈಂಡ್ ಮಾಡುತ್ತದೆ. ಫೋನ್ ನೋಟಿಫಿಕೇಶನ್‌ಗೆ ಬ್ರೌಸರ್‌ನಲ್ಲಿ ಅನುಮತಿಸಿ."))

st.sidebar.markdown("---")
st.sidebar.write("Built by Bharath Gowda | AI + Reminder v3.0 | For Karnataka Elders")
st.sidebar.write(t("Safety: Confirm with pharmacist. Not a doctor.","ಸುರಕ್ಷತೆ: ಫಾರ್ಮಸಿಸ್ಟ್‌ನೊಂದಿಗೆ ಖಚಿತಪಡಿಸಿಕೊಳ್ಳಿ."))
