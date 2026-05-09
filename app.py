import streamlit as st
import httpx
import pandas as pd
from datetime import date, timedelta
import random
import re

# --- 1. 頁面配置與 PWA 高級感介面 ---
st.set_page_config(page_title="Qurate Pro", page_icon="⚡", layout="wide")

# 高級 CSS 注入：優化字體、按鈕與手機適配
st.markdown("""
    <style>
        [data-testid="stHeader"] { visibility: hidden; }
        footer { visibility: hidden; }
        .main-title {
            background: linear-gradient(90deg, #007bff, #00d4ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 800; font-size: 2.8rem; margin-bottom: 0.5rem;
        }
        .stButton > button {
            width: 100%; border-radius: 12px; height: 3.5rem;
            background: linear-gradient(135deg, #6e8efb, #a777e3);
            color: white; font-weight: bold; border: none; transition: 0.3s;
        }
        .stButton > button:hover { transform: scale(1.02); box-shadow: 0 10px 20px rgba(110, 142, 251, 0.3); }
        input { font-size: 16px !important; }
        div[data-testid="stMetric"] {
            background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 1.2rem; border-radius: 20px; backdrop-filter: blur(5px);
        }
    </style>
""", unsafe_allow_html=True)

# --- 2. 系統狀態初始化 ---
for key in ['quiz_state', 'show_balloons', 'duplicate_word', 'force_quiz_word']:
    if key not in st.session_state:
        if key == 'quiz_state': st.session_state[key] = {'word': None}
        else: st.session_state[key] = False

if st.session_state.show_balloons:
    st.balloons(); st.session_state.show_balloons = False

