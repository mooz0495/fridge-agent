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

# ── CSS (모바일 친화적 스타일) ──────────────────────────
st.markdown("""
<style>
    .main { max-width: 480px; margin: 0 auto; }
    .ingredient-card {
        background: #f8f9fa;
        border-radius: 12px;
        padding: 12px 16px;
        margin: 6px 0;
        border-left: 4px solid #4CAF50;
    }
    .ingredient-card.warning {
        border-left-color: #FF9800;
        background: #fff8e1;
    }
    .ingredient-card.danger {
        border-left-color: #f44336;
        background: #ffebee;
    }
    .badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: bold;
    }
    .badge-ok { background: #e8f5e9; color: #2e7d32; }
    .badge-warn { background: #fff3e0; color: #e65100; }
    .badge-danger { background: #ffebee; color: #c62828; }
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
            return "danger", f"D+{abs(days_left)} 만료", days_left
        elif days_left <= 2:
            return "danger", f"D-{days_left} 위험!", days_left
        elif days_left <= 5:
            return "warning", f"D-{days_left} 주의", days_left
        else:
            return "ok", f"D-{days_left}", days_left
    except:
        return "ok", "날짜오류", 999

# ── Gemini AI 초기화 ──────────────────────────────────
def get_gemini_model(api_key: str, vision: bool = False):
    genai.configure(api_key=api_key)
    model_name = "gemini-1.5-flash" if vision else "gemini-1.5-flash"
    return genai.GenerativeModel(model_name)

# ── 카메라로 재료 인식 ────────────────────────────────
def recognize_ingredients_from_image(image_bytes: bytes, api_key: str) -> list:
    model = get_gemini_model(api_key, vision=True)
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

# ── 세션 상태 초기화 ──────────────────────────────────
if "ingredients" not in st.session_state:
    st.session_state.ingredients = load_data()
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "냉장고"
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

# ── 헤더 ─────────────────────────────────────────────
st.markdown("# 🧊 스마트 냉장고 AI")

# API 키 전역 입력 (한 번만)
with st.sidebar:
    st.markdown("### ⚙️ 설정")
    api_input = st.text_input("Claude API 키", type="password",
                               value=st.session_state.api_key,
                               placeholder="sk-ant-api...")
    if api_input:
        st.session_state.api_key = api_input
        st.success("✅ API 키 등록됨")

st.markdown("---")

# ── 탭 ───────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["🥬 냉장고", "🍳 AI 레시피", "⚠️ 알림"])

# ════════════════════════════════════════════════════
# 탭1: 냉장고 (재료 관리)
# ════════════════════════════════════════════════════
with tab1:
    st.subheader("내 냉장고")

    # 재료 추가 섹션
    with st.expander("➕ 재료 추가", expanded=False):
        input_tab1, input_tab2 = st.tabs(["✏️ 직접 입력", "📷 카메라 인식"])

        # ── 직접 입력 탭 ──────────────────────────────
        with input_tab1:
            with st.form("add_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    name = st.text_input("재료 이름", placeholder="예: 당근")
                    quantity = st.text_input("수량/용량", placeholder="예: 2개, 300g")
                with col2:
                    category = st.selectbox("분류", ["채소/과일", "육류/수산", "유제품/계란", "가공식품", "조미료/소스", "기타"])
                    expiry = st.date_input("유통기한", value=datetime.now() + timedelta(days=7))

                submitted = st.form_submit_button("냉장고에 넣기 🧊", use_container_width=True)
                if submitted and name:
                    new_item = {
                        "id": datetime.now().strftime("%Y%m%d%H%M%S"),
                        "name": name,
                        "quantity": quantity,
                        "category": category,
                        "expiry": expiry.strftime("%Y-%m-%d"),
                        "added": datetime.now().strftime("%Y-%m-%d"),
                    }
                    st.session_state.ingredients.append(new_item)
                    save_data(st.session_state.ingredients)
                    st.success(f"✅ '{name}' 추가 완료!")
                    st.rerun()

        # ── 카메라 인식 탭 ────────────────────────────
        with input_tab2:
            if not st.session_state.api_key:
                st.warning("왼쪽 사이드바(☰)에서 Claude API 키를 먼저 입력해주세요!")
            else:
                st.markdown("**냉장고 속 재료를 촬영하면 AI가 자동으로 인식해요!**")
                camera_photo = st.camera_input("📷 사진 찍기")

                if camera_photo is not None:
                    with st.spinner("🤖 AI가 재료를 인식하는 중..."):
                        try:
                            detected = recognize_ingredients_from_image(
                                camera_photo.getvalue(),
                                st.session_state.api_key
                            )

                            if not detected:
                                st.warning("식재료를 찾지 못했어요. 다시 찍어보세요!")
                            else:
                                st.success(f"✅ 재료 {len(detected)}개를 찾았어요!")
                                st.markdown("**인식된 재료 목록** (유통기한을 확인 후 추가하세요)")

                                default_expiry = datetime.now() + timedelta(days=7)

                                for i, item in enumerate(detected):
                                    with st.form(key=f"cam_form_{i}"):
                                        col1, col2, col3 = st.columns([3, 2, 2])
                                        with col1:
                                            item_name = st.text_input(
                                                "재료", value=item.get("name", ""),
                                                key=f"cam_name_{i}"
                                            )
                                            item_qty = st.text_input(
                                                "수량", value=item.get("quantity", "1개"),
                                                key=f"cam_qty_{i}"
                                            )
                                        with col2:
                                            item_cat = st.selectbox(
                                                "분류",
                                                ["채소/과일", "육류/수산", "유제품/계란", "가공식품", "조미료/소스", "기타"],
                                                index=["채소/과일", "육류/수산", "유제품/계란", "가공식품", "조미료/소스", "기타"].index(
                                                    item.get("category", "기타")
                                                ) if item.get("category", "기타") in ["채소/과일", "육류/수산", "유제품/계란", "가공식품", "조미료/소스", "기타"] else 5,
                                                key=f"cam_cat_{i}"
                                            )
                                        with col3:
                                            item_expiry = st.date_input(
                                                "유통기한",
                                                value=default_expiry,
                                                key=f"cam_exp_{i}"
                                            )
                                        if st.form_submit_button(f"➕ 추가", use_container_width=True):
                                            new_item = {
                                                "id": datetime.now().strftime("%Y%m%d%H%M%S") + str(i),
                                                "name": item_name,
                                                "quantity": item_qty,
                                                "category": item_cat,
                                                "expiry": item_expiry.strftime("%Y-%m-%d"),
                                                "added": datetime.now().strftime("%Y-%m-%d"),
                                            }
                                            st.session_state.ingredients.append(new_item)
                                            save_data(st.session_state.ingredients)
                                            st.success(f"✅ '{item_name}' 추가 완료!")
                                            st.rerun()

                        except Exception as e:
                            st.error(f"인식 오류: {e}")

    # 재료 목록 표시
    if not st.session_state.ingredients:
        st.info("냉장고가 비어있어요! 재료를 추가해보세요 🥬")
    else:
        # 유통기한 임박순으로 정렬
        sorted_ingredients = sorted(
            st.session_state.ingredients,
            key=lambda x: get_expiry_status(x.get("expiry", ""))[2]
        )

        # 요약 통계
        total = len(sorted_ingredients)
        danger_count = sum(1 for item in sorted_ingredients if get_expiry_status(item.get("expiry", ""))[0] == "danger")
        warn_count = sum(1 for item in sorted_ingredients if get_expiry_status(item.get("expiry", ""))[0] == "warning")

        col1, col2, col3 = st.columns(3)
        col1.metric("전체 재료", f"{total}개")
        col2.metric("⚠️ 주의", f"{warn_count}개")
        col3.metric("🔴 위험", f"{danger_count}개")

        st.markdown("---")

        # 재료 카드 출력
        for item in sorted_ingredients:
            status, label, _ = get_expiry_status(item.get("expiry", ""))
            badge_class = f"badge-{status if status != 'ok' else 'ok'}"
            card_class = "ingredient-card" + (" warning" if status == "warning" else " danger" if status == "danger" else "")

            col1, col2 = st.columns([5, 1])
            with col1:
                st.markdown(f"""
                <div class="{card_class}">
                    <strong>{item['name']}</strong>
                    &nbsp; <span class="badge {badge_class}">{label}</span><br>
                    <small>📦 {item.get('quantity', '-')} &nbsp;|&nbsp; 🏷️ {item.get('category', '-')}</small>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                if st.button("🗑️", key=f"del_{item['id']}", help="삭제"):
                    st.session_state.ingredients = [
                        i for i in st.session_state.ingredients if i["id"] != item["id"]
                    ]
                    save_data(st.session_state.ingredients)
                    st.rerun()

# ════════════════════════════════════════════════════
# 탭2: AI 레시피 채팅
# ════════════════════════════════════════════════════
with tab2:
    st.subheader("AI 레시피 추천")

    api_key = st.session_state.api_key

    if not api_key:
        st.info("💡 왼쪽 사이드바(☰)에서 API 키를 입력하면 AI 레시피를 추천받을 수 있어요!")
    else:
        # 채팅 기록 표시
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

        # 현재 냉장고 재료 요약
        if st.session_state.ingredients:
            ingredients_summary = ", ".join([
                f"{item['name']}({item.get('quantity','')})"
                for item in st.session_state.ingredients
            ])
        else:
            ingredients_summary = "현재 재료 없음"

        # 빠른 질문 버튼
        st.markdown("**빠른 질문:**")
        col1, col2 = st.columns(2)
        quick_q = None
        with col1:
            if st.button("🍳 오늘 저녁 뭐 만들지?", use_container_width=True):
                quick_q = "오늘 저녁 뭐 만들면 좋을까?"
            if st.button("⚡ 10분 완성 요리는?", use_container_width=True):
                quick_q = "10분 안에 만들 수 있는 요리 알려줘"
        with col2:
            if st.button("🥗 다이어트 메뉴는?", use_container_width=True):
                quick_q = "다이어트에 좋은 메뉴 추천해줘"
            if st.button("🍱 냉장고 털기 요리?", use_container_width=True):
                quick_q = "임박한 재료 먼저 쓰는 요리 추천해줘"

        # 채팅 입력
        user_input = st.chat_input("무엇이든 물어보세요! 예: 오늘 저녁 뭐 먹지?")
        final_input = quick_q or user_input

        if final_input:
            # 시스템 프롬프트 구성
            system_prompt = f"""당신은 친절한 요리 AI 어시스턴트입니다.
사용자의 냉장고에 현재 다음 재료들이 있습니다: {ingredients_summary}

중요 규칙:
1. 냉장고에 있는 재료를 최대한 활용한 레시피를 추천하세요
2. 유통기한이 임박한 재료를 우선 사용하는 레시피를 우선 추천하세요
3. 레시피는 초보자도 따라할 수 있게 쉽고 간단하게 설명하세요
4. 재료가 부족하면 솔직하게 말하고 대안을 제시하세요
5. 한국어로 답변하세요
6. 이모지를 적절히 사용해 읽기 쉽게 작성하세요"""

            # 사용자 메시지 추가
            st.session_state.chat_history.append({"role": "user", "content": final_input})

            with st.chat_message("user"):
                st.write(final_input)

            # AI 응답 생성 (Gemini)
            with st.chat_message("assistant"):
                with st.spinner("AI가 레시피를 생각하는 중...🤔"):
                    try:
                        model = get_gemini_model(api_key)
                        # 대화 히스토리 포함해서 전송
                        history_text = "\n".join([
                            f"{'사용자' if m['role']=='user' else 'AI'}: {m['content']}"
                            for m in st.session_state.chat_history[:-1]
                        ])
                        full_prompt = f"{system_prompt}\n\n이전 대화:\n{history_text}\n\n사용자: {final_input}\nAI:"
                        response = model.generate_content(full_prompt)
                        answer = response.text
                        st.write(answer)
                        st.session_state.chat_history.append({"role": "assistant", "content": answer})
                    except Exception as e:
                        st.error(f"오류 발생: {e}")

        # 대화 초기화 버튼
        if st.session_state.chat_history:
            if st.button("🔄 대화 초기화"):
                st.session_state.chat_history = []
                st.rerun()

# ════════════════════════════════════════════════════
# 탭3: 유통기한 알림
# ════════════════════════════════════════════════════
with tab3:
    st.subheader("유통기한 알림")

    if not st.session_state.ingredients:
        st.info("냉장고에 재료를 추가하면 유통기한을 관리할 수 있어요!")
    else:
        danger_items = []
        warning_items = []
        ok_items = []

        for item in st.session_state.ingredients:
            status, label, days = get_expiry_status(item.get("expiry", ""))
            item_info = {**item, "label": label, "days": days}
            if status == "danger":
                danger_items.append(item_info)
            elif status == "warning":
                warning_items.append(item_info)
            else:
                ok_items.append(item_info)

        # 위험 재료
        if danger_items:
            st.markdown("### 🔴 지금 당장 사용하세요!")
            for item in sorted(danger_items, key=lambda x: x["days"]):
                st.error(f"**{item['name']}** — {item['label']} ({item.get('quantity', '')})")

        # 주의 재료
        if warning_items:
            st.markdown("### 🟡 이번 주 안에 사용하세요")
            for item in sorted(warning_items, key=lambda x: x["days"]):
                st.warning(f"**{item['name']}** — {item['label']} ({item.get('quantity', '')})")

        # 양호 재료
        if ok_items:
            st.markdown("### 🟢 여유 있는 재료")
            for item in sorted(ok_items, key=lambda x: x["days"]):
                st.success(f"**{item['name']}** — {item['label']} ({item.get('quantity', '')})")

        # 요약
        st.markdown("---")
        st.markdown(f"""
        **📊 냉장고 현황**
        - 전체: {len(st.session_state.ingredients)}개
        - 🔴 위험: {len(danger_items)}개
        - 🟡 주의: {len(warning_items)}개
        - 🟢 양호: {len(ok_items)}개
        """)
