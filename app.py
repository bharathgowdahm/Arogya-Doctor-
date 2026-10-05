import streamlit as st
from datetime import datetime, date, time, timedelta
import json
import requests

st.set_page_config(page_title="ArogyaMitra AI + Reminder", page_icon="💊", layout="wide")

# Language
lang = st.sidebar.selectbox("Language / ಭಾಷೆ", ["ಕನ್ನಡ", "English"])

def t(en, kn):
    return kn if lang == "ಕನ್ನಡ" else en

# ===== API KEY SETUP - SIDEBAR =====
st.sidebar.markdown("---")
st.sidebar.markdown(f"### {t('🔑 AI API Setup','🔑 AI API ಸೆಟಪ್')}")
st.sidebar.caption(t(
    "Paste Gemini API key (new AQ. format or old AIzaSy format)",
    "Gemini API key ಹಾಕಿ (ಹೊಸ AQ. ಅಥವಾ ಹಳೆಯ AIzaSy ಫಾರ್ಮ್ಯಾಟ್)"
))

# API key input - secure (supports both AQ. and AIzaSy formats)
api_key = st.sidebar.text_input(
    t("Gemini API Key", "Gemini API Key"),
    type="password",
    placeholder="AQ.Ab8RN6... or AIzaSy...",
    help="Get free key from aistudio.google.com/app/apikey"
).strip()

# Also support secrets.toml for Streamlit Cloud
if not api_key:
    try:
        api_key = st.secrets.get("GEMINI_API_KEY", "").strip()
        if api_key:
            st.sidebar.success(t("API key loaded from secrets", "API key secrets ನಿಂದ ಲೋಡ್ ಆಗಿದೆ"))
    except Exception:
        pass

# Validate key format (both AQ. and AIzaSy supported)
def is_valid_key_format(key: str) -> bool:
    if not key:
        return False
    return key.startswith("AQ.") or key.startswith("AIzaSy")

if api_key:
    if is_valid_key_format(api_key):
        key_type = "AQ (new)" if api_key.startswith("AQ.") else "AIzaSy (legacy)"
        st.sidebar.success(f"✅ API Ready [{key_type}] - AI can explain any medicine!")
    else:
        st.sidebar.warning(t(
            "Key format looks unusual. Expected AQ.xxx or AIzaSy...",
            "Key ಫಾರ್ಮ್ಯಾಟ್ ಸರಿ ಇಲ್ಲ. AQ.xxx ಅಥವಾ AIzaSy... ಬೇಕು."
        ))
else:
    st.sidebar.warning(t(
        "No API key - Using local 10 medicines only. Add key for unlimited AI.",
        "API key ಇಲ್ಲ - 10 ಔಷಧಿ ಮಾತ್ರ. ಅನಿಯಮಿತ AI ಗೆ key ಸೇರಿಸಿ."
    ))

st.sidebar.markdown("[Get Free Gemini API Key](https://aistudio.google.com/app/apikey)")


# ===== GEMINI AI CALL (AQ. + AIzaSy compatible) =====
# These are the real, currently-available stable Gemini models.
# Ordered from most-preferred to fallback.
GEMINI_MODELS = [
    "gemini-2.5-flash",       # Current stable fast model (recommended)
    "gemini-2.5-flash-lite",  # Cheaper, faster variant
    "gemini-2.0-flash",       # Previous-generation stable
    "gemini-1.5-flash",       # Legacy fallback
]

