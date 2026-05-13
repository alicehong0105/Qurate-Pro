import streamlit as st
import httpx
import pandas as pd
from datetime import date, timedelta, datetime
import random
import plotly.graph_objects as go

# ============================================================
# 1. 頁面設定
# ============================================================
st.set_page_config(page_title="Qurate Pro", page_icon="⚡", layout="wide")

st.markdown("""
    <style>
        [data-testid="stHeader"] { background: rgba(0,0,0,0); height: 3rem !important; }
        .block-container { padding-top: 0rem !important; padding-bottom: 0rem !important; }
        footer { visibility: hidden; }
        .main-title { color: #2d3436; font-weight: 800; font-size: 2.2rem; margin-bottom: 1rem; }
        .stButton > button { width: 100%; border-radius: 12px; height: 3.2rem; background: #2d3436; color: white; font-weight: bold; border: none; }
        .stTabs [data-baseweb="tab-list"] { gap: 10px; }
        .stTabs [aria-selected="true"] { background-color: #2d3436 !important; color: white !important; border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)


# ============================================================
# 2. API 設定 & 工具函式
# ============================================================
URL = st.secrets["connections"]["supabase"]["url"]
KEY = st.secrets["connections"]["supabase"]["key"]
HEADERS = {
    "apikey": KEY,
    "Authorization": f"Bearer {KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

def get_ebbinghaus_date(mastery):
    curve = {0: 0, 1: 1, 2: 3, 3: 7, 4: 14, 5: 30}
    days = curve.get(mastery, 1)
    return (date.today() + timedelta(days=days)).strftime('%Y-%m-%d')

def empty_to_none(v):
    return v if v and v.strip() else None

def parse_other_forms(raw):
    """統一將 other_forms 轉為 [v1, v2, v3]，相容字串與陣列格式。"""
    if isinstance(raw, list):
        parts = raw
    elif isinstance(raw, str) and raw:
        parts = [p.strip() for p in raw.replace('{', '').replace('}', '').split('/')]
    else:
        parts = []
    while len(parts) < 3:
        parts.append("")
    return parts[:3]

def load_data():
    try:
        resp = httpx.get(f"{URL}/rest/v1/vocabulary?select=*&order=next_review.asc", headers=HEADERS)
        return resp.json()
    except Exception:
        return []


# ============================================================
# 3. 資料初始化
# ============================================================
raw_data = load_data()
df = pd.DataFrame(raw_data) if raw_data else pd.DataFrame()
due_count = (
    len(df[pd.to_datetime(df['next_review']).dt.date <= date.today()])
    if not df.empty else 0
)


# ============================================================
# 4. 側邊導航
# ============================================================
st.sidebar.markdown("<h2 style='color: #2d3436;'>⚡ Qurate Pro</h2>", unsafe_allow_html=True)

pulse_label = f"🎯 Flash Pulse {'🔴' if due_count > 0 else ''}"
choice = st.sidebar.radio(
    "SYSTEM ACCESS",
    ["📋 Matrix Core", "🎴 Matrix Cards", pulse_label, "📅 Ebbing Log"]
)

if st.sidebar.button("🔄 Force Sync Matrix"):
    st.rerun()


# ============================================================
# 5. 頁面：Matrix Core
# ============================================================
if "Matrix Core" in choice:
    st.markdown("<div class='main-title'>Matrix Core</div>", unsafe_allow_html=True)
    t_add, t_view, t_edit = st.tabs(["➕ Initialize Node", "🔍 View Matrix", "📝 Modify Protocol"])

    # --- [A] 新增單字 ---
    with t_add:
        with st.form("add_matrix_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            f_word = c1.text_input("Entry（單字）*")
            f_mean = c2.text_input("Definition（中文）*")

            st.write("---")
            st.caption("Morphology（動詞三態變化）")
            v1, v2, v3 = st.columns(3)
            f_v1 = v1.text_input("V1 (Base)")
            f_v2 = v2.text_input("V2 (Past)")
            f_v3 = v3.text_input("V3 (Participle)")

            st.write("---")
            f_pos = st.multiselect("Class（詞性）", ["n.", "v.", "adj.", "adv.", "phr.", "prep."])

            c3, c4 = st.columns(2)
            f_syn  = c3.text_input("Synonyms（同義詞）")
            f_coll = c4.text_input("Collocations（慣用搭配）")

            f_en = st.text_area("English Definition（英文定義）")
            f_ex = st.text_area("Context Example（例句）")

            if st.form_submit_button("🚀 SYNC TO CORE"):
                if f_word.strip() and f_mean.strip():
                    payload = {
                        "word":        f_word.strip(),
                        "meaning_zh":  f_mean.strip(),
                        "pos":         f_pos if f_pos else [],
                        "other_forms": [f_v1, f_v2, f_v3] if f_v1 else [],
                        "synonyms":    empty_to_none(f_syn),
                        "collocations":empty_to_none(f_coll),
                        "meaning_en":  empty_to_none(f_en),
                        "example":     empty_to_none(f_ex),
                        "mastery":     1,
                        "next_review": get_ebbinghaus_date(1)
                    }
                    resp = httpx.post(f"{URL}/rest/v1/vocabulary", json=payload, headers=HEADERS)
                    if resp.status_code < 300:
                        st.success("🎉 新增成功！正在更新矩陣...")
                        st.rerun()
                    else:
                        st.error(f"同步失敗：{resp.text}")
                else:
                    st.warning("請填寫單字與中文定義。")

    # --- [B] 檢視單字庫 ---
    with t_view:
        if not df.empty:
            v_f = st.radio("Group Filter", ["Due Today", "All Nodes", "L5 Mastered"], horizontal=True)
            d_df = df.copy()

            if v_f == "Due Today":
                d_df = d_df[pd.to_datetime(d_df['next_review']).dt.date <= date.today()]
            elif v_f == "L5 Mastered":
                d_df = d_df[d_df['mastery'] >= 5]

            st.dataframe(
                d_df[['word', 'meaning_zh', 'pos', 'mastery', 'next_review', 'other_forms']],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Matrix is currently empty.")

    # --- [C] 修改單字 ---
    with t_edit:
        if not df.empty:
            target_word = st.selectbox("Select Target Node", options=df['word'].tolist())
            row = df[df['word'] == target_word].iloc[0]
            v_parts = parse_other_forms(row.get('other_forms'))

            st.link_button(
                f"🔊 Cambridge Pronunciation: {target_word}",
                f"https://dictionary.cambridge.org/dictionary/english-chinese-traditional/{target_word.replace(' ', '-')}"
            )

            with st.form("edit_matrix_form"):
                e1, e2 = st.columns(2)
                u_word = e1.text_input("Entry（單字）*", value=row['word'])
                u_mean = e2.text_input("Definition（中文）*", value=row['meaning_zh'])

                dt_cur = datetime.strptime(str(row['next_review'])[:10], '%Y-%m-%d').date()
                u_date = st.date_input("Manual Schedule（複習日期）", value=dt_cur)

                st.write("---")
                st.caption("Morphology（動詞三態變化）")
                ev1, ev2, ev3 = st.columns(3)
                u_v1 = ev1.text_input("V1 (Base)",        value=v_parts[0])
                u_v2 = ev2.text_input("V2 (Past)",        value=v_parts[1])
                u_v3 = ev3.text_input("V3 (Participle)",  value=v_parts[2])

                st.write("---")
                pos_options = ["n.", "v.", "adj.", "adv.", "phr.", "prep."]
                db_pos = row.get('pos', [])
                if isinstance(db_pos, str):
                    current_pos = [p.strip() for p in db_pos.strip('{}').split(',') if p in pos_options]
                elif isinstance(db_pos, list):
                    current_pos = [p for p in db_pos if p in pos_options]
                else:
                    current_pos = []

                u_pos  = st.multiselect("Class（詞性）", pos_options, default=current_pos)

                ec3, ec4 = st.columns(2)
                u_syn  = ec3.text_input("Synonyms（同義詞）",      value=row.get('synonyms', '') or '')
                u_coll = ec4.text_input("Collocations（慣用搭配）", value=row.get('collocations', '') or '')

                u_en = st.text_area("English Definition", value=row.get('meaning_en', '') or '')
                u_ex = st.text_area("Context Example",   value=row.get('example', '') or '')

                if st.form_submit_button("✅ UPDATE MATRIX"):
                    upd_payload = {
                        "word":         u_word,
                        "meaning_zh":   u_mean,
                        "pos":          u_pos if u_pos else [],
                        "next_review":  u_date.strftime('%Y-%m-%d'),
                        "other_forms":  [u_v1, u_v2, u_v3] if u_v1 else [],
                        "synonyms":     empty_to_none(u_syn),
                        "collocations": empty_to_none(u_coll),
                        "meaning_en":   empty_to_none(u_en),
                        "example":      empty_to_none(u_ex)
                    }
                    resp = httpx.patch(
                        f"{URL}/rest/v1/vocabulary?id=eq.{row['id']}",
                        json=upd_payload,
                        headers=HEADERS
                    )
                    if resp.status_code < 300:
                        st.success("Node Synchronized!")
                        st.rerun()
                    else:
                        st.error(f"Update Failed: {resp.text}")
        else:
            st.info("Matrix is currently empty.")


# ============================================================
# 6. 頁面：Matrix Cards（單字翻卡預習 — 自訂正反面模式）
# ============================================================
elif "Matrix Cards" in choice:
    st.markdown("<div class='main-title'>Matrix Cards</div>", unsafe_allow_html=True)

    # ── 欄位選項定義 ──────────────────────────────────────────
    FIELD_OPTIONS = {
        "🔤 英文單字":   "word",
        "🇹🇼 中文定義":  "meaning_zh",
        "📖 英文定義":   "meaning_en",
        "📝 例句填空":   "example_blank",   # 特殊：將例句中的單字挖空
        "📝 完整例句":   "example",
        "💡 詞性":       "pos",
        "📚 三態變化":   "other_forms",
        "🔗 同義詞":     "synonyms",
        "🎯 慣用搭配":   "collocations",
    }
    FIELD_LABELS = list(FIELD_OPTIONS.keys())

    # ── 卡片模式設定面板 ──────────────────────────────────────
    with st.expander("⚙️ 自訂卡片模式", expanded=("card_front_fields" not in st.session_state)):
        st.caption("選擇今天正面要顯示什麼、反面要顯示什麼（可多選）")

        cfg1, cfg2 = st.columns(2)
        with cfg1:
            st.markdown("**正面（提示）**")
            front_choices = st.multiselect(
                "正面顯示欄位",
                FIELD_LABELS,
                default=st.session_state.get("card_front_fields", ["🇹🇼 中文定義"]),
                key="front_select",
                label_visibility="collapsed"
            )
        with cfg2:
            st.markdown("**反面（答案）**")
            back_choices = st.multiselect(
                "反面顯示欄位",
                FIELD_LABELS,
                default=st.session_state.get("card_back_fields", ["🔤 英文單字", "📖 英文定義", "📝 完整例句"]),
                key="back_select",
                label_visibility="collapsed"
            )

        col_scope, col_confirm = st.columns([2, 1])
        with col_scope:
            card_scope = st.radio(
                "複習範圍",
                ["📅 今日到期", "📦 全部單字"],
                horizontal=True,
                index=0 if st.session_state.get("card_scope", "due") == "due" else 1
            )
        with col_confirm:
            st.write("")
            if st.button("✅ 套用設定", use_container_width=True):
                st.session_state.card_front_fields = front_choices
                st.session_state.card_back_fields  = back_choices
                st.session_state.card_scope        = "due" if "今日" in card_scope else "all"
                st.session_state.card_index        = 0
                st.session_state.is_flipped        = False
                st.rerun()

    # 套用預設值（第一次進入）
    if "card_front_fields" not in st.session_state:
        st.session_state.card_front_fields = ["🇹🇼 中文定義"]
    if "card_back_fields" not in st.session_state:
        st.session_state.card_back_fields  = ["🔤 英文單字", "📖 英文定義", "📝 完整例句"]
    if "card_scope" not in st.session_state:
        st.session_state.card_scope = "due"

    # ── 篩選卡片池 ────────────────────────────────────────────
    if st.session_state.card_scope == "due":
        due_cards = [w for w in raw_data if str(w.get('next_review'))[:10] <= str(date.today())]
    else:
        due_cards = list(raw_data)

    # ── 渲染欄位的輔助函式 ────────────────────────────────────
    def render_fields(card, field_labels, is_front=False):
        """依照選擇的欄位清單渲染卡片內容。"""
        for label in field_labels:
            field_key = FIELD_OPTIONS.get(label)
            if not field_key:
                continue

            if field_key == "word":
                st.markdown(
                    f"<h1 style='text-align:center; font-size:3.5rem; margin:0.5rem 0;'>{card['word']}</h1>",
                    unsafe_allow_html=True
                )
                st.link_button(
                    "🔊 Cambridge Pronunciation",
                    f"https://dictionary.cambridge.org/dictionary/english-chinese-traditional/{card['word'].replace(' ', '-')}"
                )

            elif field_key == "meaning_zh":
                val = card.get("meaning_zh", "")
                if val:
                    st.markdown(
                        f"<h3 style='text-align:center; color:#2d3436;'>{val}</h3>",
                        unsafe_allow_html=True
                    )

            elif field_key == "meaning_en":
                val = card.get("meaning_en", "")
                st.markdown(f"**📖 英文定義：** {val or '—'}")

            elif field_key == "example_blank":
                ex = card.get("example", "")
                word = card.get("word", "")
                if ex and word:
                    # 不分大小寫挖空
                    import re
                    blanked = re.sub(re.escape(word), "**____**", ex, flags=re.IGNORECASE)
                    st.markdown(f"**📝 例句填空：**")
                    st.markdown(f"> {blanked}")
                else:
                    st.markdown("**📝 例句填空：** —")

            elif field_key == "example":
                val = card.get("example", "")
                st.markdown(f"**📝 完整例句：**")
                st.markdown(f"> {val or '—'}")

            elif field_key == "pos":
                pos = card.get("pos", [])
                pos_str = ", ".join(pos) if isinstance(pos, list) else str(pos)
                st.markdown(f"**💡 詞性：** {pos_str or '—'}")

            elif field_key == "other_forms":
                forms = parse_other_forms(card.get("other_forms"))
                forms_str = " / ".join(f for f in forms if f) or "—"
                st.markdown(f"**📚 三態變化：** {forms_str}")

            elif field_key == "synonyms":
                val = card.get("synonyms", "")
                st.markdown(f"**🔗 同義詞：** {val or '—'}")

            elif field_key == "collocations":
                val = card.get("collocations", "")
                st.markdown(f"**🎯 慣用搭配：** {val or '—'}")

    # ── 卡片主體 ──────────────────────────────────────────────
    if due_cards:
        if 'card_index' not in st.session_state:
            st.session_state.card_index = 0
        if 'is_flipped' not in st.session_state:
            st.session_state.is_flipped = False

        if st.session_state.card_index >= len(due_cards):
            st.session_state.card_index = 0

        current_card = due_cards[st.session_state.card_index]

        # 進度 & 模式摘要
        scope_label = "今日到期" if st.session_state.card_scope == "due" else "全部單字"
        front_summary = " + ".join(st.session_state.card_front_fields)
        back_summary  = " + ".join(st.session_state.card_back_fields)
        st.caption(f"📦 {scope_label}｜正面：{front_summary}｜反面：{back_summary}")
        st.progress((st.session_state.card_index + 1) / len(due_cards),
                    text=f"{st.session_state.card_index + 1} / {len(due_cards)}")

        # 卡片外框
        with st.container(border=True):
            if not st.session_state.is_flipped:
                render_fields(current_card, st.session_state.card_front_fields, is_front=True)
            else:
                st.markdown("---")
                render_fields(current_card, st.session_state.card_back_fields, is_front=False)

        # 控制按鈕
        st.write("")
        b1, b2, b3 = st.columns([1, 2, 1])

        with b1:
            if st.button("⬅️ 上一字"):
                if st.session_state.card_index > 0:
                    st.session_state.card_index -= 1
                    st.session_state.is_flipped = False
                    st.rerun()

        with b2:
            flip_label = "🔄 翻到反面" if not st.session_state.is_flipped else "🔄 翻回正面"
            if st.button(flip_label):
                st.session_state.is_flipped = not st.session_state.is_flipped
                st.rerun()

        with b3:
            if st.button("下一字 ➡️"):
                if st.session_state.card_index < len(due_cards) - 1:
                    st.session_state.card_index += 1
                    st.session_state.is_flipped = False
                    st.rerun()

        # 全部看完提示
        if st.session_state.card_index == len(due_cards) - 1 and st.session_state.is_flipped:
            st.success("🎉 這輪預習看完了！立刻去左側進入『Flash Pulse』進行打字複習測驗吧！")

    else:
        st.success("✨ 目前沒有待複習的單字卡，矩陣狀態安全！")


# ============================================================
# 7. 頁面：Flash Pulse（打字測驗）
# ============================================================
elif "Flash Pulse" in choice:
    st.markdown("<div class='main-title'>Flash Pulse</div>", unsafe_allow_html=True)

    due = [w for w in raw_data if str(w.get('next_review'))[:10] <= str(date.today())]

    if due:
        q = random.choice(due)
        st.info(f"💡 Cue: {q['meaning_zh']}")
        if q.get('example'):
            st.caption(f"Context: {q['example'].replace(q['word'], '____')}")

        ans = st.text_input("Type the correct Entry（不分大小寫）:")
        if st.button("EXECUTE VERIFICATION"):
            if ans.strip().lower() == q['word'].lower():
                st.success("Correct! Matrix Evolved.")
                st.balloons()
                new_m = min(5, q['mastery'] + 1)
                httpx.patch(
                    f"{URL}/rest/v1/vocabulary?id=eq.{q['id']}",
                    json={"mastery": new_m, "next_review": get_ebbinghaus_date(new_m)},
                    headers=HEADERS
                )
                st.rerun()
            else:
                st.error("Verification Failed. Try again.")
    else:
        st.success("Matrix Stable. No nodes due for review.")


# ============================================================
# 8. 頁面：Ebbing Log（複習預測圖表）
# ============================================================
elif "Ebbing Log" in choice:
    st.markdown("<div class='main-title'>Ebbing Log</div>", unsafe_allow_html=True)

    if not df.empty:
        v_d = st.select_slider(
            "Forecast Horizon (Days)",
            options=[7, 14, 30, 90, 180, 365],
            value=30
        )
        df['date'] = pd.to_datetime(df['next_review']).dt.date

        dates  = [date.today() + timedelta(days=i) for i in range(v_d + 1)]
        counts = [len(df[df['date'] <= d]) for d in dates]

        fig = go.Figure(go.Scatter(
            x=dates, y=counts,
            mode='lines+markers',
            line=dict(color='#2d3436', width=3),
            marker=dict(size=8, color='#ff7675'),
            name="Cumulative Due"
        ))
        fig.update_layout(
            plot_bgcolor='white',
            hovermode='x unified',
            margin=dict(l=0, r=0, t=20, b=0),
            height=450,
            xaxis=dict(showgrid=True, gridcolor='#f0f0f0', title="Review Date"),
            yaxis=dict(showgrid=True, gridcolor='#f0f0f0', title="Total Words Due")
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Insufficient data for log prediction.")