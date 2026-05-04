import streamlit as st
import httpx
import pandas as pd
from datetime import date, timedelta
import random
import re

# --- 1. 頁面設定 ---
st.set_page_config(page_title="LexiMatrix Pro", page_icon="🛡️", layout="wide")

# --- 2. 狀態初始化 ---
for key in ['quiz_state', 'show_balloons', 'duplicate_word', 'force_quiz_word']:
    if key not in st.session_state:
        if key == 'quiz_state': st.session_state[key] = {'word': None, 'q_type': None, 'attempts': 0}
        else: st.session_state[key] = None if 'word' in key else False

if st.session_state.show_balloons:
    st.balloons()
    st.session_state.show_balloons = False

# --- 3. Supabase 配置 ---
URL = st.secrets["connections"]["supabase"]["url"]
KEY = st.secrets["connections"]["supabase"]["key"]
HEADERS = {"apikey": KEY, "Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}
INTERVALS = {0: 0, 1: 1, 2: 3, 3: 7, 4: 14, 5: 30}

# --- 4. 工具函式 ---
def get_next_review_date(mastery_level):
    return str(date.today() + timedelta(days=INTERVALS.get(mastery_level, 0)))

def load_data():
    try:
        # 加上 nocache 參數確保抓到最新資料
        response = httpx.get(f"{URL}/rest/v1/vocabulary?select=*&order=id.desc", headers=HEADERS)
        return response.json()
    except: return []

# --- 5. 側邊欄 ---
with st.sidebar:
    st.title("🛡️ LexiMatrix")
    choice = st.radio("選單", ["📋 管理矩陣", "🎯 訓練模式", "📅 遺忘排程"])
    st.divider()
    if st.button("♻️ 強制整理"): st.rerun()

# --- 6. 主要功能 ---

if choice == "📋 管理矩陣":
    st.title("📋 矩陣資料庫管理")
    raw_data = load_data()
    
    with st.expander("➕ 新增單字", expanded=not st.session_state.duplicate_word):
        with st.form("add_word_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                f_word = st.text_input("英文單字*")
                f_pos = st.multiselect("詞性", ["n.", "v.", "adj.", "adv.", "phr."])
                f_cat = st.text_input("類別", "未分類")
            with c2:
                f_mean = st.text_input("中文翻譯*")
                f_forms = st.text_input("三態變化")
                f_coll = st.text_input("慣用搭配")
            f_en_def = st.text_area("英文定義")
            f_ex = st.text_area("例句")
            
            if st.form_submit_button("🚀 錄入矩陣"):
                if f_word.strip() and f_mean.strip():
                    # 查重
                    dup = next((w for w in raw_data if w['word'].lower() == f_word.strip().lower()), None)
                    if dup:
                        st.session_state.duplicate_word = f_word.strip()
                        st.rerun()
                    else:
                        payload = {
                            "word": f_word.strip(), "meaning_zh": f_mean, "pos": ", ".join(f_pos),
                            "category": f_cat, "other_forms": f_forms, "meaning_en": f_en_def, 
                            "example": f_ex, "collocations": f_coll, "mastery": 1, 
                            "next_review": get_next_review_date(1)
                        }
                        # --- 偵錯模式傳送 ---
                        resp = httpx.post(f"{URL}/rest/v1/vocabulary", json=payload, headers=HEADERS)
                        if resp.status_code < 300:
                            st.success(f"✅ {f_word} 已成功錄入！")
                            st.rerun()
                        else:
                            st.error(f"❌ 儲存失敗！代碼：{resp.status_code}")
                            st.json(resp.json()) # 如果失敗，這行會顯示原因
                else: st.warning("⚠️ 單字與中文不能空白")

    # 突擊測驗區 (Duplicate Quiz)
    if st.session_state.duplicate_word:
        dw = st.session_state.duplicate_word
        st.warning(f"⚠️ 「{dw}」已在矩陣中")
        if st.button(f"⚔️ 挑戰突擊測驗"):
            st.session_state.force_quiz_word, st.session_state.duplicate_word = dw, None
            st.rerun()

    if st.session_state.force_quiz_word:
        t_quiz = next((w for w in raw_data if w['word'].lower() == st.session_state.force_quiz_word.lower()), None)
        if t_quiz:
            ans = st.text_input(f"🔥 請拼寫「{t_quiz['meaning_zh']}」的英文：")
            if st.button("提交"):
                if ans.strip().lower() == t_quiz['word'].lower():
                    st.session_state.show_balloons = True
                    st.session_state.force_quiz_word = None
                    st.rerun()
                else: st.error("再試一次！")

    # 表格顯示區 (優化顯示)
    if raw_data:
        st.divider()
        df = pd.DataFrame(raw_data)
        # 僅選取核心欄位顯示
        display_map = {'word':'單字','meaning_zh':'中文','category':'類別','mastery':'等級'}
        # 防呆：確保欄位存在才顯示
        actual_cols = [c for c in display_map.keys() if c in df.columns]
        df_final = df[actual_cols].rename(columns=display_map)
        df_final.index = range(1, len(df_final) + 1)
        
        t1, t2 = st.tabs(["🌱 學習中", "🏆 已精通"])
        with t1: st.dataframe(df_final[df_final['等級'] < 4], use_container_width=True)
        with t2: st.dataframe(df_final[df_final['等級'] >= 4], use_container_width=True)

elif choice == "🎯 訓練模式":
    st.title("🎯 深度訓練")
    raw_data = load_data()
    today = str(date.today())
    due_list = [w for w in raw_data if not w.get('next_review') or str(w.get('next_review'))[:10] <= today]

    if due_list:
        if not st.session_state.quiz_state['word']:
            q = random.choice(due_list)
            st.session_state.quiz_state.update({'word': q['word'], 'attempts': 0})
            types = ["中文提示"]
            if q.get('example') and q['word'].lower() in q.get('example','').lower(): types.append("例句填空")
            st.session_state.quiz_state['q_type'] = random.choice(types)

        target = next((w for w in due_list if w['word'] == st.session_state.quiz_state['word']), None)
        if target:
            st.write(f"### 等級：L{target['mastery']} | 題型：{st.session_state.quiz_state['q_type']}")
            if st.session_state.quiz_state['q_type'] == "例句填空":
                st.info(f"📝 {re.sub(re.escape(target['word']), '_______', target['example'], flags=re.I)}")
            else:
                st.info(f"💡 中文：{target['meaning_zh']}")

            ans = st.text_input("輸入英文：", key="quiz_input")
            if st.button("檢查答案"):
                if ans.strip().lower() == target['word'].lower():
                    st.session_state.show_balloons = True
                    new_mas = min(5, target['mastery'] + 1)
                    httpx.patch(f"{URL}/rest/v1/vocabulary?id=eq.{target['id']}", json={"mastery": new_mas, "next_review": get_next_review_date(new_mas)}, headers=HEADERS)
                    st.session_state.quiz_state['word'] = None
                    st.rerun()
                else:
                    st.session_state.quiz_state['attempts'] += 1
                    if st.session_state.quiz_state['attempts'] >= 3:
                        httpx.patch(f"{URL}/rest/v1/vocabulary?id=eq.{target['id']}", json={"mastery": 0, "next_review": today}, headers=HEADERS)
                        st.error(f"💀 失敗！答案是 {target['word']}")
                        st.session_state.quiz_state['word'] = None
                    else: st.warning(f"❌ 提示：開頭是 {target['word'][0]}")

    else: st.success("🎉 今日複習完成！")

elif choice == "📅 遺忘排程":
    st.title("📅 遺忘排程")
    raw_data = load_data()
    if raw_data:
        df = pd.DataFrame(raw_data)
        df['next_review'] = pd.to_datetime(df['next_review']).dt.date
        today = date.today()
        due_t = df[df['next_review'] <= today].copy()
        due_f = df[df['next_review'] > today].sort_values('next_review').copy()
        
        c1, c2 = st.columns(2)
        with c1:
            st.error(f"🔥 今日待辦 ({len(due_t)})")
            if not due_t.empty: st.dataframe(due_t[['word', 'meaning_zh', 'mastery']], use_container_width=True)
        with c2:
            st.info(f"📅 未來排程 ({len(due_f)})")
            if not due_f.empty: st.dataframe(due_f[['next_review', 'word', 'mastery']], use_container_width=True)