def call_gemini_ai(medicine_name, api_key, lang):
    """
    Call Gemini to explain a medicine in Kannada + English.
    Compatible with BOTH new AQ. keys and legacy AIzaSy keys.
    AQ. keys MUST use the x-goog-api-key header (not the ?key= query param).
    """
    if not api_key:
        return None

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

    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 512,
            "responseMimeType": "application/json"  # force JSON output
        }
    }

    # CRITICAL: New AQ. keys require the header form.
    # The legacy `?key=` query param does NOT work with AQ. keys.
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key,
    }

    last_error = None
    for model in GEMINI_MODELS:
        try:
            url = (
                f"https://generativelanguage.googleapis.com/v1beta/"
                f"models/{model}:generateContent"
            )
            resp = requests.post(url, json=payload, headers=headers, timeout=25)

            if resp.status_code == 200:
                data = resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                text = text.replace("```json", "").replace("```", "").strip()
                return json.loads(text)

            elif resp.status_code in (400, 401, 403):
                # Auth / bad request — no point trying other models with same key
                last_error = f"{resp.status_code}: {resp.text[:200]}"
                st.error(
                    t(
                        f"API key rejected ({resp.status_code}). Please check your key.",
                        f"API key ತಿರಸ್ಕರಿಸಲಾಗಿದೆ ({resp.status_code}). Key ಪರಿಶೀಲಿಸಿ."
                    )
                )
                return None

            elif resp.status_code == 404:
                # Model not found — try next model
                last_error = f"{model} not available (404)"
                continue

            elif resp.status_code == 429:
                last_error = "Rate limit hit (429). Try again in a minute."
                continue

            else:
                last_error = f"{model} → {resp.status_code}: {resp.text[:150]}"
                continue

        except requests.exceptions.Timeout:
            last_error = f"{model} timed out"
            continue
        except json.JSONDecodeError:
            last_error = f"{model} returned invalid JSON"
            continue
        except Exception as e:
            last_error = f"{model} error: {e}"
            continue

    if last_error:
        st.error(f"AI Error: {last_error}")
    return None


# ===== LOCAL KNOWLEDGE BASE (Fallback) =====
MED_KB = {
    "paracetamol": {
        "use": "Fever / ಜ್ವರ",
        "kn": "ಜ್ವರ ಮತ್ತು ನೋವಿಗೆ. 6 ಗಂಟೆ ಅಂತರದಲ್ಲಿ 1 ಮಾತ್ರೆ, ದಿನಕ್ಕೆ 4 ಕ್ಕಿಂತ ಹೆಚ್ಚು ಬೇಡ. ಊಟದ ನಂತರ ತೆಗೆದುಕೊಳ್ಳಿ.",
        "en": "For fever and pain. 1 tab every 6 hours, max 4 per day, after food.",
        "tip": "After food / ಊಟದ ನಂತರ",
        "side": "No side if correct dose"
    },
    "dolo": {
        "use": "Fever / ಜ್ವರ",
        "kn": "Dolo 650 - ಜ್ವರ ಮತ್ತು ಮೈಕೈ ನೋವಿಗೆ. ಬೆಳಿಗ್ಗೆ 1, ರಾತ್ರಿ 1, 3 ದಿನ.",
        "en": "Dolo 650 for fever, body pain. Morning 1, Night 1.",
        "tip": "After food",
        "side": "No sleepiness"
    },
    "cetirizine": {
        "use": "Cold Allergy / ಶೀತ ಅಲರ್ಜಿ",
        "kn": "ಶೀತ, ಸೀನುವಿಕೆ, ಅಲರ್ಜಿಗೆ. ನಿದ್ದೆ ಬರಬಹುದು, ರಾತ್ರಿ ಮಾತ್ರ.",
        "en": "For cold, sneezing. May cause sleepiness, night only.",
        "tip": "Night only",
        "side": "Sleepiness / ನಿದ್ದೆ"
    },
    "azithromycin": {
        "use": "Infection / ಸೋಂಕು",
        "kn": "ಗಂಟಲು ಸೋಂಕಿಗೆ ಪ್ರತಿಜೀವಕ. ಪೂರ್ತಿ ಕೋರ್ಸ್ 3-5 ದಿನ ಮುಗಿಸಿ.",
        "en": "Antibiotic for throat infection. Complete course.",
        "tip": "Before food 1hr",
        "side": "Stomach upset"
    },
    "amoxicillin": {
        "use": "Infection / ಸೋಂಕು",
        "kn": "ಪ್ರತಿಜೀವಕ, ಹಲ್ಲು ನೋವು, ಗಂಟಲು ಸೋಂಕಿಗೆ. ಊಟದ ನಂತರ.",
        "en": "Antibiotic for tooth, throat.",
        "tip": "After food",
        "side": "Allergy check"
    },
    "omeprazole": {
        "use": "Acidity / ಆಸಿಡಿಟಿ",
        "kn": "ಗ್ಯಾಸ್, ಆಸಿಡಿಟಿ, ಹೊಟ್ಟೆ ಉರಿಗೆ. ಬೆಳಿಗ್ಗೆ ಖಾಲಿ ಹೊಟ್ಟೆಯಲ್ಲಿ.",
        "en": "For gas, acidity. Before breakfast.",
        "tip": "Before breakfast",
        "side": "Long use consult doctor"
    },
    "metformin": {
        "use": "Diabetes / ಸಕ್ಕರೆ",
        "kn": "ಮಧುಮೇಹಕ್ಕೆ, ಸಕ್ಕರೆ ನಿಯಂತ್ರಣ. ಊಟದ ನಂತರ ತಪ್ಪದೆ.",
        "en": "For diabetes sugar control. After food daily.",
        "tip": "After food daily",
        "side": "Take regularly"
    },
    "atorvastatin": {
        "use": "Cholesterol / ಕೊಬ್ಬು",
        "kn": "ಕೊಲೆಸ್ಟ್ರಾಲ್, ಹೃದಯ ರಕ್ಷಣೆಗೆ. ರಾತ್ರಿ.",
        "en": "For cholesterol, heart protection. Night.",
        "tip": "Night",
        "side": "Muscle pain"
    },
    "amlodipine": {
        "use": "BP / ರಕ್ತದೊತ್ತಡ",
        "kn": "ರಕ್ತದೊತ್ತಡಕ್ಕೆ. ಬೆಳಿಗ್ಗೆ ಒಂದೇ ಸಮಯಕ್ಕೆ.",
        "en": "For BP. Same time morning.",
        "tip": "Morning same time",
        "side": "Ankle swelling"
    },
    "pantoprazole": {
        "use": "Acidity / ಆಸಿಡಿಟಿ",
        "kn": "ಆಸಿಡಿಟಿ, ಹೊಟ್ಟೆ ಹುಣ್ಣಿಗೆ. ಬೆಳಿಗ್ಗೆ ಖಾಲಿ ಹೊಟ್ಟೆ.",
        "en": "Acidity, ulcer. Empty stomach morning.",
        "tip": "Empty stomach",
        "side": "Consult if long use"
    },
}

