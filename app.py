import streamlit as st
import httpx
import pandas as pd
from datetime import date, timedelta
import random

# --- 1. 網頁基本設定 (全域唯一) ---
st.set_page_config(page_title="LexiMatrix Pro", page_icon="🛡️", layout="wide")

# --- 2. 初始化全域狀態 (保留你原本的邏輯) ---
if 'show_balloons' not in st.session_state: st.session_state.show_balloons = False
if 'duplicate_word' not in st.session_state: st.session_state.duplicate_word = None
if 'force_quiz_word' not in st.session_state: st.session_state.force_quiz_word = None
if 'sudden_quiz_state' not in st.session_state:
    st.session_state.sudden_quiz_state = {'attempts': 0, 'msg': None, 'msg_type': None}

if st.session_state.show_balloons:
    st.balloons()
    st.session_state.show_balloons = False

# --- 3. Supabase 連線與常數設定 ---
URL = st.secrets["connections"]["supabase"]["url"]
KEY = st.secrets["connections"]["supabase"]["key"]
HEADERS = {"apikey": KEY, "Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}
POS_OPTIONS = ["n. (名詞)", "v. (動詞)", "adj. (形容詞)", "adv. (副詞)", "phr. (慣用語)", "Term. (專業術語)"]
INTERVALS = {0: 0, 1: 1, 2: 3, 3: 7, 4: 14, 5: 30}
MAX_LEVEL = 5

# --- 4. 功能函式 (對接雲端) ---
def get_next_review_date(mastery_level):
    days = INTERVALS.get(mastery_level, 0)
    return str(date.today() + timedelta(days=days))

def load_data():
    api_url = f"{URL}/rest/v1/vocabulary?select=*&order=id.desc"
    try:
        response = httpx.get(api_url, headers=HEADERS)
        return response.json()
    except: return []

def update_word_mastery(word_id, new_mastery):
    """更新單字等級與複習日期"""
    api_url = f"{URL}/rest/v1/vocabulary?id=eq.{word_id}"
    next_date = get_next_review_date(new_mastery)
    payload = {
        "mastery": new_mastery,
        "last_reviewed": str(date.today()),
        "next_review": next_date
    }
    httpx.patch(api_url, json=payload, headers=HEADERS)

def add_new_word(payload):
    api_url = f"{URL}/rest/v1/vocabulary"
    response = httpx.post(api_url, json=payload, headers=HEADERS)
    return response.status_code == 201

# --- 5. 側邊欄導航 (唯一的導航中心) ---
with st.sidebar:
    st.title("🛡️ LexiMatrix 導航")
    choice = st.radio("前往頁面：", ["📋 管理矩陣", "🎯 訓練模式", "📅 遺忘排程"])
    st.divider()
    st.caption("v1.6 | 突擊測驗系統已上線")

# --- 6. 頁面邏輯分流 ---

if choice == "📋 管理矩陣":
    st.title("📋 矩陣資料庫管理")
    
    # --- 新增單字區 (原 tabs[0]) ---
    with st.expander("➕ 新增單字至矩陣 (點擊展開)"):
        with st.form("add_word_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                word = st.text_input("英文單字* (必填)")
                pos = st.multiselect("詞性 (可複選)", POS_OPTIONS)
                category = st.text_input("類別", "未分類")
            with c2:
                meaning = st.text_input("中文翻譯")
                synonyms = st.text_input("同義詞")
                collocations = st.text_input("慣用搭配")
            
            submitted = st.form_submit_button("💾 儲存至矩陣")
            if submitted:
                if word.strip():
                    word_clean = word.strip()
                    all_data = load_data()
                    duplicate = next((w for w in all_data if w['word'].lower() == word_clean.lower()), None)
                    
                    if duplicate:
                        st.session_state.duplicate_word = word_clean
                    else:
                        payload = {
                            "word": word_clean, "pos": ", ".join(pos), "meaning_zh": meaning,
                            "category": category, "synonyms": synonyms, "example": "", # 依此類推
                            "mastery": 1, "last_reviewed": str(date.today()),
                            "next_review": get_next_review_date(1)
                        }
                        if add_new_word(payload):
                            st.success(f"✅ 已成功錄入：{word_clean}")
                            st.rerun()
                else:
                    st.error("❌ 請輸入英文單字！")

    # --- 處理重複與突擊測驗邏輯 ---
    if st.session_state.duplicate_word:
        dw = st.session_state.duplicate_word
        st.warning(f"⚠️ 單字「**{dw}**」已存在！")
        if st.button(f"⚔️ 直接對「{dw}」發動突擊測驗！"):
            st.session_state.force_quiz_word = dw
            st.session_state.duplicate_word = None
            st.rerun()

    if st.session_state.force_quiz_word:
        dw = st.session_state.force_quiz_word
        all_data = load_data()
        quiz = next((w for w in all_data if w['word'].lower() == dw.lower()), None)
        
        if quiz:
            st.markdown(f"### 🔥 突擊測驗：{quiz['word'][0]}... (共 {len(quiz['word'])} 字母)")
            msg = st.session_state.sudden_quiz_state.get('msg')
            if msg: st.info(msg)
            else: st.info(f"💡 **中文提示**：{quiz['meaning_zh']}")

            with st.form("instant_quiz_form", clear_on_submit=True):
                ans = st.text_input("輸入拼寫：")
                if st.form_submit_button("送出"):
                    if ans.strip().lower() == quiz['word'].lower():
                        st.session_state.show_balloons = True
                        new_level = min(MAX_LEVEL, quiz['mastery'] + 1)
                        update_word_mastery(quiz['id'], new_level)
                        st.session_state.force_quiz_word = None
                        st.session_state.sudden_quiz_state = {'attempts': 0, 'msg': None, 'msg_type': None}
                        st.success(f"🎉 答對了！提升至 L{new_level}")
                        st.rerun()
                    else:
                        st.session_state.sudden_quiz_state['attempts'] += 1
                        attempts = st.session_state.sudden_quiz_state['attempts']
                        if attempts >= 3:
                            update_word_mastery(quiz['id'], 0) # 降級至 L0
                            st.error(f"💀 三振出局！正確答案是「{quiz['word']}」。已降級重練。")
                            st.session_state.force_quiz_word = None
                            st.session_state.sudden_quiz_state = {'attempts': 0, 'msg': None, 'msg_type': None}
                        else:
                            st.session_state.sudden_quiz_state['msg'] = f"❌ 錯誤！剩餘 {3-attempts} 次機會。"
                        st.rerun()

    # --- 顯示資料表 (原 tabs[1]) ---
    st.divider()
    all_data = load_data()
    if all_data:
        st.dataframe(pd.DataFrame(all_data), use_container_width=True)

elif choice == "🎯 訓練模式":
    st.title("🎯 單字訓練模式")
    st.write("這裡是純淨的測驗空間，不會出現新增欄位。")
    # 這裡可以接你其他的隨機測驗代碼

elif choice == "📅 遺忘排程":
    st.title("📅 遺忘排程")
    st.write("複習清單載入中...")