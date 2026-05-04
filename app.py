import streamlit as st
import httpx
import pandas as pd
from datetime import date, timedelta, datetime
import random
import re

# --- 1. 基本設定 ---
st.set_page_config(page_title="LexiMatrix Pro", page_icon="🛡️", layout="wide")

# --- 2. 初始化全域狀態 (防止 AttributeError) ---
if 'quiz_state' not in st.session_state:
    st.session_state.quiz_state = {'word': None, 'q_type': None, 'attempts': 0}
if 'show_balloons' not in st.session_state: 
    st.session_state.show_balloons = False
if 'duplicate_word' not in st.session_state: 
    st.session_state.duplicate_word = None
if 'force_quiz_word' not in st.session_state: 
    st.session_state.force_quiz_word = None

# 氣球特效觸發器
if st.session_state.show_balloons:
    st.balloons()
    st.session_state.show_balloons = False

# --- 3. Supabase 連線資訊 ---
URL = st.secrets["connections"]["supabase"]["url"]
KEY = st.secrets["connections"]["supabase"]["key"]
HEADERS = {"apikey": KEY, "Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}
INTERVALS = {0: 0, 1: 1, 2: 3, 3: 7, 4: 14, 5: 30}
MAX_LEVEL = 5

# --- 4. 工具函式 ---
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
    httpx.patch(api_url, json=payload, headers=HEADERS)

# --- 5. 側邊欄 ---
with st.sidebar:
    st.title("🛡️ LexiMatrix 導航")
    choice = st.radio("功能切換：", ["📋 管理矩陣", "🎯 訓練模式", "📅 遺忘排程"])
    st.divider()
    if st.button("♻️ 重新整理"): st.rerun()

# --- 6. 頁面邏輯 ---

# A. 管理矩陣
if choice == "📋 管理矩陣":
    st.title("📋 矩陣資料庫管理")
    raw_data = load_data()
    
    with st.expander("➕ 新增單字", expanded=not st.session_state.duplicate_word):
        with st.form("add_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                f_word = st.text_input("英文單字*")
                f_pos = st.multiselect("詞性 (可複選)", ["n.", "v.", "adj.", "adv.", "phr.", "Term."])
                f_cat = st.text_input("類別 (例如：托福)", value="未分類")
            with c2:
                f_mean = st.text_input("中文翻譯*")
                f_syn = st.text_input("同義詞")
                f_coll = st.text_input("慣用搭配")
            f_forms = st.text_input("三態/時態變化 (如: go-went-gone)")
            f_en_def = st.text_area("英文定義")
            f_ex = st.text_area("例句")
            
            if st.form_submit_button("🚀 錄入矩陣"):
                if f_word.strip() and f_mean.strip():
                    # 檢查重複單字 (不分大小寫)
                    dup = next((w for w in raw_data if w['word'].lower() == f_word.strip().lower()), None)
                    if dup:
                        st.session_state.duplicate_word = f_word.strip()
                        st.rerun()
                    else:
                        payload = {
                            "word": f_word.strip(), "meaning_zh": f_mean, "pos": ", ".join(f_pos),
                            "category": f_cat, "other_forms": f_forms, "synonyms": f_syn,
                            "collocations": f_coll, "meaning_en": f_en_def, "example": f_ex,
                            "mastery": 1, "next_review": get_next_review_date(1)
                        }
                        httpx.post(f"{URL}/rest/v1/vocabulary", json=payload, headers=HEADERS)
                        st.success("✅ 錄入成功！")
                        st.rerun()

    # --- 突擊測驗 (Sudden Quiz) ---
    if st.session_state.duplicate_word:
        dw = st.session_state.duplicate_word
        st.warning(f"⚠️ 單字「{dw}」已存在於矩陣中！")
        if st.button(f"⚔️ 發動突擊測驗挑戰「{dw}」"):
            st.session_state.force_quiz_word = dw
            st.session_state.duplicate_word = None
            st.rerun()

    if st.session_state.force_quiz_word:
        target_quiz = next((w for w in raw_data if w['word'].lower() == st.session_state.force_quiz_word.lower()), None)
        if target_quiz:
            st.info(f"🔥 突擊測驗！請拼寫出「{target_quiz['meaning_zh']}」的英文：")
            ans = st.text_input("你的回答：", key="sudden_quiz_input")
            if st.button("確認提交"):
                if ans.strip().lower() == target_quiz['word'].lower():
                    st.session_state.show_balloons = True
                    st.success("🎊 記憶力驚人！測驗通過！")
                    st.session_state.force_quiz_word = None
                    st.rerun()
                else: st.error("❌ 拼寫有誤，再想一下！")

    # 表格顯示 (編號從 1 開始)
    if raw_data:
        st.divider()
        df = pd.DataFrame(raw_data)
        df_display = df.rename(columns={'word':'單字','meaning_zh':'中文','pos':'詞性','category':'類別','mastery':'掌握度','other_forms':'三態/變化'})
        df_display.index = range(1, len(df_display) + 1)
        
        t0, t1, t2 = st.tabs(["🌱 新錄入/重練 (L0-1)", "🏃 穩定熟悉 (L2-3)", "👑 完全精通 (L4-5)"])
        with t0: st.dataframe(df_display[df_display['掌握度'] <= 1], use_container_width=True)
        with t1: st.dataframe(df_display[(df_display['掌握度'] > 1) & (df_display['掌握度'] <= 3)], use_container_width=True)
        with t2: st.dataframe(df_display[df_display['掌握度'] > 3], use_container_width=True)

# B. 訓練模式 (進化題型 + 懲罰機制)
elif choice == "🎯 訓練模式":
    st.title("🎯 深度訓練模式")
    raw_data = load_data()
    today_str = str(date.today())
    
    # 修正：日期安全過濾 (處理 None 與格式)
    due_list = [w for w in raw_data if not w.get('next_review') or str(w.get('next_review'))[:10] <= today_str]

    if due_list:
        if not st.session_state.quiz_state['word']:
            q = random.choice(due_list)
            st.session_state.quiz_state.update({'word': q['word'], 'attempts': 0})
            
            # 進化題型隨機選擇
            types = ["中文提示"]
            if q.get('example') and q['word'].lower() in q.get('example','').lower(): types.append("例句填空")
            if q.get('meaning_en'): types.append("英文定義題")
            st.session_state.quiz_state['q_type'] = random.choice(types)

        curr_q = next((w for w in due_list if w['word'] == st.session_state.quiz_state['word']), None)
        if curr_q:
            st.subheader(f"當前等級：Level {curr_q['mastery']}")
            q_type = st.session_state.quiz_state['q_type']
            st.info(f"💡 挑戰類型：**{q_type}**")
            
            if q_type == "例句填空":
                st.markdown(f"#### {re.sub(re.escape(curr_q['word']), '_______', curr_q['example'], flags=re.I)}")
            elif q_type == "英文定義題":
                st.markdown(f"#### {curr_q['meaning_en']}")
            else:
                st.markdown(f"#### 中文意思：{curr_q['meaning_zh']}")

            with st.form("training_form"):
                ans = st.text_input("拼寫單字：")
                if st.form_submit_button("送出答案"):
                    if ans.strip().lower() == curr_q['word'].lower():
                        st.session_state.show_balloons = True
                        new_mas = min(MAX_LEVEL, curr_q.get('mastery', 0) + 1)
                        update_supabase(curr_q['id'], {"mastery": new_mas, "next_review": get_next_review_date(new_mas)})
                        st.session_state.quiz_state['word'] = None # 重置觸發下一題
                        st.rerun()
                    else:
                        st.session_state.quiz_state['attempts'] += 1
                        att = st.session_state.quiz_state['attempts']
                        if att >= 3:
                            # 智慧懲罰：錯 3 次降為 0
                            update_supabase(curr_q['id'], {"mastery": 0, "next_review": today_str})
                            st.error(f"💀 失敗！答案是「{curr_q['word']}」，等級已降為 0 並排入重練。")
                            st.session_state.quiz_state['word'] = None
                        elif att == 1:
                            st.warning(f"❌ 錯誤！提示：這個字是以 `{curr_q['word'][0]}` 開頭的。")
                        else:
                            st.warning(f"❌ 再試一次！剩餘 1 次機會。")
                        st.rerun()
    else:
        st.success("🎉 今日複習已全數完成！大腦需要休息，明天再來！")

# C. 遺忘排程
elif choice == "📅 遺忘排程":
    st.title("📅 遺忘排程追蹤")
    raw_data = load_data()
    if raw_data:
        df = pd.DataFrame(raw_data)
        # 修正：日期物件比較 (解決 TypeError)
        df['next_review_dt'] = pd.to_datetime(df['next_review']).dt.date
        today = date.today()
        
        due_today = df[df['next_review_dt'] <= today].copy()
        due_future = df[df['next_review_dt'] > today].sort_values('next_review_dt').copy()
        
        # 顯示欄位整理與編號
        for d in [due_today, due_future]:
            d.rename(columns={'word':'單字','meaning_zh':'中文','mastery':'掌握度','next_review_dt':'排程日期'}, inplace=True)
            d.index = range(1, len(d) + 1)

        c1, c2 = st.columns(2)
        with c1:
            st.error(f"🔥 今日待辦 ({len(due_today)} 字)")
            st.dataframe(due_today[['單字', '中文', '掌握度']], use_container_width=True)
        with c2:
            st.info(f"📅 未來排程 ({len(due_future)} 字)")
            st.dataframe(due_future[['排程日期', '單字', '掌握度']], use_container_width=True)