# ===== APP TITLE =====
st.title(t("💊 ArogyaMitra Pro - AI + Reminder", "💊 ಆರೋಗ್ಯಮಿತ್ರ ಪ್ರೊ - AI + ರಿಮೈಂಡರ್"))
st.caption(t(
    "Paste API key in sidebar → Search ANY medicine in Kannada",
    "ಸೈಡ್‌ಬಾರ್‌ನಲ್ಲಿ API key ಹಾಕಿ → ಯಾವುದೇ ಔಷಧಿ ಕನ್ನಡದಲ್ಲಿ ಹುಡುಕಿ"
))

# ===== SESSION STATES =====
if "meds" not in st.session_state:
    st.session_state.meds = [
        {"name": "Dolo 650", "m": 1, "n": 0, "ni": 1, "days": 3, "mt": time(8, 0), "nt": time(21, 0)},
        {"name": "Cetirizine", "m": 0, "n": 0, "ni": 1, "days": 2, "mt": time(8, 0), "nt": time(21, 30)},
    ]
if "taken" not in st.session_state:
    st.session_state.taken = {}
if "reminder_times" not in st.session_state:
    st.session_state.reminder_times = {
        "morning": time(8, 0),
        "noon": time(13, 0),
        "night": time(21, 0)
    }

# ===== SIDEBAR - REMINDER SETUP =====
st.sidebar.markdown(f"### {t('⚙️ Reminder Setup','⚙️ ರಿಮೈಂಡರ್ ಸೆಟಪ್')}")
st.session_state.reminder_times["morning"] = st.sidebar.time_input(
    t("Morning", "ಬೆಳಿಗ್ಗೆ"), st.session_state.reminder_times["morning"]
)
st.session_state.reminder_times["noon"] = st.sidebar.time_input(
    t("Noon", "ಮಧ್ಯಾಹ್ನ"), st.session_state.reminder_times["noon"]
)
st.session_state.reminder_times["night"] = st.sidebar.time_input(
    t("Night", "ರಾತ್ರಿ"), st.session_state.reminder_times["night"]
)

