import streamlit as st
import httpx
import pandas as pd
from datetime import date, timedelta
import random

# --- 1. 網頁基本設定 (全域唯一) ---
st.set_page_config(page_title="LexiMatrix Pro", page_icon="🛡️", layout="wide")

# --- 2. 初始化全域狀態 ---
if 'show_balloons' not in st.session_state: st.session_state.show_balloons = False
if 'duplicate_word' not in st.session_state: st.session_state.duplicate_word = None
if 'force_quiz_word' not in st.session_state: st.session_state.force_quiz_word = None
if 'sudden_quiz_state' not in st.session_state:
    st.session_state.sudden_quiz_state = {'attempts': 0, 'msg': None, 'msg_type': None}

if st.session_state.show_balloons:
    st.balloons()
    st.session_state.show_balloons = False

# --- 3. Supabase 連線設定 ---
URL = st.secrets["connections"]["supabase"]["url"]
KEY = st.secrets["connections"]["supabase"]["key"]
HEADERS = {"apikey": KEY, "Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}
POS_OPTIONS = ["n.", "v.", "adj.", "adv.", "phr.", "Term."]
INTERVALS = {0: 0, 1: 1, 2: 3, 3: 7, 4: 14, 5: 30}

# --- 4. 功能函式 ---
def get_next_review_date(mastery_level):
    days = INTERVALS.get(mastery_level, 0)
    return str(date.today() + timedelta(days=days))

def load_data():
    api_url = f"{URL}/rest/v1/vocabulary?select=*&order=id.desc"
    try:
        response = httpx.get(api_url, headers=HEADERS)
        return response.json()
    except: return []

# --- 5. 側邊欄導航 ---
with st.sidebar:
    st.title("🛡️ LexiMatrix 導航")
    choice = st.radio("前往頁面：", ["📋 管理矩陣", "🎯 訓練模式", "📅 遺忘排程"])
    st.divider()

# --- 6. 頁面邏輯分流 ---

if choice == "📋 管理矩陣":
    st.title("📋 矩陣資料庫管理")
    raw_data = load_data()
    
    if raw_data:
        search_list = [w.get('word', '未知') for w in raw_data]
        search_word = st.selectbox("🔍 選擇單字進行預覽或編輯：", search_list)
        target_w = next((w for w in raw_data if w.get('word') == search_word), None)
        
        if target_w:
            with st.container(border=True):
                edit_mode = st.toggle("✏️ 開啟修改模式 (可編輯定義與例句)")
                
                if edit_mode:
                    with st.form("edit_form"):
                        col1, col2 = st.columns(2)
                        with col1:
                            u_word = st.text_input("單字", value=target_w.get('word', ''))
                            # 處理詞性轉換
                            old_pos = target_w.get('pos', '')
                            d_pos = [p.strip() for p in old_pos.split(',')] if isinstance(old_pos, str) else []
                            u_pos = st.multiselect("詞性", POS_OPTIONS, default=[p for p in d_pos if p in POS_OPTIONS])
                            u_cat = st.text_input("類別", value=target_w.get('category', ''))
                        with col2:
                            u_mean = st.text_input("中文", value=target_w.get('meaning_zh', ''))
                            u_syn = st.text_input("同義詞", value=target_w.get('synonyms', ''))
                            u_form = st.text_input("三態/變化", value=target_w.get('other_forms', ''))
                            u_mas = st.number_input("等級", 0, 5, value=int(target_w.get('mastery', 0)))
                        
                        # ✨ 這裡補上了你說缺少的欄位
                        u_def = st.text_area("英文定義", value=target_w.get('meaning_en', ''))
                        u_ex = st.text_area("例句", value=target_w.get('example', ''))
                        
                        if st.form_submit_button("💾 儲存修改"):
                            up_payload = {
                                "word": u_word, "pos": ", ".join(u_pos), "meaning_zh": u_mean,
                                "meaning_en": u_def, "example": u_ex, "category": u_cat,
                                "synonyms": u_syn, "other_forms": u_form, "mastery": u_mas,
                                "next_review": get_next_review_date(u_mas)
                            }
                            httpx.patch(f"{URL}/rest/v1/vocabulary?id=eq.{target_w['id']}", json=up_payload, headers=HEADERS)
                            st.success("更新成功！")
                            st.rerun()
                else:
                    # 預覽模式
                    st.subheader(f"🔤 {target_w['word']}")
                    st.write(f"**中文：** {target_w.get('meaning_zh')}")
                    st.info(f"**📖 定義：**\n{target_w.get('meaning_en', '未填')}")
                    st.warning(f"**📝 例句：**\n{target_w.get('example', '未填')}")

    # --- 新增單字區 (縮小並放在最下面) ---
    st.divider()
    with st.expander("➕ 新增單字"):
        # 這裡放你原本的新增單字表單...
        st.write("新增單字表單內容...")

elif choice == "🎯 訓練模式":
    st.title("🎯 單字訓練模式")
    # 這裡把突擊測驗的邏輯搬過來
    all_words = load_data()
    if all_words:
        st.write("### 🔥 隨機挑戰")
        if st.button("開始測驗"):
            q = random.choice(all_words)
            st.session_state.quiz_state['word'] = q['word']
            st.session_state.quiz_state['meaning'] = q['meaning_zh']
        
        if st.session_state.quiz_state.get('word'):
            st.info(f"這個單字的意思是：**{st.session_state.quiz_state['meaning']}**")
            ans = st.text_input("請輸入英文單字：")
            if st.button("送出答案"):
                if ans.lower() == st.session_state.quiz_state['word'].lower():
                    st.balloons()
                    st.success("太棒了！答對了！")
                else:
                    st.error(f"可惜錯了，答案是 {st.session_state.quiz_state['word']}")
    else:
        st.warning("資料庫空空的，先去管理矩陣加點單字吧！")

elif choice == "📅 遺忘排程":
    st.title("📅 遺忘排程")
    st.write("這裡是你的複習進度...")