#!/bin/bash

# 스마트 냉장고 AI 앱 실행기
export PATH="$PATH:/Users/iuseog/Library/Python/3.9/bin"

echo "🧊 스마트 냉장고 AI 시작 중..."
echo ""

# 앱 폴더로 이동
cd /Users/iuseog/홈피관련/경운대학교/sw/fridge-agent

# 기존에 실행 중인 앱 종료
pkill -f "streamlit run app.py" 2>/dev/null
sleep 1

echo "✅ 브라우저가 자동으로 열립니다..."
echo "   종료하려면 이 창을 닫으세요."
echo ""

# 앱 실행
streamlit run app.py \
  --server.port 8501 \
  --browser.gatherUsageStats false \
  --server.headless false
