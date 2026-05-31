import streamlit as st
import httpx
import pandas as pd
from datetime import date, timedelta, datetime
import random
import plotly.graph_objects as go
import re
import base64

# ============================================================
# 1. 頁面設定
# ============================================================
st.set_page_config(page_title="Qurate Pro", page_icon="⚡", layout="wide")

st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;800&display=swap');

        [data-testid="stHeader"] { background: rgba(0,0,0,0); height: 3rem !important; }
        .block-container { padding-top: 1rem !important; padding-bottom: 0rem !important; }
        footer { visibility: hidden; }

        .main-title {
            font-family: 'JetBrains Mono', monospace !important;
            color: #00cec9; font-weight: 800; font-size: 2rem;
            margin-bottom: 1rem; letter-spacing: -1px;
            text-shadow: 0 0 30px rgba(0,206,201,0.3);
        }
        .stButton > button {
            width: 100%; border-radius: 8px; height: 3.2rem;
            background: linear-gradient(135deg, #00cec9, #0984e3) !important;
            color: #ffffff !important; font-weight: 700; border: none;
            font-family: 'JetBrains Mono', monospace; transition: all 0.2s ease;
            box-shadow: 0 0 20px rgba(0,206,201,0.2);
        }
        .stButton > button:hover { box-shadow: 0 0 30px rgba(0,206,201,0.5); transform: translateY(-1px); }
        .stTabs [data-baseweb="tab-list"] { gap: 8px; border-radius: 10px; padding: 4px; }
        .stTabs [data-baseweb="tab"] { border-radius: 8px; font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; }
        .stTabs [aria-selected="true"] { background: linear-gradient(135deg, #00cec9, #0984e3) !important; color: #ffffff !important; border-radius: 8px; font-weight: 700; }
        [data-testid="stVerticalBlockBorderWrapper"] {
            border: 1px solid rgba(0,206,201,0.2) !important;
            border-radius: 12px !important; box-shadow: 0 0 20px rgba(0,206,201,0.05);
        }
        [data-testid="stTextInput"] input:focus,
        [data-testid="stTextArea"] textarea:focus {
            border-color: #00cec9 !important; box-shadow: 0 0 0 3px rgba(0,206,201,0.15) !important;
        }
        .hint-badge {
            background: linear-gradient(135deg, rgba(0,206,201,0.1), rgba(9,132,227,0.1));
            color: #00cec9; border: 1px solid #00cec9; border-radius: 8px;
            padding: 0.5rem 1rem; font-weight: 700; margin: 0.5rem 0;
            font-family: 'JetBrains Mono', monospace;
        }
        .cat-badge {
            display: inline-block; background: rgba(0,206,201,0.1); color: #00cec9;
            border: 1px solid rgba(0,206,201,0.3); border-radius: 20px;
            padding: 0.2rem 0.8rem; font-size: 0.78rem; font-weight: 600;
            margin-bottom: 0.5rem; font-family: 'JetBrains Mono', monospace;
        }
        .tutorial-card {
            background: linear-gradient(135deg, #161b22 0%, #0d1117 100%);
            border: 1px solid #00cec9; border-radius: 16px; padding: 2.5rem;
            color: #e6edf3; text-align: center; margin: 1rem 0;
            box-shadow: 0 0 40px rgba(0,206,201,0.15);
        }
        [data-testid="stProgressBar"] > div > div {
            background: linear-gradient(90deg, #00cec9, #0984e3) !important;
        }
        .wrong-card {
            background: rgba(214,48,49,0.08);
            border: 1px solid rgba(214,48,49,0.4);
            border-radius: 12px; padding: 0.6rem 1rem; margin-bottom: 0.5rem;
            font-size: 0.92rem;
        }
        .match-btn-left {
            background: rgba(0,206,201,0.1) !important;
            border: 1px solid rgba(0,206,201,0.4) !important;
            color: #00cec9 !important;
            font-family: 'JetBrains Mono', monospace !important;
        }
        .match-btn-right {
            background: rgba(9,132,227,0.1) !important;
            border: 1px solid rgba(9,132,227,0.4) !important;
            color: #74b9ff !important;
            font-family: 'JetBrains Mono', monospace !important;
        }
        .match-btn-selected {
            background: rgba(0,206,201,0.3) !important;
            border: 2px solid #00cec9 !important;
            box-shadow: 0 0 15px rgba(0,206,201,0.5) !important;
        }
        .match-btn-matched {
            background: rgba(85,239,196,0.15) !important;
            border: 1px solid #55efc4 !important;
            color: #55efc4 !important;
            opacity: 0.6;
        }
        .match-btn-wrong {
            background: rgba(214,48,49,0.2) !important;
            border: 2px solid #d63031 !important;
            animation: shake 0.3s ease;
        }
        @keyframes shake {
            0%,100% { transform: translateX(0); }
            25% { transform: translateX(-5px); }
            75% { transform: translateX(5px); }
        }
        .ai-bubble {
            background: linear-gradient(135deg, rgba(0,206,201,0.08), rgba(9,132,227,0.08));
            border: 1px solid rgba(0,206,201,0.3);
            border-radius: 16px; padding: 1rem 1.2rem;
            margin: 0.5rem 0; font-size: 0.95rem; line-height: 1.6;
            color: #e6edf3;
        }
    </style>
""",
    unsafe_allow_html=True,
)

# ============================================================
# 2. API 設定
# ============================================================
URL = st.secrets["connections"]["supabase"]["url"]
KEY = st.secrets["connections"]["supabase"]["key"]
try:
    ANTHROPIC_API_KEY = st.secrets["anthropic"]["api_key"]
except (KeyError, Exception):
    ANTHROPIC_API_KEY = ""


def get_headers(access_token=None):
    token = access_token or KEY
    return {
        "apikey": KEY,
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


# ============================================================
# 3. Auth 函式
# ============================================================
def sign_up(email, password):
    resp = httpx.post(
        f"{URL}/auth/v1/signup",
        json={"email": email, "password": password},
        headers={"apikey": KEY, "Content-Type": "application/json"},
    )
    return resp.json()


def sign_in(email, password):
    resp = httpx.post(
        f"{URL}/auth/v1/token?grant_type=password",
        json={"email": email, "password": password},
        headers={"apikey": KEY, "Content-Type": "application/json"},
    )
    return resp.json()


def sign_out(access_token):
    httpx.post(
        f"{URL}/auth/v1/logout",
        headers={"apikey": KEY, "Authorization": f"Bearer {access_token}"},
    )


# ============================================================
# 4. 工具函式
# ============================================================
def get_ebbinghaus_date(mastery):
    curve = {0: 0, 1: 1, 2: 3, 3: 7, 4: 14, 5: 30}
    days = curve.get(mastery, 1)
    return (date.today() + timedelta(days=days)).strftime("%Y-%m-%d")


def empty_to_none(v):
    return v if v and v.strip() else None


def parse_other_forms(raw):
    if isinstance(raw, list):
        parts = raw
    elif isinstance(raw, str) and raw:
        parts = [p.strip() for p in raw.replace("{", "").replace("}", "").split("/")]
    else:
        parts = []
    while len(parts) < 3:
        parts.append("")
    return parts[:3]


def calculate_new_mastery(current_mastery, penalty=2):
    if current_mastery < 2:
        return 0
    return current_mastery - penalty


def load_data(access_token):
    try:
        resp = httpx.get(
            f"{URL}/rest/v1/vocabulary?select=*&order=next_review.asc",
            headers=get_headers(access_token),
        )
        return resp.json()
    except Exception:
        return []


def update_mastery_in_db(word_id, new_mastery, access_token):
    httpx.patch(
        f"{URL}/rest/v1/vocabulary?id=eq.{word_id}",
        json={"mastery": new_mastery, "next_review": get_ebbinghaus_date(new_mastery)},
        headers=get_headers(access_token),
    )


def get_all_categories(raw_data):
    cats = (
        sorted(set((row.get("category") or "預設") for row in raw_data))
        if raw_data
        else []
    )
    if "預設" not in cats:
        cats = ["預設"] + cats
    return cats


def play_pronunciation(word: str):
    try:
        from gtts import gTTS

        tts = gTTS(text=word, lang="en", tld="co.uk")
        tts.save("/tmp/pronunciation.mp3")
        with open("/tmp/pronunciation.mp3", "rb") as f:
            audio_bytes = f.read()
        audio_b64 = base64.b64encode(audio_bytes).decode()
        st.markdown(
            f"""
            <audio autoplay controls style="width:100%; margin-top:0.5rem;">
                <source src="data:audio/mp3;base64,{audio_b64}" type="audio/mp3">
            </audio>""",
            unsafe_allow_html=True,
        )
    except Exception:
        st.link_button(
            f"🔊 Cambridge: {word}",
            f"https://dictionary.cambridge.org/dictionary/english-chinese-traditional/{word.replace(' ', '-')}",
        )


def inject_sound(sound_type: str):
    import streamlit.components.v1 as components

    if sound_type == "success":
        freqs = [523, 659, 784, 1047]
        dur = 0.18
        osc_type = "sine"
    else:
        freqs = [523, 659, 784, 1047, 784, 1047, 1319, 1047, 1319, 1568]
        dur = 0.15
        osc_type = "triangle"

    notes_js = ", ".join(
        f"{{f:{f}, t:{round(i * dur, 3)}}}" for i, f in enumerate(freqs)
    )

    html_code = f"""<!DOCTYPE html>
<html><body>
<script>
(function() {{
    function playSound() {{
        try {{
            var AudioCtx = window.AudioContext || window.webkitAudioContext;
            if (!AudioCtx) return;
            var ctx = new AudioCtx();
            var resume = ctx.state === 'suspended' ? ctx.resume() : Promise.resolve();
            resume.then(function() {{
                var notes = [{notes_js}];
                notes.forEach(function(n) {{
                    var osc = ctx.createOscillator();
                    var gain = ctx.createGain();
                    osc.connect(gain);
                    gain.connect(ctx.destination);
                    osc.frequency.value = n.f;
                    osc.type = '{osc_type}';
                    var t = ctx.currentTime + n.t + 0.05;
                    gain.gain.setValueAtTime(0.4, t);
                    gain.gain.exponentialRampToValueAtTime(0.001, t + {dur + 0.08});
                    osc.start(t);
                    osc.stop(t + {dur + 0.12});
                }});
            }});
        }} catch(e) {{
            console.warn('Audio error:', e);
        }}
    }}
    playSound();
}})();
</script>
</body></html>"""
    components.html(html_code, height=0, scrolling=False)


# ============================================================
# Flash Pulse 專用：勝利號角 + 爆炸粒子特效
# ============================================================
def inject_congrats_sound():
    """播放 Congratulations 音效：上升琶音 + 長尾餘韻"""
    import streamlit.components.v1 as components

    html = """<!DOCTYPE html><html><body>
<script>
(function(){
  try {
    var AC = window.AudioContext || window.webkitAudioContext;
    var ctx = new AC();
    var go = ctx.state==='suspended' ? ctx.resume() : Promise.resolve();
    go.then(function(){
      // 主旋律：歡樂上升琶音
      var melody = [
        {f:523.25, t:0.00, d:0.18, vol:0.35},
        {f:659.25, t:0.16, d:0.18, vol:0.35},
        {f:783.99, t:0.32, d:0.18, vol:0.35},
        {f:1046.5, t:0.48, d:0.35, vol:0.40},
        {f:987.77, t:0.70, d:0.18, vol:0.30},
        {f:1046.5, t:0.88, d:0.55, vol:0.45},
      ];
      // 和聲層
      var harmony = [
        {f:261.63, t:0.00, d:0.55, vol:0.15},
        {f:329.63, t:0.00, d:0.55, vol:0.12},
        {f:523.25, t:0.48, d:0.85, vol:0.18},
      ];
      function playNote(n, type) {
        var osc = ctx.createOscillator();
        var gain = ctx.createGain();
        osc.connect(gain); gain.connect(ctx.destination);
        osc.type = type || 'sine';
        osc.frequency.value = n.f;
        var t = ctx.currentTime + n.t + 0.05;
        gain.gain.setValueAtTime(0, t);
        gain.gain.linearRampToValueAtTime(n.vol, t + 0.03);
        gain.gain.exponentialRampToValueAtTime(0.001, t + n.d + 0.12);
        osc.start(t); osc.stop(t + n.d + 0.18);
      }
      melody.forEach(function(n){ playNote(n, 'sine'); });
      harmony.forEach(function(n){ playNote(n, 'triangle'); });
    });
  } catch(e){ console.warn(e); }
})();
</script>
</body></html>"""
    components.html(html, height=1, scrolling=False)


def inject_victory_effect():
    import streamlit.components.v1 as components
    import random as _rnd

    _id = _rnd.randint(100000, 999999)

    html = f"""<!DOCTYPE html>
<html>
<head>
<style>
  html, body {{ margin:0; padding:0; background:transparent; overflow:hidden; }}
</style>
</head>
<body>
<script>
(function(){{
  /* 在父頁面建立 canvas 和閃光層 */
  var doc = window.parent.document;

  /* 閃光背景 */
  var flash = doc.createElement('div');
  flash.id = 'vic_flash_{_id}';
  flash.style.cssText = [
    'position:fixed','top:0','left:0','width:100vw','height:100vh',
    'pointer-events:none','z-index:8888',
    'background:radial-gradient(ellipse at center,rgba(0,206,201,0.4) 0%,rgba(9,132,227,0.2) 45%,transparent 70%)',
    'opacity:0','transition:opacity 0.15s'
  ].join(';');
  doc.body.appendChild(flash);
  setTimeout(function(){{ flash.style.opacity='1'; }}, 30);
  setTimeout(function(){{ flash.style.opacity='0.5'; }}, 300);
  setTimeout(function(){{ flash.style.opacity='0'; }}, 1800);
  setTimeout(function(){{ flash.remove(); }}, 2200);

  /* Canvas */
  var canvas = doc.createElement('canvas');
  canvas.id = 'vic_canvas_{_id}';
  canvas.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;pointer-events:none;z-index:9999;';
  doc.body.appendChild(canvas);
  canvas.width  = window.parent.innerWidth;
  canvas.height = window.parent.innerHeight;
  var W = canvas.width, H = canvas.height;
  var cx = canvas.getContext('2d');

  /* 音效：勝利號角 */
  try {{
    var AC = window.parent.AudioContext || window.parent.webkitAudioContext
          || window.AudioContext || window.webkitAudioContext;
    var actx = new AC();
    var go = actx.state==='suspended' ? actx.resume() : Promise.resolve();
    go.then(function(){{
      var notes=[
        {{f:392,t:0.00,d:0.22}},{{f:523,t:0.22,d:0.22}},{{f:659,t:0.44,d:0.22}},
        {{f:784,t:0.66,d:0.32}},{{f:784,t:0.98,d:0.16}},{{f:880,t:1.14,d:0.65}}
      ];
      notes.forEach(function(n){{
        var osc=actx.createOscillator(),gain=actx.createGain(),dist=actx.createWaveShaper();
        var cv=new Float32Array(256);
        for(var i=0;i<256;i++) cv[i]=(i<128?i/128:(i-256)/128)*0.5;
        dist.curve=cv;
        osc.connect(dist);dist.connect(gain);gain.connect(actx.destination);
        osc.type='sawtooth';osc.frequency.value=n.f;
        var t=actx.currentTime+n.t+0.05;
        gain.gain.setValueAtTime(0,t);
        gain.gain.linearRampToValueAtTime(0.3,t+0.04);
        gain.gain.exponentialRampToValueAtTime(0.001,t+n.d+0.08);
        osc.start(t);osc.stop(t+n.d+0.15);
      }});
    }});
  }} catch(e){{ console.warn('audio',e); }}

  /* 粒子 */
  var COLORS=['#00cec9','#0984e3','#55efc4','#fdcb6e','#ff7675','#a29bfe','#fd79a8','#fff','#ffeaa7','#6c5ce7'];
  function P(x,y,a){{
    this.x=x;this.y=y;
    this.color=COLORS[Math.floor(Math.random()*COLORS.length)];
    var spd=6+Math.random()*16;
    this.vx=Math.cos(a)*spd;this.vy=Math.sin(a)*spd;
    this.size=5+Math.random()*10;
    this.shape=Math.random()<0.5?'r':'c';
    this.rot=Math.random()*Math.PI*2;this.rs=(Math.random()-.5)*.35;
    this.life=1;this.decay=0.008+Math.random()*0.012;
    this.g=0.18+Math.random()*.15;
  }}
  P.prototype.update=function(){{this.vy+=this.g;this.vx*=.99;this.x+=this.vx;this.y+=this.vy;this.rot+=this.rs;this.life-=this.decay;}};
  P.prototype.draw=function(){{
    cx.save();cx.globalAlpha=Math.max(0,this.life);cx.fillStyle=this.color;
    cx.translate(this.x,this.y);cx.rotate(this.rot);
    if(this.shape==='r'){{ cx.fillRect(-this.size/2,-this.size/4,this.size,this.size*.5); }}
    else{{ cx.beginPath();cx.arc(0,0,this.size/2,0,Math.PI*2);cx.fill(); }}
    cx.restore();
  }};

  var bursts=[
    {{x:W*.50,y:H*.40,n:180,d:0,  a:null}},
    {{x:W*.05,y:H*.05,n:100,d:60, a:Math.PI*.25}},
    {{x:W*.95,y:H*.05,n:100,d:80, a:Math.PI*.75}},
    {{x:W*.05,y:H*.95,n:100,d:100,a:-Math.PI*.25}},
    {{x:W*.95,y:H*.95,n:100,d:120,a:-Math.PI*.75}},
    {{x:W*.50,y:H*.02,n:80, d:160,a:Math.PI*.5}},
    {{x:W*.50,y:H*.98,n:80, d:180,a:-Math.PI*.5}},
    {{x:W*.02,y:H*.50,n:80, d:200,a:0}},
    {{x:W*.98,y:H*.50,n:80, d:220,a:Math.PI}},
  ];
  var particles=[],frame=0;

  function spawn(b){{
    for(var i=0;i<b.n;i++){{
      var ang=b.a!==null?b.a+(Math.random()-.5)*Math.PI*.9:Math.random()*Math.PI*2;
      particles.push(new P(b.x,b.y,ang));
    }}
  }}
  function loop(){{
    cx.clearRect(0,0,W,H);
    bursts.forEach(function(b){{if(frame===b.d)spawn(b);}});
    particles=particles.filter(function(p){{return p.life>0;}});
    particles.forEach(function(p){{p.update();p.draw();}});
    frame++;
    if(frame<650||particles.length>0) requestAnimationFrame(loop);
    else{{
      cx.clearRect(0,0,W,H);
      try{{ canvas.remove(); }} catch(e){{}}
      try{{ doc.getElementById('vic_flash_{_id}').remove(); }} catch(e){{}}
    }}
  }}
  loop();

  /* 8秒後強制清除，避免殘留 */
  setTimeout(function(){{
    try{{ canvas.remove(); }} catch(e){{}}
    try{{ doc.getElementById('vic_flash_{_id}').remove(); }} catch(e){{}}
  }}, 8000);
}})();
</script>
</body>
</html>"""
    components.html(html, height=1, scrolling=False)


# ============================================================
# AI 輔助學習函式
# ============================================================
def get_ai_help(words_list: list, api_key: str) -> str:
    if not api_key:
        return "（未設定 Anthropic API Key，無法使用 AI 輔助）"

    words_str = "\n".join(
        [
            f"- {w['word']}：{w.get('meaning_zh', '')}（{w.get('meaning_en', '') or ''}）"
            for w in words_list
        ]
    )

    prompt = f"""你是一位專業的英文老師。學生剛剛在測驗中答錯了以下單字：

{words_str}

請用繁體中文，針對這些答錯的單字，提供：
1. 每個單字的記憶小技巧（字源、聯想、諧音、或故事）
2. 一個生動的例句（附中文翻譯）
3. 常見錯誤或混淆點（如果有的話）

格式清晰易讀，用 emoji 增加趣味性。每個單字獨立一段，最後給一個簡短的鼓勵。"""

    try:
        resp = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-opus-4-5",
                "max_tokens": 1500,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=30,
        )
        data = resp.json()
        if "content" in data and data["content"]:
            return data["content"][0].get("text", "AI 回應解析失敗")
        return f"API 錯誤：{data.get('error', {}).get('message', '未知錯誤')}"
    except Exception as e:
        return f"連線錯誤：{str(e)}"


def build_prompt(
    word: str, meaning_zh: str, meaning_en: str = "", example: str = ""
) -> str:
    lines = [
        f"我正在學習英文單字「{word}」（中文：{meaning_zh}）。",
        "請用繁體中文幫我：",
        "1. 解釋這個字的核心含義與使用場景",
        "2. 提供一個好記的記憶技巧（字根、聯想、故事或諧音皆可）",
        "3. 給出 2 個生動的例句（附中文翻譯）",
        "4. 列出 2-3 個常用搭配詞（collocations）",
        "5. 提醒我這個字容易和哪些字混淆",
    ]
    if meaning_en:
        lines.insert(1, f"英文定義：{meaning_en}")
    if example:
        lines.insert(2, f"例句參考：{example}")
    return "\n".join(lines)


# ============================================================
# 5. 登入／註冊頁面
# ============================================================
def show_auth_page():
    SAVED_EMAIL = st.secrets["autofill"]["email"]
    SAVED_PASSWORD = st.secrets["autofill"]["password"]
    st.markdown(
        """
        <div style='text-align:center; margin-top:4rem;'>
            <div style='font-family:JetBrains Mono,monospace; font-size:2.5rem; font-weight:800; color:#00cec9; text-shadow:0 0 20px rgba(0,206,201,0.4);'>⚡ Qurate Pro</div>
            <div style='color:#8b949e; font-family:JetBrains Mono,monospace; margin-bottom:2rem;'>科學化語言學習管理系統</div>
        </div>""",
        unsafe_allow_html=True,
    )
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab_login, tab_signup = st.tabs(["🔑 登入", "📝 註冊"])
        with tab_login:
            if st.button("⚡ 快速登入（已儲存帳號）", use_container_width=True):
                with st.spinner("登入中..."):
                    result = sign_in(SAVED_EMAIL, SAVED_PASSWORD)
                if "access_token" in result:
                    st.session_state.access_token = result["access_token"]
                    st.session_state.user_id = result["user"]["id"]
                    st.session_state.user_email = result["user"]["email"]
                    st.rerun()
                else:
                    st.error(
                        result.get("error_description", "登入失敗，請確認帳號密碼")
                    )
            st.divider()
            email = st.text_input("Email", key="login_email")
            password = st.text_input("密碼", type="password", key="login_pw")
            if st.button("登入", key="login_btn"):
                if email and password:
                    with st.spinner("驗證中..."):
                        result = sign_in(email, password)
                    if "access_token" in result:
                        st.session_state.access_token = result["access_token"]
                        st.session_state.user_id = result["user"]["id"]
                        st.session_state.user_email = result["user"]["email"]
                        st.rerun()
                    else:
                        st.error(
                            result.get("error_description", "登入失敗，請確認帳號密碼")
                        )
                else:
                    st.warning("請填寫 Email 和密碼")
        with tab_signup:
            new_email = st.text_input("Email", key="signup_email")
            new_password = st.text_input(
                "密碼（至少6位）", type="password", key="signup_pw"
            )
            new_password2 = st.text_input("確認密碼", type="password", key="signup_pw2")
            if st.button("建立帳號", key="signup_btn"):
                if not new_email or not new_password:
                    st.warning("請填寫所有欄位")
                elif new_password != new_password2:
                    st.error("兩次密碼不一致")
                elif len(new_password) < 6:
                    st.error("密碼至少需要 6 個字元")
                else:
                    with st.spinner("建立帳號中..."):
                        result = sign_up(new_email, new_password)
                    if "id" in result.get("user", {}):
                        st.success("🎉 帳號建立成功！請直接登入。")
                    else:
                        st.error(result.get("error_description", "註冊失敗"))


# ============================================================
# 6. 檢查登入狀態
# ============================================================
if "access_token" not in st.session_state:
    show_auth_page()
    st.stop()

access_token = st.session_state.access_token
user_email = st.session_state.get("user_email", "")
HEADERS = get_headers(access_token)

raw_data = load_data(access_token)
df = pd.DataFrame(raw_data) if raw_data else pd.DataFrame()
due_count = (
    len(df[pd.to_datetime(df["next_review"]).dt.date <= date.today()])
    if not df.empty
    else 0
)
all_categories = get_all_categories(raw_data)

# ============================================================
# 7. 側邊導航
# ============================================================
st.sidebar.markdown(
    "<h2 style='color:#00cec9; font-family:JetBrains Mono,monospace;'>⚡ Qurate Pro</h2>",
    unsafe_allow_html=True,
)
st.sidebar.caption(f"👤 {user_email}")

if st.sidebar.button("🚪 登出"):
    sign_out(access_token)
    for key in ["access_token", "user_id", "user_email"]:
        st.session_state.pop(key, None)
    st.rerun()

pulse_label = f"🎯 Flash Pulse {'🔴' if due_count > 0 else ''}"

_default_nav = st.session_state.pop("_nav_force", None)
nav_options = ["📋 Matrix Core", "🎴 Matrix Cards", pulse_label, "📅 Ebbing Log"]
if _default_nav and _default_nav in nav_options:
    _nav_idx = nav_options.index(_default_nav)
else:
    _nav_idx = (
        nav_options.index(st.session_state.get("_nav_current", nav_options[0]))
        if st.session_state.get("_nav_current") in nav_options
        else 0
    )

choice = st.sidebar.radio("SYSTEM ACCESS", nav_options, index=_nav_idx)
st.session_state["_nav_current"] = choice

st.sidebar.markdown("---")
st.sidebar.markdown("**📂 類別篩選**")
sidebar_cat = st.sidebar.selectbox(
    "目前類別",
    ["全部"] + all_categories,
    key="sidebar_cat_filter",
    label_visibility="collapsed",
)
if st.sidebar.button("🔄 Force Sync Matrix"):
    st.rerun()

# ============================================================
# 8. 頁面：Matrix Core
# ============================================================
if "Matrix Core" in choice:
    st.markdown("<div class='main-title'>Matrix Core</div>", unsafe_allow_html=True)
    t_add, t_view, t_edit = st.tabs(
        ["➕ Initialize Node", "🔍 View Matrix", "📝 Modify Protocol"]
    )

    with t_add:
        with st.form("add_matrix_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            f_word = c1.text_input("Entry（單字）*")
            f_mean = c2.text_input("Definition（中文）*")
            st.write("---")
            ca1, ca2 = st.columns(2)
            with ca1:
                f_cat_select = st.selectbox(
                    "Category（類別）",
                    all_categories + ["＋ 新增類別"],
                    key="add_cat_select",
                )
            with ca2:
                f_cat_new = st.text_input(
                    "新類別名稱",
                    placeholder="選「＋ 新增類別」後填寫",
                    key="add_cat_new",
                )
            f_category = (
                f_cat_new.strip()
                if f_cat_select == "＋ 新增類別" and f_cat_new.strip()
                else (f_cat_select if f_cat_select != "＋ 新增類別" else "預設")
            )
            st.write("---")
            st.caption("Morphology（動詞三態變化）")
            v1, v2, v3 = st.columns(3)
            f_v1 = v1.text_input("V1 (Base)")
            f_v2 = v2.text_input("V2 (Past)")
            f_v3 = v3.text_input("V3 (Participle)")
            st.write("---")
            f_pos = st.multiselect(
                "Class（詞性）", ["n.", "v.", "adj.", "adv.", "phr.", "prep."]
            )
            c3, c4 = st.columns(2)
            f_syn = c3.text_input("Synonyms（同義詞）")
            f_coll = c4.text_input("Collocations（慣用搭配）")
            f_en = st.text_area("English Definition（英文定義）")
            f_ex = st.text_area("Context Example（例句）")
            if st.form_submit_button("🚀 SYNC TO CORE"):
                if f_word.strip() and f_mean.strip():
                    payload = {
                        "word": f_word.strip(),
                        "meaning_zh": f_mean.strip(),
                        "category": f_category,
                        "pos": f_pos if f_pos else [],
                        "other_forms": [f_v1, f_v2, f_v3] if f_v1 else [],
                        "synonyms": empty_to_none(f_syn),
                        "collocations": empty_to_none(f_coll),
                        "meaning_en": empty_to_none(f_en),
                        "example": empty_to_none(f_ex),
                        "mastery": 1,
                        "next_review": get_ebbinghaus_date(1),
                        "user_id": st.session_state.user_id,
                    }
                    resp = httpx.post(
                        f"{URL}/rest/v1/vocabulary", json=payload, headers=HEADERS
                    )
                    if resp.status_code < 300:
                        st.success(f"🎉 新增成功！類別：{f_category}")
                        st.rerun()
                    else:
                        st.error(f"同步失敗：{resp.text}")
                else:
                    st.warning("請填寫單字與中文定義。")

    with t_view:
        if not df.empty:
            col_cat, col_grp = st.columns([1, 2])
            with col_cat:
                view_cat = st.selectbox(
                    "📂 類別",
                    ["全部"] + all_categories,
                    index=(["全部"] + all_categories).index(sidebar_cat)
                    if sidebar_cat in (["全部"] + all_categories)
                    else 0,
                    key="view_cat",
                )
            with col_grp:
                v_f = st.radio(
                    "Group Filter",
                    ["Due Today", "All Nodes", "L5 Mastered"],
                    horizontal=True,
                )
            d_df = df.copy()
            if view_cat != "全部":
                d_df = d_df[d_df["category"] == view_cat]
            if v_f == "Due Today":
                d_df = d_df[pd.to_datetime(d_df["next_review"]).dt.date <= date.today()]
            elif v_f == "L5 Mastered":
                d_df = d_df[d_df["mastery"] >= 5]
            st.caption(f"顯示 {len(d_df)} 筆")
            display_cols = [
                "word",
                "meaning_zh",
                "category",
                "pos",
                "mastery",
                "next_review",
            ]
            existing_cols = [c for c in display_cols if c in d_df.columns]
            st.dataframe(d_df[existing_cols], use_container_width=True, hide_index=True)
        else:
            st.info("Matrix is currently empty.")

    with t_edit:
        if not df.empty:
            edit_cat_filter = st.selectbox(
                "📂 篩選類別", ["全部"] + all_categories, key="edit_cat_filter"
            )
            word_options = (
                df[df["category"] == edit_cat_filter]["word"].tolist()
                if edit_cat_filter != "全部"
                else df["word"].tolist()
            )
            if not word_options:
                st.info("此類別目前沒有單字。")
            else:
                target_word = st.selectbox("Select Target Node", options=word_options)
                row = df[df["word"] == target_word].iloc[0]
                v_parts = parse_other_forms(row.get("other_forms"))
                current_cat = row.get("category") or "預設"
                st.markdown(
                    f"<span class='cat-badge'>📂 {current_cat}</span>",
                    unsafe_allow_html=True,
                )
                col_pron, _ = st.columns([1, 2])
                with col_pron:
                    if st.button(f"🔊 播放發音：{target_word}"):
                        play_pronunciation(target_word)
                with st.form("edit_matrix_form"):
                    e1, e2 = st.columns(2)
                    u_word = e1.text_input("Entry（單字）*", value=row["word"])
                    u_mean = e2.text_input(
                        "Definition（中文）*", value=row["meaning_zh"]
                    )
                    ea1, ea2 = st.columns(2)
                    with ea1:
                        cat_index = (
                            all_categories.index(current_cat)
                            if current_cat in all_categories
                            else 0
                        )
                        u_cat_select = st.selectbox(
                            "Category（類別）",
                            all_categories + ["＋ 新增類別"],
                            index=cat_index,
                            key="edit_cat_select",
                        )
                    with ea2:
                        u_cat_new = st.text_input(
                            "新類別名稱",
                            placeholder="選「＋ 新增類別」後填寫",
                            key="edit_cat_new",
                        )
                    u_category = (
                        u_cat_new.strip()
                        if u_cat_select == "＋ 新增類別" and u_cat_new.strip()
                        else (
                            u_cat_select
                            if u_cat_select != "＋ 新增類別"
                            else current_cat
                        )
                    )
                    dt_cur = datetime.strptime(
                        str(row["next_review"])[:10], "%Y-%m-%d"
                    ).date()
                    u_date = st.date_input("Manual Schedule（複習日期）", value=dt_cur)
                    st.write("---")
                    st.caption("Morphology（動詞三態變化）")
                    ev1, ev2, ev3 = st.columns(3)
                    u_v1 = ev1.text_input("V1 (Base)", value=v_parts[0])
                    u_v2 = ev2.text_input("V2 (Past)", value=v_parts[1])
                    u_v3 = ev3.text_input("V3 (Participle)", value=v_parts[2])
                    st.write("---")
                    pos_options = ["n.", "v.", "adj.", "adv.", "phr.", "prep."]
                    db_pos = row.get("pos", [])
                    if isinstance(db_pos, str):
                        current_pos = [
                            p.strip()
                            for p in db_pos.strip("{}").split(",")
                            if p in pos_options
                        ]
                    elif isinstance(db_pos, list):
                        current_pos = [p for p in db_pos if p in pos_options]
                    else:
                        current_pos = []
                    u_pos = st.multiselect(
                        "Class（詞性）", pos_options, default=current_pos
                    )
                    ec3, ec4 = st.columns(2)
                    u_syn = ec3.text_input(
                        "Synonyms", value=row.get("synonyms", "") or ""
                    )
                    u_coll = ec4.text_input(
                        "Collocations", value=row.get("collocations", "") or ""
                    )
                    u_en = st.text_area(
                        "English Definition", value=row.get("meaning_en", "") or ""
                    )
                    u_ex = st.text_area(
                        "Context Example", value=row.get("example", "") or ""
                    )
                    if st.form_submit_button("✅ UPDATE MATRIX"):
                        upd_payload = {
                            "word": u_word,
                            "meaning_zh": u_mean,
                            "category": u_category,
                            "pos": u_pos if u_pos else [],
                            "next_review": u_date.strftime("%Y-%m-%d"),
                            "other_forms": [u_v1, u_v2, u_v3] if u_v1 else [],
                            "synonyms": empty_to_none(u_syn),
                            "collocations": empty_to_none(u_coll),
                            "meaning_en": empty_to_none(u_en),
                            "example": empty_to_none(u_ex),
                        }
                        resp = httpx.patch(
                            f"{URL}/rest/v1/vocabulary?id=eq.{row['id']}",
                            json=upd_payload,
                            headers=HEADERS,
                        )
                        if resp.status_code < 300:
                            st.success("Node Synchronized!")
                            st.rerun()
                        else:
                            st.error(f"Update Failed: {resp.text}")
        else:
            st.info("Matrix is currently empty.")


# ============================================================
# 9. 頁面：Matrix Cards
# ============================================================
elif "Matrix Cards" in choice:
    st.markdown("<div class='main-title'>Matrix Cards</div>", unsafe_allow_html=True)

    FIELD_OPTIONS = {
        "🔤 英文單字": "word",
        "🇹🇼 中文定義": "meaning_zh",
        "📖 英文定義": "meaning_en",
        "📝 例句填空": "example_blank",
        "📝 完整例句": "example",
        "💡 詞性": "pos",
        "📚 三態變化": "other_forms",
        "🔗 同義詞": "synonyms",
        "🎯 慣用搭配": "collocations",
    }
    FIELD_LABELS = list(FIELD_OPTIONS.keys())

    TUTORIAL_STEPS = [
        {
            "icon": "🎴",
            "title": "歡迎使用 Matrix Cards！",
            "desc": "這裡是你的單字翻卡訓練區。\n開始之前，花 30 秒了解怎麼使用。",
        },
        {
            "icon": "📋",
            "title": "Step 1：選擇正面欄位",
            "desc": "正面是你的「提示」。\n建議放：中文定義 或 例句填空\n⚠️ 選擇的順序 = 卡片的排版順序！",
        },
        {
            "icon": "🔄",
            "title": "Step 2：選擇反面欄位",
            "desc": "反面是你的「答案」。\n建議放：英文單字 + 英文定義 + 完整例句",
        },
        {
            "icon": "📦",
            "title": "Step 3：選擇複習範圍與類別",
            "desc": "今日到期 = 艾賓浩斯排程到期的單字\n全部單字 = 所有單字\n可用類別篩選只練特定主題！",
        },
        {
            "icon": "🚀",
            "title": "準備好了！",
            "desc": "點「套用設定」開始翻卡！\n翻完後去 Flash Pulse 做打字測驗更新熟練度。",
        },
    ]

    for k, v in [
        ("card_tutorial_done", False),
        ("card_tutorial_step", 0),
        ("card_show_completion", False),
    ]:
        if k not in st.session_state:
            st.session_state[k] = v

    if not st.session_state.card_tutorial_done:
        step = st.session_state.card_tutorial_step
        s = TUTORIAL_STEPS[step]
        st.markdown(
            f"""
            <div class="tutorial-card">
                <div style="font-size:4rem">{s["icon"]}</div>
                <div style="font-size:1.6rem;font-weight:800;margin:0.5rem 0">{s["title"]}</div>
                <div style="opacity:0.85;line-height:1.6">{s["desc"].replace(chr(10), "<br>")}</div>
            </div>""",
            unsafe_allow_html=True,
        )
        st.progress(
            (step + 1) / len(TUTORIAL_STEPS), text=f"{step + 1} / {len(TUTORIAL_STEPS)}"
        )
        col_skip, col_prev, col_next = st.columns([2, 1, 1])
        with col_skip:
            if st.button("⏭️ 跳過教學"):
                st.session_state.card_tutorial_done = True
                st.rerun()
        with col_prev:
            if step > 0 and st.button("← 上一步"):
                st.session_state.card_tutorial_step -= 1
                st.rerun()
        with col_next:
            if step < len(TUTORIAL_STEPS) - 1:
                if st.button("下一步 →"):
                    st.session_state.card_tutorial_step += 1
                    st.rerun()
            else:
                if st.button("✅ 開始使用！"):
                    st.session_state.card_tutorial_done = True
                    st.rerun()
        st.stop()

    with st.expander(
        "⚙️ 自訂卡片模式", expanded=("card_front_fields" not in st.session_state)
    ):
        st.caption("⚠️ 選擇欄位的順序會影響卡片排版，第一個選的顯示在最上方")
        cfg1, cfg2 = st.columns(2)
        with cfg1:
            st.markdown("**正面（提示）**")
            front_choices = st.multiselect(
                "正面",
                FIELD_LABELS,
                default=st.session_state.get("card_front_fields", ["🇹🇼 中文定義"]),
                key="front_select",
                label_visibility="collapsed",
            )
        with cfg2:
            st.markdown("**反面（答案）**")
            back_choices = st.multiselect(
                "反面",
                FIELD_LABELS,
                default=st.session_state.get(
                    "card_back_fields", ["🔤 英文單字", "📖 英文定義", "📝 完整例句"]
                ),
                key="back_select",
                label_visibility="collapsed",
            )
        col_scope, col_cat, col_confirm = st.columns([1, 1, 1])
        with col_scope:
            card_scope = st.radio(
                "複習範圍",
                ["📅 今日到期", "📦 全部單字"],
                horizontal=True,
                index=0 if st.session_state.get("card_scope", "due") == "due" else 1,
            )
        with col_cat:
            card_cat = st.selectbox(
                "📂 類別篩選",
                ["全部"] + all_categories,
                index=(["全部"] + all_categories).index(
                    st.session_state.get("card_cat", "全部")
                )
                if st.session_state.get("card_cat", "全部")
                in (["全部"] + all_categories)
                else 0,
                key="card_cat_select",
            )
        with col_confirm:
            st.write("")
            st.write("")
            if st.button("✅ 套用設定", use_container_width=True):
                st.session_state.card_front_fields = front_choices
                st.session_state.card_back_fields = back_choices
                st.session_state.card_scope = "due" if "今日" in card_scope else "all"
                st.session_state.card_cat = card_cat
                st.session_state.card_index = 0
                st.session_state.is_flipped = False
                st.session_state.card_show_completion = False
                st.rerun()
        if st.button("📖 重新觀看教學"):
            st.session_state.card_tutorial_done = False
            st.session_state.card_tutorial_step = 0
            st.rerun()

    for k, v in [
        ("card_front_fields", ["🇹🇼 中文定義"]),
        ("card_back_fields", ["🔤 英文單字", "📖 英文定義", "📝 完整例句"]),
        ("card_scope", "due"),
        ("card_cat", "全部"),
    ]:
        if k not in st.session_state:
            st.session_state[k] = v

    due_cards = (
        [w for w in raw_data if str(w.get("next_review"))[:10] <= str(date.today())]
        if st.session_state.card_scope == "due"
        else list(raw_data)
    )
    if st.session_state.card_cat != "全部":
        due_cards = [
            w
            for w in due_cards
            if (w.get("category") or "預設") == st.session_state.card_cat
        ]

    def render_fields(card, field_labels, is_front=False):
        for label in field_labels:
            field_key = FIELD_OPTIONS.get(label)
            if not field_key:
                continue
            if field_key == "word":
                cat_display = card.get("category") or "預設"
                st.markdown(
                    f"<div style='text-align:center'><span class='cat-badge'>📂 {cat_display}</span></div>",
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f"<h1 style='text-align:center;font-size:3.5rem;margin:0.5rem 0'>{card['word']}</h1>",
                    unsafe_allow_html=True,
                )
                if st.button(
                    "🔊 播放發音", key=f"pron_{card.get('id', 'x')}_{is_front}"
                ):
                    play_pronunciation(card["word"])
            elif field_key == "meaning_zh":
                val = card.get("meaning_zh", "")
                if val:
                    st.markdown(
                        f"<h3 style='text-align:center'>{val}</h3>",
                        unsafe_allow_html=True,
                    )
            elif field_key == "meaning_en":
                st.markdown(f"**📖 英文定義：** {card.get('meaning_en', '') or '—'}")
            elif field_key == "example_blank":
                ex, word = card.get("example", ""), card.get("word", "")
                if ex and word:
                    blanked = re.sub(
                        re.escape(word), "**____**", ex, flags=re.IGNORECASE
                    )
                    st.markdown(f"**📝 例句填空：**\n> {blanked}")
                else:
                    st.markdown("**📝 例句填空：** —")
            elif field_key == "example":
                st.markdown(f"**📝 完整例句：**\n> {card.get('example', '') or '—'}")
            elif field_key == "pos":
                pos = card.get("pos", [])
                st.markdown(
                    f"**💡 詞性：** {', '.join(pos) if isinstance(pos, list) else pos or '—'}"
                )
            elif field_key == "other_forms":
                forms = parse_other_forms(card.get("other_forms"))
                st.markdown(
                    f"**📚 三態變化：** {' / '.join(f for f in forms if f) or '—'}"
                )
            elif field_key == "synonyms":
                st.markdown(f"**🔗 同義詞：** {card.get('synonyms', '') or '—'}")
            elif field_key == "collocations":
                st.markdown(f"**🎯 慣用搭配：** {card.get('collocations', '') or '—'}")

    if due_cards:
        if "card_index" not in st.session_state:
            st.session_state.card_index = 0
        if "is_flipped" not in st.session_state:
            st.session_state.is_flipped = False
        if st.session_state.card_index >= len(due_cards):
            st.session_state.card_index = len(due_cards) - 1

        # Matrix Cards 完成：保留原本氣球 + triangle 音效
        if st.session_state.get("card_show_completion", False):
            inject_sound("completion")
            st.balloons()
            st.markdown(
                """
            <div style="background:linear-gradient(135deg,#161b22 0%,#0d1117 100%);
                border:2px solid #00cec9;border-radius:24px;padding:3rem 2rem;
                text-align:center;box-shadow:0 0 80px rgba(0,206,201,0.4);margin:2rem auto;max-width:560px;">
                <div style="font-size:5rem;margin-bottom:0.5rem">🎉</div>
                <div style="font-family:'JetBrains Mono',monospace;font-size:1.8rem;font-weight:800;color:#00cec9;margin-bottom:0.5rem">全部看完了！</div>
                <div style="color:#8b949e;margin-bottom:2rem;font-size:1rem">太厲害了！要繼續複習還是去打字測驗？</div>
            </div>""",
                unsafe_allow_html=True,
            )
            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                if st.button("🔄 再來一次", use_container_width=True):
                    st.session_state.card_index = 0
                    st.session_state.is_flipped = False
                    st.session_state.card_show_completion = False
                    st.rerun()
            with btn_col2:
                if st.button("⚡ 去 Flash Pulse 測驗", use_container_width=True):
                    st.session_state.card_show_completion = False
                    st.session_state["_nav_force"] = pulse_label
                    st.rerun()
            st.stop()

        st.session_state.card_index = max(
            0, min(st.session_state.card_index, len(due_cards) - 1)
        )
        current_card = due_cards[st.session_state.card_index]
        scope_label = "今日到期" if st.session_state.card_scope == "due" else "全部單字"
        cat_label = (
            f"｜📂 {st.session_state.card_cat}"
            if st.session_state.card_cat != "全部"
            else ""
        )
        total_cards = len(due_cards)
        slider_val = max(1, min(st.session_state.card_index + 1, total_cards))
        if total_cards > 1:
            new_index = (
                st.slider(
                    f"📦 {scope_label}{cat_label}",
                    min_value=1,
                    max_value=total_cards,
                    value=slider_val,
                    format="%d 張",
                )
                - 1
            )
            if new_index != st.session_state.card_index:
                st.session_state.card_index = new_index
                st.session_state.is_flipped = False
                st.rerun()
        else:
            st.caption(f"📦 {scope_label}{cat_label}　1 / 1 張")

        st.progress((st.session_state.card_index + 1) / len(due_cards))
        with st.container(border=True):
            if not st.session_state.is_flipped:
                render_fields(
                    current_card, st.session_state.card_front_fields, is_front=True
                )
            else:
                st.markdown("---")
                render_fields(
                    current_card, st.session_state.card_back_fields, is_front=False
                )

        st.write("")
        b1, b2, b3 = st.columns([1, 2, 1])
        with b1:
            if st.button("⬅️ 上一字") and st.session_state.card_index > 0:
                st.session_state.card_index -= 1
                st.session_state.is_flipped = False
                st.rerun()
        with b2:
            if st.button(
                "🔄 翻到反面" if not st.session_state.is_flipped else "🔄 翻回正面"
            ):
                st.session_state.is_flipped = not st.session_state.is_flipped
                st.rerun()
        with b3:
            if st.button("下一字 ➡️"):
                if st.session_state.card_index < len(due_cards) - 1:
                    st.session_state.card_index += 1
                    st.session_state.is_flipped = False
                    st.rerun()
                else:
                    st.session_state.card_show_completion = True
                    st.rerun()
    else:
        st.success("✨ 目前沒有符合條件的單字卡！")


# ============================================================
# 10. 頁面：Flash Pulse
# ============================================================
elif "Flash Pulse" in choice:
    st.markdown("<div class='main-title'>Flash Pulse</div>", unsafe_allow_html=True)

    pulse_cat = st.selectbox(
        "📂 練習類別", ["全部"] + all_categories, key="pulse_cat_filter"
    )
    all_due = [
        w for w in raw_data if str(w.get("next_review"))[:10] <= str(date.today())
    ]
    due = (
        [w for w in all_due if (w.get("category") or "預設") == pulse_cat]
        if pulse_cat != "全部"
        else all_due
    )

    if not due:
        msg = (
            f"「{pulse_cat}」類別目前沒有待複習的單字。"
            if pulse_cat != "全部"
            else "Matrix Stable. No nodes due for review."
        )
        st.success(msg)
        st.stop()

    def init_session():
        shuffled = list(due)
        random.shuffle(shuffled)
        st.session_state.pulse_session_words = shuffled
        st.session_state.pulse_session_idx = 0
        st.session_state.pulse_wrong_words = []
        st.session_state.pulse_session_done = False
        st.session_state.pulse_review_mode = False
        st.session_state.pulse_review_idx = 0
        st.session_state.pulse_review_flipped = False
        st.session_state.hint_level = 0
        st.session_state.pulse_ai_mode = False
        st.session_state.pulse_match_mode = False
        st.session_state.pulse_ai_response = ""
        st.session_state.prompt_expanded = {}
        st.session_state.pulse_victory_shown = False
        st.session_state.pulse_last_correct = False

    if "pulse_session_words" not in st.session_state:
        init_session()

    if st.button("🔄 重新開始測驗（今日到期單字）", use_container_width=True):
        init_session()
        st.rerun()

    st.markdown("---")

    session_words = st.session_state.get("pulse_session_words", [])
    if not session_words:
        init_session()
        st.rerun()

    # ══════════════════════════════════════════════════════════
    # 連連看模式
    # ══════════════════════════════════════════════════════════
    if st.session_state.get("pulse_match_mode", False):
        wrong_list = st.session_state.get("pulse_wrong_words", [])
        if not wrong_list:
            st.session_state.pulse_match_mode = False
            st.rerun()

        st.markdown("### 🎮 連連看：英文配中文")
        st.caption("點選左欄的英文單字，再點右欄對應的中文定義")

        if "match_pairs" not in st.session_state or st.session_state.get(
            "match_reset", False
        ):
            sample = wrong_list[: min(8, len(wrong_list))]
            left_items = [w["word"] for w in sample]
            right_items = [w["meaning_zh"] for w in sample]
            random.shuffle(right_items)
            st.session_state.match_pairs = {w["word"]: w["meaning_zh"] for w in sample}
            st.session_state.match_left = left_items
            st.session_state.match_right = right_items
            st.session_state.match_selected_left = None
            st.session_state.match_matched = set()
            st.session_state.match_wrong_flash = set()
            st.session_state.match_reset = False

        pairs = st.session_state.match_pairs
        left_items = st.session_state.match_left
        right_items = st.session_state.match_right
        matched = st.session_state.match_matched
        selected_left = st.session_state.match_selected_left
        wrong_flash = st.session_state.match_wrong_flash

        total_pairs = len(left_items)
        st.progress(
            len(matched) / total_pairs if total_pairs > 0 else 0,
            text=f"已配對 {len(matched)} / {total_pairs}",
        )

        col_left, col_spacer, col_right = st.columns([2, 0.2, 2])

        with col_left:
            st.markdown("**🔤 英文單字**")
            for word in left_items:
                if word in matched:
                    st.markdown(
                        f"<div style='background:rgba(85,239,196,0.15);border:1px solid #55efc4;"
                        f"border-radius:8px;padding:0.5rem 1rem;margin-bottom:0.4rem;"
                        f"color:#55efc4;font-family:JetBrains Mono,monospace;opacity:0.6'>"
                        f"✓ {word}</div>",
                        unsafe_allow_html=True,
                    )
                elif word == selected_left:
                    if st.button(
                        f"▶ {word}", key=f"ml_{word}", use_container_width=True
                    ):
                        st.session_state.match_selected_left = None
                        st.rerun()
                else:
                    if word in wrong_flash:
                        st.markdown(
                            f"<div style='background:rgba(214,48,49,0.2);border:2px solid #d63031;"
                            f"border-radius:8px;padding:0.5rem 1rem;margin-bottom:0.4rem;"
                            f"color:#ff7675;font-family:JetBrains Mono,monospace'>"
                            f"✗ {word}</div>",
                            unsafe_allow_html=True,
                        )
                    else:
                        if st.button(word, key=f"ml_{word}", use_container_width=True):
                            st.session_state.match_selected_left = word
                            st.session_state.match_wrong_flash = set()
                            st.rerun()

        with col_right:
            st.markdown("**🇹🇼 中文定義**")
            for meaning in right_items:
                matched_word = next(
                    (w for w, m in pairs.items() if m == meaning and w in matched), None
                )
                if matched_word:
                    st.markdown(
                        f"<div style='background:rgba(85,239,196,0.15);border:1px solid #55efc4;"
                        f"border-radius:8px;padding:0.5rem 1rem;margin-bottom:0.4rem;"
                        f"color:#55efc4;opacity:0.6'>"
                        f"✓ {meaning}</div>",
                        unsafe_allow_html=True,
                    )
                else:
                    is_wrong = meaning in wrong_flash
                    if is_wrong:
                        st.markdown(
                            f"<div style='background:rgba(214,48,49,0.2);border:2px solid #d63031;"
                            f"border-radius:8px;padding:0.5rem 1rem;margin-bottom:0.4rem;"
                            f"color:#ff7675'>"
                            f"✗ {meaning}</div>",
                            unsafe_allow_html=True,
                        )
                    else:
                        if st.button(
                            meaning, key=f"mr_{meaning}", use_container_width=True
                        ):
                            if selected_left:
                                correct_meaning = pairs.get(selected_left)
                                if correct_meaning == meaning:
                                    matched.add(selected_left)
                                    st.session_state.match_matched = matched
                                    st.session_state.match_selected_left = None
                                    inject_sound("success")
                                    if len(matched) == total_pairs:
                                        inject_sound("completion")
                                        st.balloons()
                                    st.rerun()
                                else:
                                    st.session_state.match_wrong_flash = {
                                        selected_left,
                                        meaning,
                                    }
                                    st.session_state.match_selected_left = None
                                    st.rerun()
                            else:
                                st.info("請先點選左邊的英文單字！")

        if len(matched) == total_pairs:
            st.markdown(
                """
                <div style="background:linear-gradient(135deg,#161b22,#0d1117);
                    border:2px solid #55efc4;border-radius:16px;padding:2rem;
                    text-align:center;margin:1rem 0;">
                    <div style="font-size:3rem">🏆</div>
                    <div style="color:#55efc4;font-family:JetBrains Mono,monospace;font-size:1.4rem;font-weight:800">全部配對完成！</div>
                </div>""",
                unsafe_allow_html=True,
            )
            mc1, mc2 = st.columns(2)
            with mc1:
                if st.button("🔄 再玩一次連連看", use_container_width=True):
                    st.session_state.match_reset = True
                    st.rerun()
            with mc2:
                if st.button("✅ 結束複習", use_container_width=True):
                    st.session_state.pulse_match_mode = False
                    init_session()
                    st.rerun()
        else:
            st.write("")
            if st.button("🏳️ 離開連連看", use_container_width=True):
                st.session_state.pulse_match_mode = False
                st.rerun()
        st.stop()

    # ══════════════════════════════════════════════════════════
    # AI 輔助學習模式
    # ══════════════════════════════════════════════════════════
    if st.session_state.get("pulse_ai_mode", False):
        wrong_list = st.session_state.get("pulse_wrong_words", [])
        st.markdown("### 🤖 AI 記憶輔助")
        st.caption(f"針對 {len(wrong_list)} 個答錯的單字，AI 提供記憶技巧")

        if not st.session_state.get("pulse_ai_response"):
            with st.spinner("🧠 AI 正在分析你的弱點單字..."):
                response = get_ai_help(wrong_list, ANTHROPIC_API_KEY)
                st.session_state.pulse_ai_response = response

        ai_text = st.session_state.get("pulse_ai_response", "")
        if ai_text:
            st.markdown(
                f"<div class='ai-bubble'>{ai_text.replace(chr(10), '<br>')}</div>",
                unsafe_allow_html=True,
            )

        ab1, ab2 = st.columns(2)
        with ab1:
            if st.button("🎮 去玩連連看", use_container_width=True):
                st.session_state.pulse_ai_mode = False
                st.session_state.pulse_match_mode = True
                st.session_state.match_reset = True
                st.rerun()
        with ab2:
            if st.button("🔄 重新測驗", use_container_width=True):
                st.session_state.pulse_ai_mode = False
                init_session()
                st.rerun()
        st.stop()

    # ══════════════════════════════════════════════════════════
    # 翻卡複習模式（答錯清單）
    # ══════════════════════════════════════════════════════════
    if st.session_state.get("pulse_review_mode", False):
        wrong_list = st.session_state.get("pulse_wrong_words", [])
        rev_idx = st.session_state.get("pulse_review_idx", 0)

        if not wrong_list:
            st.success("🎉 沒有答錯的單字，太強了！")
            if st.button("🔄 再來一輪測驗", use_container_width=True):
                init_session()
                st.rerun()
            st.stop()

        if rev_idx >= len(wrong_list):
            rev_idx = 0
            st.session_state.pulse_review_idx = 0

        st.markdown(f"### 📚 答錯單字複習　{rev_idx + 1} / {len(wrong_list)}")
        st.progress((rev_idx + 1) / len(wrong_list))

        rc = wrong_list[rev_idx]
        rev_flipped = st.session_state.get("pulse_review_flipped", False)

        with st.container(border=True):
            if not rev_flipped:
                cat_display = rc.get("category") or "預設"
                st.markdown(
                    f"<span class='cat-badge'>📂 {cat_display}</span>",
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f"<h3 style='text-align:center'>💡 {rc['meaning_zh']}</h3>",
                    unsafe_allow_html=True,
                )
                if rc.get("example"):
                    st.caption(
                        f"📝 Context: {rc['example'].replace(rc['word'], '____')}"
                    )
            else:
                st.markdown(
                    f"<h1 style='text-align:center;font-size:3rem;color:#00cec9'>{rc['word']}</h1>",
                    unsafe_allow_html=True,
                )
                if rc.get("meaning_en"):
                    st.markdown(f"**📖 英文定義：** {rc['meaning_en']}")
                if rc.get("example"):
                    st.markdown(f"**📝 例句：** {rc['example']}")
                if rc.get("collocations"):
                    st.markdown(f"**🎯 慣用搭配：** {rc['collocations']}")
                if st.button("🔊 播放發音", key=f"rev_pron_{rc.get('id', 'x')}"):
                    play_pronunciation(rc["word"])

        rb1, rb2, rb3 = st.columns([1, 2, 1])
        with rb1:
            if st.button("⬅️ 上一字", key="rev_prev") and rev_idx > 0:
                st.session_state.pulse_review_idx -= 1
                st.session_state.pulse_review_flipped = False
                st.rerun()
        with rb2:
            if st.button(
                "🔄 翻到反面" if not rev_flipped else "🔄 翻回正面", key="rev_flip"
            ):
                st.session_state.pulse_review_flipped = not rev_flipped
                st.rerun()
        with rb3:
            next_label = "下一字 ➡️" if rev_idx < len(wrong_list) - 1 else "✅ 複習完畢"
            if st.button(next_label, key="rev_next"):
                if rev_idx < len(wrong_list) - 1:
                    st.session_state.pulse_review_idx += 1
                    st.session_state.pulse_review_flipped = False
                    st.rerun()
                else:
                    init_session()
                    st.rerun()
        st.stop()

    # ══════════════════════════════════════════════════════════
    # 最後一題答對後的停留畫面（在結束畫面前攔截）
    # ══════════════════════════════════════════════════════════
    if st.session_state.get("pulse_last_correct", False):
        inject_sound("success")
        st.markdown(
            """
<div style="text-align:center;padding:3rem 0;">
  <div style="font-size:6rem">🎉</div>
  <div style="font-family:'JetBrains Mono',monospace;font-size:2rem;font-weight:800;color:#55efc4;margin:0.5rem 0">
    Correct!
  </div>
  <div style="color:#8b949e;font-size:1.1rem;margin-bottom:2rem">最後一個單字答對了！</div>
</div>""",
            unsafe_allow_html=True,
        )
        if st.button("🏁 查看測驗結果", use_container_width=True):
            st.session_state.pulse_last_correct = False
            st.session_state.pulse_session_done = True
            st.rerun()
        st.stop()

    # ══════════════════════════════════════════════════════════
    # 測驗結束畫面  ← Flash Pulse 專用勝利特效
    # ══════════════════════════════════════════════════════════
    # idx 超出時直接設 done，不 rerun，同一次渲染直接顯示結束畫面
    if st.session_state.pulse_session_idx >= len(session_words):
        st.session_state.pulse_session_done = True

    if st.session_state.get("pulse_session_done", False):
        wrong_list = st.session_state.get("pulse_wrong_words", [])
        total = len(session_words)
        correct_count = total - len(wrong_list)

        if correct_count > 0 and not st.session_state.get("pulse_victory_shown", False):
            inject_congrats_sound()
            inject_victory_effect()
            st.session_state.pulse_victory_shown = True

        st.markdown(
            f"""
        <div style="background:linear-gradient(135deg,#161b22 0%,#0d1117 100%);
            border:2px solid #00cec9;border-radius:24px;padding:2.5rem 2rem;
            text-align:center;box-shadow:0 0 60px rgba(0,206,201,0.4);margin-bottom:1.5rem;">
            <div style="font-size:4rem">{"🏆" if not wrong_list else "📝"}</div>
            <div style="font-family:'JetBrains Mono',monospace;font-size:1.6rem;font-weight:800;color:#00cec9;margin:0.5rem 0">測驗完成！</div>
            <div style="font-size:2rem;font-weight:800;color:#55efc4">{correct_count} / {total} 答對</div>
            <div style="color:#8b949e;margin-top:0.5rem">{"全部答對，超厲害！🎉" if not wrong_list else f"有 {len(wrong_list)} 個單字需要加強複習"}</div>
        </div>""",
            unsafe_allow_html=True,
        )

        if wrong_list:
            if "prompt_expanded" not in st.session_state:
                st.session_state.prompt_expanded = {}

            st.markdown("### ❌ 答錯的單字")

            for w in wrong_list:
                word_id = str(w.get("id", w["word"]))
                pos_list = w.get("pos", [])
                pos_str = (
                    "　".join(pos_list)
                    if isinstance(pos_list, list) and pos_list
                    else ""
                )
                is_expanded = st.session_state.prompt_expanded.get(word_id, False)

                col_info, col_btn = st.columns([5, 2])
                with col_info:
                    example_html = ""
                    if w.get("example"):
                        example_html = f"<br><small style='color:#636e72'>📝 {w['example'].replace(w['word'], '____')}</small>"
                    pos_html = ""
                    if pos_str:
                        pos_html = f"<span style='color:#74b9ff;font-size:0.8rem;margin-left:0.6rem'>{pos_str}</span>"
                    st.markdown(
                        f"""<div class="wrong-card">
                            <b style="color:#ff7675;font-size:1.05rem">{w["word"]}</b>
                            {pos_html}
                            <span style="color:#8b949e;margin-left:0.8rem">{w.get("meaning_zh", "")}</span>
                            {example_html}
                        </div>""",
                        unsafe_allow_html=True,
                    )
                with col_btn:
                    btn_label = (
                        "✅ 已展開提示詞" if is_expanded else "📋 複製 AI 提示詞"
                    )
                    if st.button(
                        btn_label, key=f"prompt_btn_{word_id}", use_container_width=True
                    ):
                        st.session_state.prompt_expanded[word_id] = not is_expanded
                        st.rerun()

                if is_expanded:
                    prompt_text = build_prompt(
                        word=w["word"],
                        meaning_zh=w.get("meaning_zh", ""),
                        meaning_en=w.get("meaning_en", ""),
                        example=w.get("example", ""),
                    )
                    st.code(prompt_text, language=None)
                    st.caption(
                        "👆 點選右上角複製圖示，貼到 ChatGPT / Gemini / Claude 即可學習"
                    )

            st.write("")
            st.markdown("### 📚 繼續強化這些單字")
            dc1, dc2, dc3 = st.columns(3)
            with dc1:
                if st.button("🎴 翻卡複習", use_container_width=True):
                    st.session_state.pulse_review_mode = True
                    st.session_state.pulse_review_idx = 0
                    st.session_state.pulse_review_flipped = False
                    st.rerun()
            with dc2:
                if st.button("🎮 連連看", use_container_width=True):
                    st.session_state.pulse_match_mode = True
                    st.session_state.match_reset = True
                    st.rerun()
            with dc3:
                if st.button("🤖 AI 記憶輔助", use_container_width=True):
                    st.session_state.pulse_ai_mode = True
                    st.session_state.pulse_ai_response = ""
                    st.rerun()

            st.write("")
            if st.button("🔄 重新測驗全部", use_container_width=True):
                init_session()
                st.rerun()
        else:
            if st.button("🔄 再來一輪", use_container_width=True):
                init_session()
                st.rerun()
        st.stop()

    # ══════════════════════════════════════════════════════════
    # 正在作答
    # ══════════════════════════════════════════════════════════

    idx = st.session_state.pulse_session_idx
    if idx >= len(session_words):
        st.session_state.pulse_session_done = True
        st.rerun()

    q = session_words[idx]
    hint_level = st.session_state.get("hint_level", 0)
    total = len(session_words)
    wrong_so_far = len(st.session_state.get("pulse_wrong_words", []))

    st.markdown(f"**進度：{idx + 1} / {total}　｜　已答錯：{wrong_so_far} 個**")
    st.progress((idx + 1) / total)

    abandon_col, _ = st.columns([1, 3])
    with abandon_col:
        if st.button("🏳️ 放棄（拼不出來）", use_container_width=True):
            current_m = q.get("mastery", 1)
            new_m = calculate_new_mastery(current_m)
            update_mastery_in_db(q["id"], new_m, access_token)
            wrong_list = st.session_state.get("pulse_wrong_words", [])
            wrong_list.append(q)
            st.session_state.pulse_wrong_words = wrong_list
            st.session_state.pulse_session_idx += 1
            st.session_state.hint_level = 0
            if st.session_state.pulse_session_idx >= total:
                st.session_state.pulse_session_done = True
            st.rerun()

    with st.container(border=True):
        cat_display = q.get("category") or "預設"
        st.markdown(
            f"<span class='cat-badge'>📂 {cat_display}</span>",
            unsafe_allow_html=True,
        )
        st.markdown(f"### 💡 中文提示：**{q['meaning_zh']}**")
        if q.get("example"):
            st.caption(f"📝 Context: {q['example'].replace(q['word'], '____')}")
        if hint_level == 1:
            st.markdown(
                f"<div class='hint-badge'>💡 字首提示：{q['word'][0].upper()}...</div>",
                unsafe_allow_html=True,
            )
            play_pronunciation(q["word"])
        elif hint_level == 2:
            st.markdown(
                f"<div class='hint-badge'>📖 英文定義：{q.get('meaning_en', '（無英文定義）')}</div>",
                unsafe_allow_html=True,
            )
        st.caption(
            f"目前熟練度：{'⭐' * int(q.get('mastery', 1))} L{q.get('mastery', 1)}"
        )

    with st.form("pulse_form_session", clear_on_submit=True):
        ans = st.text_input(
            "Type the correct Entry（不分大小寫）:",
            key="pulse_input_s",
            placeholder="輸入答案後按 Enter 送出",
        )
        col1, col2 = st.columns([3, 1])
        with col1:
            submitted = st.form_submit_button(
                "EXECUTE VERIFICATION", use_container_width=True
            )
        with col2:
            play_btn = st.form_submit_button("🔊 發音", use_container_width=True)

    if submitted and ans.strip():
        if ans.strip().lower() == q["word"].lower():
            inject_sound("success")
            new_m = min(5, q["mastery"] + 1)
            update_mastery_in_db(q["id"], new_m, access_token)
            st.session_state.pulse_session_idx += 1
            st.session_state.hint_level = 0
            if st.session_state.pulse_session_idx >= total:
                # 最後一題：顯示答對畫面，等使用者按按鈕才跳到結束
                st.session_state.pulse_last_correct = True
                st.rerun()
            else:
                st.success("✅ Correct!")
                st.rerun()
        else:
            if hint_level < 2:
                st.session_state.hint_level += 1
                st.warning(f"❌ 答錯！給你提示 {st.session_state.hint_level}/2")
                st.rerun()
            else:
                current_m = q.get("mastery", 1)
                new_m = calculate_new_mastery(current_m)
                update_mastery_in_db(q["id"], new_m, access_token)
                st.error(f"💀 答案是：**{q['word']}**　熟練度 L{current_m} → L{new_m}")
                wrong_list = st.session_state.get("pulse_wrong_words", [])
                wrong_list.append(q)
                st.session_state.pulse_wrong_words = wrong_list
                st.session_state.pulse_session_idx += 1
                st.session_state.hint_level = 0
                if st.session_state.pulse_session_idx >= total:
                    st.session_state.pulse_session_done = True
                st.rerun()

    if play_btn:
        play_pronunciation(q["word"])

    st.markdown("---")
    hint_status = {
        0: "🟢 無提示",
        1: "🟡 字首已顯示",
        2: "🔴 英文定義已顯示（再答不出將降級）",
    }
    st.caption(f"提示狀態：{hint_status[hint_level]}")


# ============================================================
# 11. 頁面：Ebbing Log
# ============================================================
elif "Ebbing Log" in choice:
    st.markdown("<div class='main-title'>Ebbing Log</div>", unsafe_allow_html=True)

    if not df.empty:
        ebbing_cat = st.selectbox(
            "📂 類別篩選", ["全部"] + all_categories, key="ebbing_cat_filter"
        )
        df_filtered = (
            df[df["category"] == ebbing_cat].copy()
            if ebbing_cat != "全部"
            else df.copy()
        )

        level_counts = df_filtered.groupby("mastery").size().reset_index()
        level_counts.columns = ["Level", "數量"]
        all_levels = pd.DataFrame({"Level": [0, 1, 2, 3, 4, 5]})
        level_counts = all_levels.merge(level_counts, on="Level", how="left").fillna(0)
        level_counts["數量"] = level_counts["數量"].astype(int)

        fig_levels = go.Figure()
        fig_levels.add_trace(
            go.Scatter(
                x=level_counts["Level"],
                y=level_counts["數量"],
                mode="lines+markers+text",
                text=level_counts["數量"],
                textposition="top center",
                line=dict(color="#00cec9", width=3),
                marker=dict(
                    size=12, color="#ff7675", line=dict(color="#00cec9", width=2)
                ),
            )
        )
        fig_levels.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            height=280,
            margin=dict(l=0, r=0, t=30, b=0),
            xaxis=dict(
                tickvals=[0, 1, 2, 3, 4, 5],
                ticktext=[
                    "L0 遺忘",
                    "L1 初學",
                    "L2 認識",
                    "L3 熟悉",
                    "L4 精通",
                    "L5 掌握",
                ],
                showgrid=True,
                gridcolor="rgba(255,255,255,0.1)",
                color="#8b949e",
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor="rgba(255,255,255,0.1)",
                title="單字數量",
                color="#8b949e",
            ),
            showlegend=False,
            font=dict(color="#e6edf3"),
        )
        st.plotly_chart(fig_levels, use_container_width=True)

        total = len(df_filtered)
        level_colors = [
            "#d63031",
            "#ff7675",
            "#fdcb6e",
            "#74b9ff",
            "#55efc4",
            "#6c5ce7",
        ]
        cols = st.columns(6)
        for i, (col, color) in enumerate(zip(cols, level_colors)):
            count = int(level_counts[level_counts["Level"] == i]["數量"].values[0])
            pct = f"{count / total * 100:.0f}%" if total > 0 else "0%"
            col.markdown(
                f"<div style='background:{color}20;border-left:4px solid {color};"
                f"padding:0.4rem 0.6rem;border-radius:8px;text-align:center'>"
                f"<b>L{i}</b><br>{count}<br><small>{pct}</small></div>",
                unsafe_allow_html=True,
            )

        st.write("")
        st.divider()

        st.markdown("**⏰ 最近待複習（前 10 筆）**")
        upcoming = df_filtered.sort_values("next_review").head(10)
        for _, row in upcoming.iterrows():
            days_until = (pd.to_datetime(row["next_review"]).date() - date.today()).days
            badge = (
                f"🔴 過期{abs(days_until)}天"
                if days_until < 0
                else ("🟡 今日" if days_until == 0 else f"🟢 {days_until}天後")
            )
            cat_tag = row.get("category") or "預設"
            st.markdown(
                f"<div style='padding:0.4rem 0.6rem;margin-bottom:0.4rem;"
                f"background:rgba(255,255,255,0.05);border-radius:8px;font-size:0.88rem'>"
                f"<b>{row['word']}</b> {badge} <span class='cat-badge'>{cat_tag}</span><br>"
                f"<span style='color:#8b949e'>{row['meaning_zh']} ｜ L{row['mastery']}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
    else:
        st.info("Insufficient data for log prediction.")