# --- 3. 核心 API 與艾賓浩斯演算法 ---
URL = st.secrets["connections"]["supabase"]["url"]
KEY = st.secrets["connections"]["supabase"]["key"]
HEADERS = {"apikey": KEY, "Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}

def get_next_review_date(mastery):
    # 艾賓浩斯等級：1, 3, 7, 14, 30 天
    curve = {0: 0, 1: 1, 2: 3, 3: 7, 4: 14, 5: 30}
    days = curve.get(mastery, 1)
    return str(date.today() + timedelta(days=days))

def load_data():
    try:
        resp = httpx.get(f"{URL}/rest/v1/vocabulary?select=*&order=next_review.asc", headers=HEADERS)
        return resp.json()
    except: return []

# --- 4. 側邊欄導航 ---
st.sidebar.markdown("<h1 style='color: #007bff;'>⚡ Qurate Pro</h1>", unsafe_allow_html=True)
choice = st.sidebar.radio("SYSTEM ACCESS", ["📋 Matrix Core", "🎯 Flash Pulse", "📅 Ebbing Log"])
st.sidebar.divider()
st.sidebar.caption("PWA Engine v1.0 | Authorized Access Only")

# --- 5. 功能模組 ---

# 模組 A: Matrix Core (核心資料庫與管理)
if choice == "📋 Matrix Core":
    st.markdown("<div class='main-title'>Matrix Core</div>", unsafe_allow_html=True)
    raw_data = load_data()
    df = pd.DataFrame(raw_data) if raw_data else pd.DataFrame()

    t_add, t_edit, t_view = st.tabs(["➕ Initialize Node", "📝 Modify Protocol", "🔍 View Matrix"])

    with t_add:
        with st.form("add_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            f_word = c1.text_input("Entry (英文單字)*")
            f_mean = c2.text_input("Definition (中文翻譯)*")
            
            st.write("---")
            st.caption("Morphology (動詞三態 / 詞類變化)")
            v1, v2, v3 = st.columns(3)
            f_v1 = v1.text_input("Base (V1)", placeholder="e.g. eat")
            f_v2 = v2.text_input("Past (V2)", placeholder="e.g. ate")
            f_v3 = v3.text_input("P.P. (V3)", placeholder="e.g. eaten")
            
            st.write("---")
            f_pos = st.multiselect("Class (詞性)", ["n.", "v.", "adj.", "adv.", "phr.", "prep."])
            
            c3, c4 = st.columns(2)
            f_syn = c3.text_input("Synonyms (同義詞)")
            f_coll = c4.text_input("Collocations (常用搭配)")
            
            f_def_en = st.text_area("English Definition (英文定義)")
            f_ex = st.text_area("Context Sentence (例句)")
            
            if st.form_submit_button("🚀 SYNC TO CORE"):
                if f_word.strip() and f_mean.strip():
                    # 檢查重複
                    dup = next((w for w in raw_data if w['word'].lower() == f_word.strip().lower()), None)
                    if dup:
                        st.session_state.duplicate_word = f_word.strip()
                        st.rerun()
                    else:
                        variants = f"{f_v1} / {f_v2} / {f_v3}" if f_v1 else ""
                        payload = {
                            "word": f_word.strip(), "meaning_zh": f_mean.strip(), "pos": ", ".join(f_pos),
                            "other_forms": variants, "synonyms": f_syn, "collocations": f_coll,
                            "meaning_en": f_def_en, "example": f_ex, "mastery": 1, "next_review": get_next_review_date(1)
                        }
                        httpx.post(f"{URL}/rest/v1/vocabulary", json={k:v for k,v in payload.items() if v}, headers=HEADERS)
                        st.session_state.show_balloons = True; st.rerun()

    with t_edit:
        if not df.empty:
            target = st.selectbox("Select Node to Modify", options=df['word'].tolist())
            row = df[df['word'] == target].iloc[0]
            # 劍橋發音聯動
            st.link_button(f"🔊 Audio: {target} (Cambridge)", f"https://dictionary.cambridge.org/dictionary/english-chinese-traditional/{target.replace(' ', '-')}")
            
            with st.form("modify_form"):
                u_word = st.text_input("Entry", value=row.get('word',''))
                u_mean = st.text_input("Definition", value=row.get('meaning_zh',''))
                u_syn = st.text_input("Synonyms", value=row.get('synonyms',''))
                u_ex = st.text_area("Context", value=row.get('example',''))
                b_save, b_del, _ = st.columns([1, 1, 4])
                if b_save.form_submit_button("UPDATE"):
                    upd = {"word": u_word, "meaning_zh": u_mean, "synonyms": u_syn, "example": u_ex}
                    httpx.patch(f"{URL}/rest/v1/vocabulary?id=eq.{row['id']}", json=upd, headers=HEADERS)
                    st.rerun()
                if b_del.form_submit_button("PURGE"):
                    httpx.delete(f"{URL}/rest/v1/vocabulary?id=eq.{row['id']}", headers=HEADERS)
                    st.rerun()

    with t_view:
        if not df.empty:
            # 分區檢視功能
            v_f = st.radio("Filter Protocol", ["All Nodes", "Due Today", "Mastered (L5)"], horizontal=True)
            search = st.text_input("🔍 Neural Search...")
            d_df = df.copy()
            if v_f == "Due Today": d_df = d_df[pd.to_datetime(d_df['next_review']).dt.date <= date.today()]
            elif v_f == "Mastered (L5)": d_df = d_df[d_df['mastery'] >= 5]
            if search: d_df = d_df[d_df['word'].str.contains(search, case=False) | d_df['meaning_zh'].str.contains(search)]
            st.dataframe(d_df[['word', 'meaning_zh', 'other_forms', 'mastery', 'next_review']], use_container_width=True)

    # 重複單字突擊挑戰
    if st.session_state.duplicate_word:
        st.error(f"Collision Detected: '{st.session_state.duplicate_word}' exists in Matrix.")
        if st.button("⚔️ Start Force Challenge"):
            st.session_state.force_quiz_word = st.session_state.duplicate_word
            st.session_state.duplicate_word = False; st.rerun()
    if st.session_state.force_quiz_word:
        q_ans = st.text_input(f"Verify Entry '{st.session_state.force_quiz_word}':")
        if st.button("CONFIRM IDENTITY"):
            if q_ans.lower() == st.session_state.force_quiz_word.lower():
                st.session_state.show_balloons = True; st.session_state.force_quiz_word = False; st.rerun()
            else: st.error("Verification failed.")

# 模組 B: Flash Pulse (閃擊訓練)
elif choice == "🎯 Flash Pulse":
    st.markdown("<div class='main-title'>Flash Pulse</div>", unsafe_allow_html=True)
    raw_data = load_data()
    due = [w for w in raw_data if str(w.get('next_review'))[:10] <= str(date.today())]
    
    if not st.session_state.quiz_state['word']:
        if due: st.session_state.quiz_state['word'] = random.choice(due)['word']
        else: st.success("✨ Neural Matrix Stable. No pending tasks."); st.stop()

    target = next((w for w in due if w['word'] == st.session_state.quiz_state['word']), None)
    if target:
        st.info(f"💡 Neural Cue: {target['meaning_zh']}")
        st.markdown(f"[🔊 Audio Tip](https://dictionary.cambridge.org/dictionary/english-chinese-traditional/{target['word'].replace(' ', '-')})")
        ans = st.text_input("Entry Input:")
        if st.button("EXECUTE"):
            if ans.strip().lower() == target['word'].lower():
                st.session_state.show_balloons = True
                new_m = min(5, target['mastery'] + 1)
                httpx.patch(f"{URL}/rest/v1/vocabulary?id=eq.{target['id']}", 
                            json={"mastery": new_m, "next_review": get_next_review_date(new_m)}, headers=HEADERS)
                st.session_state.quiz_state['word'] = None; st.rerun()
            else: st.error("Inconsistent Node. Try again.")

# 模組 C: Ebbing Log (數據與預測)
elif choice == "📅 Ebbing Log":
    st.markdown("<div class='main-title'>Ebbing Log</div>", unsafe_allow_html=True)
    raw_data = load_data()
    if raw_data:
        df = pd.DataFrame(raw_data)
        df['date'] = pd.to_datetime(df['next_review']).dt.date
        
        # 線型預測圖表 (未來 7 天)
        st.subheader("📈 Retention Projection (7-Day Line Forecast)")
        f_dates = [date.today() + timedelta(days=i) for i in range(8)]
        f_counts = [len(df[df['date'] <= d]) for d in f_dates]
        chart_data = pd.DataFrame({"Date": f_dates, "Cumulative Load": f_counts}).set_index("Date")
        st.line_chart(chart_data) # 改為線型圖
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Due Today", len(df[df['date'] <= date.today()]))
        c2.metric("Total Nodes", len(df))
        c3.metric("L5 Mastery", len(df[df['mastery'] == 5]))