import streamlit as st
import httpx
import pandas as pd
from datetime import date, timedelta
import random
import re

# --- 1. 基本設定 ---
st.set_page_config(page_title="LexiMatrix Pro", page_icon="🛡️", layout="wide")

# --- 2. 初始化全域狀態 ---
for key in ['quiz_state', 'show_balloons', 'duplicate_word', 'force_quiz_word']:
    if key not in st.session_state:
        st.session_state[key] = {'word': None, 'q_type': None, 'attempts': 0} if 'quiz' in key else False

if st.session_state.get('show_balloons'):
    st.balloons()
    st.session_state.show_balloons = False

# --- 3. Supabase 配置 ---
URL = st.secrets["connections"]["supabase"]["url"]
KEY = st.secrets["connections"]["supabase"]["key"]
HEADERS = {"apikey": KEY, "Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}

# --- 4. 工具函式 ---
def get_next_review_date(level):
    intervals = {0: 0, 1: 1, 2: 3, 3: 7, 4: 14, 5: 30}
    return str(date.today() + timedelta(days=intervals.get(level, 0)))

def load_data():
    try:
        resp = httpx.get(f"{URL}/rest/v1/vocabulary?select=*&order=id.desc", headers=HEADERS)
        return resp.json()
    except: return []

# --- 5. 側邊欄 ---
with st.sidebar:
    st.title("🛡️ LexiMatrix")
    choice = st.radio("功能選單", ["📋 管理矩陣", "🎯 訓練模式", "📅 遺忘排程"])
    st.divider()
    if st.button("♻️ 強制重新整理"): st.rerun()

# --- 6. 頁面功能 ---

if choice == "📋 管理矩陣":
    st.title("📋 矩陣資料庫管理")
    raw_data = load_data()
    
    # A. 新增區
    with st.expander("➕ 新增單字"):
        with st.form("add_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                f_word = st.text_input("英文單字*")
                f_pos = st.multiselect("詞性", ["n.", "v.", "adj.", "adv.", "phr.", "Term."])
                f_cat = st.text_input("類別", value="未分類")
            with c2:
                f_mean = st.text_input("中文翻譯*")
                f_forms = st.text_input("三態/變化 (other_forms)")
                f_coll = st.text_input("慣用搭配 (collocations)")
            f_en_def = st.text_area("英文定義 (meaning_en)")
            f_ex = st.text_area("例句 (example)")
            
            if st.form_submit_button("🚀 錄入矩陣"):
                if f_word.strip() and f_mean.strip():
                    payload = {
                        "word": f_word.strip(), "meaning_zh": f_mean, "pos": ", ".join(f_pos),
                        "category": f_cat, "other_forms": f_forms, "collocations": f_coll,
                        "meaning_en": f_en_def, "example": f_ex, "mastery": 1, 
                        "next_review": get_next_review_date(1)
                    }
                    resp = httpx.post(f"{URL}/rest/v1/vocabulary", json=payload, headers=HEADERS)
                    if resp.status_code < 300:
                        st.success(f"✅ {f_word} 已成功錄入矩陣！")
                        st.rerun()
                    else: st.error(f"❌ 錯誤：{resp.json().get('message')}")

    # B. 工具列與表格
    if raw_data:
        st.divider()
        df = pd.DataFrame(raw_data)
        
        # 1. 搜尋功能
        search_q = st.text_input("🔍 搜尋關鍵字 (單字或中文)：", "")
        if search_q:
            df = df[df['word'].str.contains(search_q, case=False, na=False) | 
                    df['meaning_zh'].str.contains(search_q, case=False, na=False)]

        # 2. 顯示模式與下載
        tool_c1, tool_c2 = st.columns([3, 1])
        with tool_c1:
            view_mode = st.radio("顯示模式", ["分區檢視 (L0-5)", "完整矩陣 (全顯示)"], horizontal=True)
        with tool_c2:
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 下載備份 (CSV)", data=csv, file_name=f"lexi_backup_{date.today()}.csv", mime='text/csv')

        # 3. 欄位映射
        cols_map = {
            'word':'單字', 'meaning_zh':'中文', 'category':'類別', 
            'mastery':'等級', 'pos':'詞性', 'other_forms':'變化', 'example':'例句'
        }
        actual_cols = [c for c in cols_map.keys() if c in df.columns]
        df_show = df[actual_cols].rename(columns=cols_map)
        df_show.index = range(1, len(df_show) + 1)

        # 4. 呈現表格
        if view_mode == "分區檢視 (L0-5)":
            t1, t2, t3 = st.tabs(["🌱 L0-L1", "🏃 L2-L3", "👑 L4-L5"])
            with t1: st.dataframe(df_show[df_show['等級'] <= 1], use_container_width=True)
            with t2: st.dataframe(df_show[(df_show['等級'] >= 2) & (df_show['等級'] <= 3)], use_container_width=True)
            with t3: st.dataframe(df_show[df_show['等級'] >= 4], use_container_width=True)
        else:
            st.dataframe(df_show, use_container_width=True)

elif choice == "🎯 訓練模式":
    st.title("🎯 深度訓練模式")
    raw_data = load_data()
    today = str(date.today())
    due_list = [w for w in raw_data if not w.get('next_review') or str(w.get('next_review'))[:10] <= today]

    if due_list:
        if not st.session_state.quiz_state['word']:
            q = random.choice(due_list)
            st.session_state.quiz_state.update({'word': q['word'], 'attempts': 0})
            opts = ["中文提示"]
            if q.get('example') and q['word'].lower() in q.get('example','').lower(): opts.append("例句填空")
            st.session_state.quiz_state['q_type'] = random.choice(opts)

        target = next((w for w in due_list if w['word'] == st.session_state.quiz_state['word']), None)
        if target:
            st.write(f"### 等級：Level {target['mastery']}")
            if st.session_state.quiz_state['q_type'] == "例句填空":
                st.info(f"📝 {re.sub(re.escape(target['word']), '_______', target['example'], flags=re.I)}")
            else:
                st.info(f"💡 中文：{target['meaning_zh']}")

            ans = st.text_input("請拼寫單字：")
            if st.button("送出"):
                if ans.strip().lower() == target['word'].lower():
                    st.session_state.show_balloons = True
                    new_mas = min(5, target['mastery'] + 1)
                    httpx.patch(f"{URL}/rest/v1/vocabulary?id=eq.{target['id']}", 
                                json={"mastery": new_mas, "next_review": get_next_review_date(new_mas)}, 
                                headers=HEADERS)
                    st.session_state.quiz_state['word'] = None
                    st.rerun()
                else: st.error("拼寫錯誤，再試一次！")
    else: st.success("🎉 今日複習已全數完成！大腦該休息囉。")

elif choice == "📅 遺忘排程":
    st.title("📅 遺忘排程追蹤")
    raw_data = load_data()
    if raw_data:
        df = pd.DataFrame(raw_data)
        df['nr_date'] = pd.to_datetime(df['next_review']).dt.date
        today = date.today()
        
        c1, c2 = st.columns(2)
        with c1:
            st.error(f"🔥 今日待辦 ({len(df[df['nr_date'] <= today])})")
            st.dataframe(df[df['nr_date'] <= today][['word', 'meaning_zh', 'mastery']].rename(columns={'word':'單字','meaning_zh':'中文','mastery':'等級'}), use_container_width=True)
        with c2:
            st.info("📅 未來複習預告")
            future = df[df['nr_date'] > today].sort_values('nr_date')
            st.dataframe(future[['nr_date', 'word']].rename(columns={'nr_date':'日期','word':'單字'}), use_container_width=True)