# ===== TABS =====
tab1, tab2, tab3 = st.tabs([
    t("📋 My Medicines", "📋 ನನ್ನ ಔಷಧಿಗಳು"),
    t("🤖 AI Search (with API key)", "🤖 AI ಹುಡುಕಾಟ"),
    t("⏰ Reminders", "⏰ ರಿಮೈಂಡರ್")
])

# ===== TAB 1: MY MEDICINES =====
with tab1:
    st.subheader(t("Add Medicine with Reminder", "ರಿಮೈಂಡರ್ ಜೊತೆ ಔಷಧಿ ಸೇರಿಸಿ"))

    with st.form("add_med"):
        c1, c2 = st.columns(2)
        name = c1.text_input(t("Medicine Name", "ಔಷಧಿ ಹೆಸರು"), placeholder="Dolo 650")
        days = c2.number_input(t("Days", "ದಿನಗಳು"), 1, 90, 3)

        c1, c2, c3 = st.columns(3)
        m = c1.number_input("🌅 " + t("Morning", "ಬೆಳಿಗ್ಗೆ"), 0, 4, 1)
        n = c2.number_input("☀️ " + t("Noon", "ಮಧ್ಯಾಹ್ನ"), 0, 4, 0)
        ni = c3.number_input("🌙 " + t("Night", "ರಾತ್ರಿ"), 0, 4, 1)

        c1, c2 = st.columns(2)
        mt = c1.time_input(t("Morning reminder", "ಬೆಳಿಗ್ಗೆ ರಿಮೈಂಡರ್"), time(8, 0))
        nt = c2.time_input(t("Night reminder", "ರಾತ್ರಿ ರಿಮೈಂಡರ್"), time(21, 0))

        if st.form_submit_button(t("➕ Add", "➕ ಸೇರಿಸಿ")) and name:
            st.session_state.meds.insert(0, {
                "name": name, "m": m, "n": n, "ni": ni,
                "days": days, "mt": mt, "nt": nt
            })
            st.success(f"{name} added!")
            st.balloons()

    st.divider()

    for i, med in enumerate(st.session_state.meds):
        with st.container(border=True):
            st.markdown(f"### {med['name']} | {med['days']} days")
            st.write(f"🌅 {med['m']} at {med['mt']} | 🌙 {med['ni']} at {med['nt']}")
            voice = (
                f"{med['name']}. ಬೆಳಿಗ್ಗೆ {med['m']} ಮಾತ್ರೆ "
                f"{med['mt'].strftime('%I:%M %p')} ಗೆ"
            )
            st.code(voice)
            if st.button("🗑️ Remove", key=f"del{i}"):
                st.session_state.meds.pop(i)
                st.rerun()

