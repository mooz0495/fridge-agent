import streamlit as st
import json
import os
import base64
from datetime import datetime, timedelta
import google.generativeai as genai
from PIL import Image
import io

# ── 페이지 설정 ──────────────────────────────────────
st.set_page_config(
    page_title="스마트 냉장고 AI",
    page_icon="🧊",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── 카테고리 아이콘 ───────────────────────────────────
CATEGORY_ICON = {
    "채소/과일": "🥦",
    "육류/수산": "🥩",
    "유제품/계란": "🥚",
    "가공식품": "🥫",
    "조미료/소스": "🧂",
    "기타": "🍽️",
}

# ── CSS ───────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Noto Sans KR', sans-serif;
}

/* 전체 배경 */
.stApp {
    background: #f0f4f8;
}

/* 헤더 */
.hero {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    border-radius: 20px;
    padding: 28px 24px 20px;
    margin-bottom: 20px;
    text-align: center;
    box-shadow: 0 8px 32px rgba(0,0,0,0.2);
}
.hero h1 {
    color: white;
    font-size: 26px;
    font-weight: 700;
    margin: 0 0 4px 0;
}
.hero p {
    color: rgba(255,255,255,0.6);
    font-size: 13px;
    margin: 0;
}

/* 통계 카드 */
.stat-row {
    display: flex;
    gap: 10px;
    margin: 12px 0;
}
.stat-card {
    flex: 1;
    background: white;
    border-radius: 14px;
    padding: 14px 10px;
    text-align: center;
    box-shadow: 0 2px 12px rgba(0,0,0,0.07);
}
.stat-num {
    font-size: 24px;
    font-weight: 700;
    line-height: 1;
}
.stat-label {
    font-size: 11px;
    color: #888;
    margin-top: 4px;
}
.stat-total .stat-num { color: #1a1a2e; }
.stat-warn .stat-num  { color: #f59e0b; }
.stat-danger .stat-num{ color: #ef4444; }

/* 재료 카드 */
.ing-card {
    background: white;
    border-radius: 14px;
    padding: 14px 16px;
    margin: 8px 0;
    display: flex;
    align-items: center;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    border-left: 4px solid #22c55e;
    transition: transform .15s;
}
.ing-card.warn  { border-left-color: #f59e0b; background: #fffbeb; }
.ing-card.danger{ border-left-color: #ef4444; background: #fef2f2; }
.ing-icon { font-size: 28px; margin-right: 12px; }
.ing-info { flex: 1; }
.ing-name { font-size: 15px; font-weight: 600; color: #1a1a2e; }
.ing-meta { font-size: 12px; color: #888; margin-top: 2px; }
.ing-badge {
    font-size: 11px;
    font-weight: 700;
    padding: 3px 8px;
    border-radius: 20px;
    white-space: nowrap;
}
.badge-ok     { background: #dcfce7; color: #15803d; }
.badge-warn   { background: #fef3c7; color: #b45309; }
.badge-danger { background: #fee2e2; color: #b91c1c; }

/* 섹션 헤더 */
.section-header {
    font-size: 13px;
    font-weight: 700;
    color: #6b7280;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin: 16px 0 8px;
}

/* 빠른 질문 버튼 */
.stButton > button {
    border-radius: 12px !important;
    font-size: 13px !important;
    border: 1.5px solid #e5e7eb !important;
    background: white !important;
    color: #374151 !important;
    transition: all .2s !important;
}
.stButton > button:hover {
    border-color: #6366f1 !important;
    color: #6366f1 !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(99,102,241,0.15) !important;
}

/* expander 스타일 */
details {
    background: white !important;
    border-radius: 14px !important;
    border: 1.5px solid #e5e7eb !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06) !important;
    margin-bottom: 12px !important;
}
details summary {
    color: #1a1a2e !important;
    font-weight: 600 !important;
    font-size: 15px !important;
    padding: 14px 16px !important;
}
details summary:hover {
    background: #f9fafb !important;
    border-radius: 14px !important;
}
.streamlit-expanderHeader,
.streamlit-expanderHeader p,
[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary p {
    color: #1a1a2e !important;
    font-weight: 600 !important;
}

/* 탭 스타일 */
.stTabs [data-baseweb="tab-list"] {
    background: white;
    border-radius: 12px;
    padding: 4px;
    gap: 4px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px !important;
    font-size: 13px !important;
    color: #374151 !important;
}
.stTabs [data-baseweb="tab"] p {
    color: #374151 !important;
}
.stTabs [aria-selected="true"] {
    background: #1a1a2e !important;
    color: white !important;
}
.stTabs [aria-selected="true"] p {
    color: white !important;
}

/* 빈 냉장고 */
.empty-fridge {
    text-align: center;
    padding: 40px 20px;
    color: #9ca3af;
}
.empty-fridge .icon { font-size: 56px; margin-bottom: 12px; }
.empty-fridge .text { font-size: 15px; }

/* 알림 카드 */
.alert-card {
    border-radius: 14px;
    padding: 14px 16px;
    margin: 8px 0;
    display: flex;
    align-items: center;
    gap: 12px;
}
.alert-danger { background: #fef2f2; border: 1px solid #fecaca; }
.alert-warn   { background: #fffbeb; border: 1px solid #fde68a; }
.alert-ok     { background: #f0fdf4; border: 1px solid #bbf7d0; }
.alert-icon   { font-size: 22px; }
.alert-name   { font-size: 14px; font-weight: 600; color: #1a1a2e; }
.alert-sub    { font-size: 12px; color: #6b7280; }
</style>
""", unsafe_allow_html=True)

# ── 데이터 저장/불러오기 ──────────────────────────────
DATA_FILE = "fridge_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ── 유통기한 상태 계산 ────────────────────────────────
def get_expiry_status(expiry_date_str):
    if not expiry_date_str:
        return "ok", "날짜없음", 999
    try:
        expiry = datetime.strptime(expiry_date_str, "%Y-%m-%d")
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        days_left = (expiry - today).days
        if days_left < 0:
            return "danger", f"만료 {abs(days_left)}일 지남", days_left
        elif days_left <= 2:
            return "danger", f"D-{days_left} 위험!", days_left
        elif days_left <= 5:
            return "warning", f"D-{days_left} 주의", days_left
        else:
            return "ok", f"D-{days_left}", days_left
    except:
        return "ok", "날짜오류", 999

# ── Gemini AI ─────────────────────────────────────────
def get_gemini_model(api_key: str):
    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-1.5-flash-latest")

def recognize_ingredients_from_image(image_bytes: bytes, api_key: str) -> list:
    model = get_gemini_model(api_key)
    image = Image.open(io.BytesIO(image_bytes))
    prompt = """이 사진에서 식재료를 모두 찾아서 JSON 형식으로 알려주세요.
반드시 아래 형식만 출력하고 다른 설명은 쓰지 마세요.

[
  {"name": "재료이름", "quantity": "수량(모르면 1개)", "category": "채소/과일 or 육류/수산 or 유제품/계란 or 가공식품 or 조미료/소스 or 기타"},
  ...
]

식재료가 없으면 [] 를 출력하세요."""
    response = model.generate_content([prompt, image])
    text = response.text.strip()
    start = text.find("[")
    end = text.rfind("]") + 1
    if start == -1 or end == 0:
        return []
    return json.loads(text[start:end])

# ── 세션 초기화 ───────────────────────────────────────
if "ingredients" not in st.session_state:
    st.session_state.ingredients = load_data()
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

# ── 사이드바 (API 키) ─────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ 설정")
    api_input = st.text_input("Gemini API 키", type="password",
                               value=st.session_state.api_key,
                               placeholder="AIza...")
    if api_input:
        st.session_state.api_key = api_input
        st.success("✅ API 키 등록됨")
    st.markdown("---")
    st.markdown("**앱 버전** v1.0")
    st.markdown("**개발** 경운대학교 SW경진대회")

# ── 헤더 ─────────────────────────────────────────────
total = len(st.session_state.ingredients)
danger_count = sum(1 for i in st.session_state.ingredients if get_expiry_status(i.get("expiry",""))[0]=="danger")
warn_count   = sum(1 for i in st.session_state.ingredients if get_expiry_status(i.get("expiry",""))[0]=="warning")

st.markdown(f"""
<div class="hero">
    <h1>🧊 스마트 냉장고 AI</h1>
    <p>AI가 재료를 인식하고 레시피를 추천해드려요</p>
</div>
<div class="stat-row">
    <div class="stat-card stat-total">
        <div class="stat-num">{total}</div>
        <div class="stat-label">전체 재료</div>
    </div>
    <div class="stat-card stat-warn">
        <div class="stat-num">{warn_count}</div>
        <div class="stat-label">주의 재료</div>
    </div>
    <div class="stat-card stat-danger">
        <div class="stat-num">{danger_count}</div>
        <div class="stat-label">위험 재료</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── 탭 ───────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["🥬  냉장고", "🍳  AI 레시피", "🔔  알림"])

# ════════════════════════════════════════════════════
# 탭1: 냉장고
# ════════════════════════════════════════════════════
with tab1:
    with st.expander("➕  재료 추가하기", expanded=False):
        input_tab1, input_tab2 = st.tabs(["✏️ 직접 입력", "📷 카메라 인식"])

        with input_tab1:
            with st.form("add_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    name     = st.text_input("재료 이름", placeholder="예: 당근")
                    quantity = st.text_input("수량/용량", placeholder="예: 2개, 300g")
                with col2:
                    category = st.selectbox("분류", list(CATEGORY_ICON.keys()))
                    expiry   = st.date_input("유통기한", value=datetime.now() + timedelta(days=7))
                if st.form_submit_button("냉장고에 넣기 🧊", use_container_width=True) and name:
                    st.session_state.ingredients.append({
                        "id":       datetime.now().strftime("%Y%m%d%H%M%S"),
                        "name":     name,
                        "quantity": quantity,
                        "category": category,
                        "expiry":   expiry.strftime("%Y-%m-%d"),
                        "added":    datetime.now().strftime("%Y-%m-%d"),
                    })
                    save_data(st.session_state.ingredients)
                    st.success(f"✅ '{name}' 추가 완료!")
                    st.rerun()

        with input_tab2:
            st.caption("냉장고 속 재료를 촬영하면 AI가 자동으로 인식해요!")
            if not st.session_state.api_key:
                st.warning("⚠️ 사이드바(☰)에서 Gemini API 키를 입력해야 인식이 가능해요!")
            camera_photo = st.camera_input("📷 사진 찍기")
            if camera_photo:
                if not st.session_state.api_key:
                    st.error("API 키를 먼저 사이드바(☰)에 입력해주세요!")
                else:
                    with st.spinner("🤖 AI가 재료를 분석하는 중..."):
                        try:
                            detected = recognize_ingredients_from_image(
                                camera_photo.getvalue(), st.session_state.api_key)
                            if not detected:
                                st.warning("식재료를 찾지 못했어요. 다시 찍어보세요!")
                            else:
                                st.success(f"✅ 재료 {len(detected)}개 인식 완료!")
                                default_expiry = datetime.now() + timedelta(days=7)
                                for i, item in enumerate(detected):
                                    with st.form(key=f"cam_{i}"):
                                        c1, c2, c3 = st.columns([3,2,2])
                                        with c1:
                                            iname = st.text_input("재료", value=item.get("name",""), key=f"n{i}")
                                            iqty  = st.text_input("수량", value=item.get("quantity","1개"), key=f"q{i}")
                                        with c2:
                                            cats = list(CATEGORY_ICON.keys())
                                            icat = st.selectbox("분류", cats,
                                                index=cats.index(item.get("category","기타")) if item.get("category","기타") in cats else 5,
                                                key=f"c{i}")
                                        with c3:
                                            iexp = st.date_input("유통기한", value=default_expiry, key=f"e{i}")
                                        if st.form_submit_button("➕ 추가", use_container_width=True):
                                            st.session_state.ingredients.append({
                                                "id":       datetime.now().strftime("%Y%m%d%H%M%S")+str(i),
                                                "name":     iname,
                                                "quantity": iqty,
                                                "category": icat,
                                                "expiry":   iexp.strftime("%Y-%m-%d"),
                                                "added":    datetime.now().strftime("%Y-%m-%d"),
                                            })
                                            save_data(st.session_state.ingredients)
                                            st.success(f"✅ '{iname}' 추가!")
                                            st.rerun()
                        except Exception as e:
                            st.error(f"인식 오류: {e}")

    # 재료 목록
    if not st.session_state.ingredients:
        st.markdown("""
        <div class="empty-fridge">
            <div class="icon">🧊</div>
            <div class="text">냉장고가 비어있어요!<br>재료를 추가해보세요</div>
        </div>""", unsafe_allow_html=True)
    else:
        sorted_items = sorted(st.session_state.ingredients,
                              key=lambda x: get_expiry_status(x.get("expiry",""))[2])

        # 위험/주의 먼저 표시
        danger_items = [i for i in sorted_items if get_expiry_status(i.get("expiry",""))[0]=="danger"]
        warn_items   = [i for i in sorted_items if get_expiry_status(i.get("expiry",""))[0]=="warning"]
        ok_items     = [i for i in sorted_items if get_expiry_status(i.get("expiry",""))[0]=="ok"]

        for group, label in [(danger_items,"🔴 지금 사용하세요"), (warn_items,"🟡 이번 주 안에"), (ok_items,"🟢 여유 있음")]:
            if not group: continue
            st.markdown(f'<div class="section-header">{label}</div>', unsafe_allow_html=True)
            for item in group:
                status, badge_label, _ = get_expiry_status(item.get("expiry",""))
                icon = CATEGORY_ICON.get(item.get("category","기타"), "🍽️")
                card_class = "ing-card" + (" warn" if status=="warning" else " danger" if status=="danger" else "")
                badge_class = "badge-warn" if status=="warning" else "badge-danger" if status=="danger" else "badge-ok"

                col1, col2 = st.columns([6, 1])
                with col1:
                    st.markdown(f"""
                    <div class="{card_class}">
                        <div class="ing-icon">{icon}</div>
                        <div class="ing-info">
                            <div class="ing-name">{item['name']}</div>
                            <div class="ing-meta">{item.get('quantity','-')} · {item.get('category','-')}</div>
                        </div>
                        <span class="ing-badge {badge_class}">{badge_label}</span>
                    </div>""", unsafe_allow_html=True)
                with col2:
                    if st.button("🗑️", key=f"del_{item['id']}"):
                        st.session_state.ingredients = [i for i in st.session_state.ingredients if i["id"]!=item["id"]]
                        save_data(st.session_state.ingredients)
                        st.rerun()

# ════════════════════════════════════════════════════
# 탭2: AI 레시피
# ════════════════════════════════════════════════════
with tab2:
    api_key = st.session_state.api_key

    if not api_key:
        st.markdown("#### 🔑 Gemini API 키 입력")
        st.caption("AI 레시피 기능을 사용하려면 API 키가 필요해요.")
        inline_key = st.text_input("API 키", type="password", placeholder="AIzaSy...", label_visibility="collapsed")
        if inline_key:
            st.session_state.api_key = inline_key
            st.success("✅ API 키 등록 완료! 잠시 후 새로고침됩니다.")
            st.rerun()
        st.info("💡 API 키 발급: aistudio.google.com/apikey (무료)")
    else:
        ingredients_summary = ", ".join([
            f"{i['name']}({i.get('quantity','')})"
            for i in st.session_state.ingredients
        ]) or "재료 없음"

        # 빠른 질문
        st.markdown('<div class="section-header">빠른 질문</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        quick_q = None
        with c1:
            if st.button("🍳 오늘 저녁 뭐 만들지?", use_container_width=True):
                quick_q = "오늘 저녁 뭐 만들면 좋을까?"
            if st.button("⚡ 10분 완성 요리는?", use_container_width=True):
                quick_q = "10분 안에 만들 수 있는 요리 알려줘"
        with c2:
            if st.button("🥗 다이어트 메뉴는?", use_container_width=True):
                quick_q = "다이어트에 좋은 메뉴 추천해줘"
            if st.button("🍱 냉장고 털기 요리?", use_container_width=True):
                quick_q = "임박한 재료 먼저 쓰는 요리 추천해줘"

        st.markdown("---")

        # 채팅 기록
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

        user_input = st.chat_input("무엇이든 물어보세요!")
        final_input = quick_q or user_input

        if final_input:
            system_prompt = f"""당신은 친절한 요리 AI 어시스턴트입니다.
현재 냉장고 재료: {ingredients_summary}

규칙:
1. 냉장고 재료를 최대한 활용한 레시피 추천
2. 유통기한 임박 재료 우선 사용
3. 초보자도 따라할 수 있게 쉽게 설명
4. 한국어로 답변
5. 이모지 적절히 사용"""

            st.session_state.chat_history.append({"role":"user","content":final_input})
            with st.chat_message("user"):
                st.write(final_input)
            with st.chat_message("assistant"):
                with st.spinner("AI가 레시피를 생각하는 중..."):
                    try:
                        model = get_gemini_model(api_key)
                        history_text = "\n".join([
                            f"{'사용자' if m['role']=='user' else 'AI'}: {m['content']}"
                            for m in st.session_state.chat_history[:-1]
                        ])
                        full_prompt = f"{system_prompt}\n\n이전 대화:\n{history_text}\n\n사용자: {final_input}\nAI:"
                        response = model.generate_content(full_prompt)
                        answer = response.text
                        st.write(answer)
                        st.session_state.chat_history.append({"role":"assistant","content":answer})
                    except Exception as e:
                        if "429" in str(e):
                            st.warning("⏳ AI 요청이 너무 많아요. 10초 후 다시 시도해주세요!")
                        elif "404" in str(e):
                            st.error("모델 오류가 발생했어요. 새로고침 후 다시 시도해주세요.")
                        else:
                            st.error(f"오류: {e}")

        if st.session_state.chat_history:
            if st.button("🔄 대화 초기화"):
                st.session_state.chat_history = []
                st.rerun()

# ════════════════════════════════════════════════════
# 탭3: 알림
# ════════════════════════════════════════════════════
with tab3:
    if not st.session_state.ingredients:
        st.markdown("""
        <div class="empty-fridge">
            <div class="icon">🔔</div>
            <div class="text">냉장고에 재료를 추가하면<br>유통기한을 알려드려요!</div>
        </div>""", unsafe_allow_html=True)
    else:
        all_items = sorted(st.session_state.ingredients,
                           key=lambda x: get_expiry_status(x.get("expiry",""))[2])

        danger_items = [i for i in all_items if get_expiry_status(i.get("expiry",""))[0]=="danger"]
        warn_items   = [i for i in all_items if get_expiry_status(i.get("expiry",""))[0]=="warning"]
        ok_items     = [i for i in all_items if get_expiry_status(i.get("expiry",""))[0]=="ok"]

        for group, css, header in [
            (danger_items, "alert-danger", "🔴 지금 당장 사용하세요!"),
            (warn_items,   "alert-warn",   "🟡 이번 주 안에 사용하세요"),
            (ok_items,     "alert-ok",     "🟢 여유 있는 재료"),
        ]:
            if not group: continue
            st.markdown(f'<div class="section-header">{header}</div>', unsafe_allow_html=True)
            for item in group:
                _, badge_label, _ = get_expiry_status(item.get("expiry",""))
                icon = CATEGORY_ICON.get(item.get("category","기타"), "🍽️")
                st.markdown(f"""
                <div class="alert-card {css}">
                    <div class="alert-icon">{icon}</div>
                    <div>
                        <div class="alert-name">{item['name']}</div>
                        <div class="alert-sub">{badge_label} · {item.get('quantity','-')}</div>
                    </div>
                </div>""", unsafe_allow_html=True)

        # 하단 요약
        st.markdown("---")
        c1, c2, c3 = st.columns(3)
        c1.metric("전체", f"{len(all_items)}개")
        c2.metric("주의", f"{len(warn_items)}개")
        c3.metric("위험", f"{len(danger_items)}개")
