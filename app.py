import streamlit as st
import httpx
import pandas as pd
from datetime import date, timedelta
import random
import re

# --- 1. 頁面基本設定 ---
st.set_page_config(page_title="LexiMatrix Pro", page_icon="🛡️", layout="wide")

# --- 2. 初始化全域狀態 ---
if 'quiz_state' not in st.session_state:
    st.session_state.quiz_state = {'word': None, 'q_type': None, 'attempts': 0, 'msg': None, 'msg_type': None}
if 'show_balloons' not in st.session_state: st.session_state.show_balloons = False
if 'duplicate_word' not in st.session_state: st.session_state.duplicate_word = None

if st.session_state.get('show_balloons'):
    st.balloons()
    st.session_state.show_balloons = False

# --- 3. 連線資訊與常數 ---
URL = st.secrets["connections"]["supabase"]["url"]
KEY = st.secrets["connections"]["supabase"]["key"]
HEADERS = {"apikey": KEY, "Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}
POS_OPTIONS = ["n.", "v.", "adj.", "adv.", "phr.", "Term."]
INTERVALS = {0: 0, 1: 1, 2: 3, 3: 7, 4: 14, 5: 30}
MAX_LEVEL = 5

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

def update_supabase(word_id, payload):
    api_url = f"{URL}/rest/v1/vocabulary?id=eq.{word_id}"
    try:
        response = httpx.patch(api_url, json=payload, headers=HEADERS)
        return response.status_code < 400
    except: return False

# --- 5. 側邊欄導航 ---
with st.sidebar:
    st.title("🛡️ LexiMatrix")
    choice = st.radio("功能清單", ["📋 管理矩陣", "🎯 訓練模式", "📅 遺忘排程"])
    st.divider()
    if st.button("♻️ 強制重新整理"): st.rerun()

# --- 6. 頁面分流 ---

if choice == "📋 管理矩陣":
    st.title("📋 矩陣資料庫管理")
    raw_data = load_data()

    # A. 新增單字
    with st.expander("➕ 新增單字至矩陣", expanded=False):
        with st.form("add_word_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                word = st.text_input("英文單字*")
                pos = st.multiselect("詞性", POS_OPTIONS)
                cat = st.text_input("類別", "未分類")
                forms = st.text_input("三態變化")
            with c2:
                mean = st.text_input("中文翻譯*")
                syn = st.text_input("同義詞")
                coll = st.text_input("慣用搭配")
            en_def = st.text_area("英文定義")
            example = st.text_area("例句")
            
            submitted = st.form_submit_button("🚀 錄入矩陣")
            if submitted:
                if word.strip() and mean.strip():
                    payload = {
                        "word": word.strip(), "pos": ", ".join(pos), "meaning_zh": mean,
                        "meaning_en": en_def, "example": example, "category": cat,
                        "synonyms": syn, "other_forms": forms, "collocations": coll,
                        "mastery": 1, "last_reviewed": str(date.today()),
                        "next_review": get_next_review_date(1)
                    }
                    res = httpx.post(f"{URL}/rest/v1/vocabulary", json=payload, headers=HEADERS)
                    if res.status_code < 300:
                        st.success(f"✅ {word} 已成功存入雲端！")
                        st.rerun()
                else: st.error("❌ 單字與中文為必填項")

    # B. 編輯與表格顯示
    if raw_data:
        st.divider()
        # 1. 編輯功能
        search_list = [w.get('word', 'Unknown') for w in raw_data]
        selected_word = st.selectbox("🔍 搜尋並管理單字：", search_list)
        target_w = next((w for w in raw_data if w.get('word') == selected_word), None)
        
        if target_w:
            with st.container(border=True):
                if st.toggle("✏️ 修改資料"):
                    with st.form(f"edit_{target_w['id']}"):
                        c1, c2 = st.columns(2)
                        with c1:
                            u_word = st.text_input("單字", value=target_w.get('word',''))
                            u_mas = st.number_input("掌握度", 0, 5, value=int(target_w.get('mastery', 0)))
                        with c2:
                            u_mean = st.text_input("中文", value=target_w.get('meaning_zh',''))
                            u_cat = st.text_input("類別", value=target_w.get('category',''))
                        u_def = st.text_area("定義", value=target_w.get('meaning_en',''))
                        u_ex = st.text_area("例句", value=target_w.get('example',''))
                        
                        if st.form_submit_button("💾 儲存修改"):
                            up_payload = {"word": u_word, "meaning_zh": u_mean, "mastery": u_mas, "meaning_en": u_def, "example": u_ex, "category": u_cat}
                            if update_supabase(target_w['id'], up_payload):
                                st.success("更新成功！")
                                st.rerun()
                else:
                    st.subheader(f"🔤 {target_w.get('word')}")
                    st.markdown(f"**中文：** {target_w.get('meaning_zh')} | **掌握度：** L{target_w.get('mastery')}")
                    st.info(f"**定義：**\n{target_w.get('meaning_en') or '未填'}")

        # 2. 表格總表
        st.divider()
        df = pd.DataFrame(raw_data)
        t1, t2, t3 = st.tabs(["🌱 L0-L1", "🏃 L2-L3", "👑 L4-L5"])
        with t1: st.dataframe(df[df['mastery'].isin([0, 1])][["word", "meaning_zh", "category", "mastery"]], use_container_width=True)
        with t2: st.dataframe(df[df['mastery'].isin([2, 3])][["word", "meaning_zh", "category", "mastery"]], use_container_width=True)
        with t3: st.dataframe(df[df['mastery'].isin([4, 5])][["word", "meaning_zh", "category", "mastery"]], use_container_width=True)
    else:
        st.info("矩陣目前是空的，請點選上方「新增單字」。")

elif choice == "🎯 訓練模式":
    st.title("🎯 單字複習訓練")
    raw_data = load_data()
    today = str(date.today())
    # 安全篩選：處理空日期
    target_list = [w for w in raw_data if str(w.get('next_review', today)) <= today]

    if target_list:
        if not st.session_state.quiz_state['word']:
            q = random.choice(target_list)
            st.session_state.quiz_state.update({'word': q['word'], 'attempts': 0, 'msg': None})
            # 隨機決定題型
            opts = ["中文"]
            if q.get('example') and q['word'].lower() in q.get('example','').lower(): opts.append("例句填空")
            st.session_state.quiz_state['q_type'] = random.choice(opts)

        curr_q = next((w for w in target_list if w['word'] == st.session_state.quiz_state['word']), None)
        if curr_q:
            st.write(f"### 目前挑戰：Level {curr_q['mastery']}")
            q_type = st.session_state.quiz_state['q_type']
            
            if q_type == "例句填空":
                st.info(f"💡 填空題目：\n{re.sub(re.escape(curr_q['word']), '_______', curr_q['example'], flags=re.I)}")
            else:
                st.info(f"💡 中文提示：**{curr_q['meaning_zh']}**")
            
            with st.form("quiz_form"):
                ans = st.text_input("請輸入英文單字：")
                if st.form_submit_button("提交"):
                    if ans.strip().lower() == curr_q['word'].lower():
                        st.session_state.show_balloons = True
                        new_mas = min(5, curr_q['mastery'] + 1)
                        update_supabase(curr_q['id'], {"mastery": new_mas, "next_review": get_next_review_date(new_mas)})
                        st.session_state.quiz_state['word'] = None # 清空題目觸發下一題
                        st.rerun()
                    else:
                        st.error("不對喔，再想一下！")
    else:
        st.success("🎉 今日複習任務已完成！大腦需要休息，明天再來吧。")

elif choice == "📅 遺忘排程":
    st.title("📅 遺忘曲線分析")
    raw_data = load_data()
    if raw_data:
        df = pd.DataFrame(raw_data)
        st.metric("矩陣總單字量", len(df))
        st.subheader("掌握度分佈")
        st.bar_chart(df['mastery'].value_counts())
        
        st.subheader("待複習清單")
        today = str(date.today())
        pending = df[df['next_review'] <= today]
        st.dataframe(pending[["word", "meaning_zh", "next_review"]], use_container_width=True)
    else:
        st.warning("暫無資料可供分析。")