# ===== TAB 2: AI SEARCH =====
with tab2:
    st.subheader(t(
        "🤖 AI Search - Any Medicine in Kannada",
        "🤖 AI ಹುಡುಕಾಟ - ಯಾವುದೇ ಔಷಧಿ ಕನ್ನಡದಲ್ಲಿ"
    ))

    if not api_key:
        st.info(t(
            "👈 Paste Gemini API key in sidebar to enable AI for ANY medicine. "
            "Without key, only 10 local medicines work.",
            "👈 ಸೈಡ್‌ಬಾರ್‌ನಲ್ಲಿ Gemini API key ಹಾಕಿದರೆ ಯಾವುದೇ ಔಷಧಿ AI ವಿವರಿಸುತ್ತದೆ. "
            "Key ಇಲ್ಲದಿದ್ದರೆ 10 ಮಾತ್ರ."
        ))

    q = st.text_input(
        t("Medicine name", "ಔಷಧಿ ಹೆಸರು"),
        placeholder="E.g., Telma 40, Ecosprin, Vitamin D..."
    )

    col1, col2 = st.columns([1, 2])
    search_clicked = col1.button(
        t("🔍 AI Explain (Kannada)", "🔍 AI ವಿವರಿಸು"),
        type="primary"
    )

    if search_clicked and q:
        ql = q.lower().strip()

        # Check local KB first
        found_local = None
        for k in MED_KB:
            if k in ql or ql in k:
                found_local = k
                break

        if api_key:
            with st.spinner(t(
                f"AI searching {q} in Kannada...",
                f"AI {q} ಅನ್ನು ಕನ್ನಡದಲ್ಲಿ ಹುಡುಕುತ್ತಿದೆ..."
            )):
                ai_result = call_gemini_ai(q, api_key, lang)

            if ai_result:
                st.success(f"**{q.upper()}** - {ai_result['use']} (AI)")
                st.markdown(f"### {t('Kannada:','ಕನ್ನಡದಲ್ಲಿ:')} {ai_result['kn']}")
                st.markdown(f"**English:** {ai_result['en']}")
                st.info(f"💊 {ai_result['tip']} | ⚠️ {ai_result['side']}")
                st.code(f"{q} - {ai_result['kn']}")

                if st.button(f"➕ Add {q} to Reminders"):
                    st.session_state.meds.insert(0, {
                        "name": q.title(), "m": 1, "n": 0, "ni": 1,
                        "days": 3, "mt": time(8, 0), "nt": time(21, 0)
                    })
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
                st.warning(t(
                    f"'{q}' not in local DB. Add Gemini API key in sidebar to search ANY medicine.",
                    f"ಸ್ಥಳೀಯ DB ನಲ್ಲಿ ಇಲ್ಲ. ಸೈಡ್‌ಬಾರ್‌ನಲ್ಲಿ API key ಹಾಕಿ ಯಾವುದೇ ಔಷಧಿ ಹುಡುಕಿ."
                ))

    st.markdown("---")
    st.write(t("Try popular:", "ಪ್ರಯತ್ನಿಸಿ:"))
    cols = st.columns(5)
    for i, k in enumerate(list(MED_KB.keys())[:5]):
        with cols[i]:
            if st.button(k.title(), key=f"pop_{k}"):
                st.session_state["q"] = k
                st.info(MED_KB[k]["kn"])

# ===== TAB 3: REMINDERS =====
with tab3:
    st.subheader(t("⏰ Today's Schedule", "⏰ ಇಂದಿನ ವೇಳಾಪಟ್ಟಿ"))

    now = datetime.now().time()
    today_str = date.today().isoformat()
    todays = []

    for med in st.session_state.meds:
        if med["m"] > 0:
            todays.append({
                "time": med["mt"], "name": med["name"],
                "dose": med["m"], "period": "Morning", "icon": "🌅"
            })
        if med["n"] > 0:
            todays.append({
                "time": st.session_state.reminder_times["noon"],
                "name": med["name"], "dose": med["n"],
                "period": "Noon", "icon": "☀️"
            })
        if med["ni"] > 0:
            todays.append({
                "time": med["nt"], "name": med["name"],
                "dose": med["ni"], "period": "Night", "icon": "🌙"
            })

    todays = sorted(todays, key=lambda x: x["time"])
    next_dose = next((d for d in todays if d["time"] > now), None)

    if next_dose:
        delta = (
            datetime.combine(date.today(), next_dose["time"]) -
            datetime.combine(date.today(), now)
        )
        mins = int(delta.total_seconds() // 60)
        st.success(
            f"Next: {next_dose['name']} at "
            f"{next_dose['time'].strftime('%I:%M %p')} in {mins} min"
        )
        if 0 <= mins <= 15:
            st.toast(f"⏰ Take {next_dose['name']} now!", icon="💊")

    taken_count = 0
    for idx, d in enumerate(todays):
        key = f"{today_str}_{d['name']}_{d['time']}"
        is_taken = st.session_state.taken.get(key, False)

        c1, c2, c3 = st.columns([1, 3, 1])
        c1.write(f"**{d['time'].strftime('%I:%M %p')}**")
        c2.write(f"{d['icon']} {d['name']} - {d['dose']}")
        checked = c3.checkbox("Taken", value=is_taken, key=f"chk_{idx}")

        if checked != is_taken:
            st.session_state.taken[key] = checked
            if checked:
                st.balloons()

        if checked:
            taken_count += 1

    if todays:
        st.progress(
            taken_count / len(todays),
            text=f"{taken_count}/{len(todays)} taken"
        )

st.sidebar.markdown("---")
st.sidebar.caption("Built by Bharath Gowda | v4.1 AQ-Key Compatible")
