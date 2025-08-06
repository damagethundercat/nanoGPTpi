#!/bin/bash
# piGPT 라즈베리파이 업데이트 스크립트
# 사용법: bash update_pigpt.sh

set -e  # 오류 발생시 중단

echo "🔄 piGPT 업데이트를 시작합니다..."

# 현재 디렉토리 확인
if [ ! -f "run_echoes_workflow.py" ]; then
    echo "❌ piGPT 디렉토리가 아닙니다. 올바른 경로로 이동해주세요."
    echo "   예: cd ~/YOUR_REPO/piGPT"
    exit 1
fi

# 1. Git 상태 확인
echo "📦 Git 상태 확인 중..."
if [ -n "$(git status --porcelain)" ]; then
    echo "⚠️  로컬 변경사항이 있습니다. 백업 중..."
    git stash push -m "Auto backup before update $(date)"
fi

# 2. 최신 코드 받기
echo "⬇️  최신 코드 다운로드 중..."
git fetch origin
git pull origin main

# 3. 가상환경 활성화
echo "🐍 가상환경 활성화 중..."
if [ ! -d "venv_pigpt" ]; then
    echo "❌ 가상환경이 없습니다. 초기 설치를 먼저 실행해주세요:"
    echo "   bash setup_pi.sh"
    exit 1
fi

source venv_pigpt/bin/activate

# 4. 의존성 업데이트 (필요시)
if git diff HEAD~1 HEAD --name-only | grep -q "requirements_pi.txt"; then
    echo "📚 의존성 업데이트 중..."
    pip install --prefer-binary -r requirements_pi.txt
else
    echo "📚 의존성 변경사항 없음 (건너뛰기)"
fi

# 5. 모델 파일 확인
echo "🧠 모델 파일 확인 중..."
missing_files=()

if [ ! -f "models/ckpt.pt" ]; then
    missing_files+=("ckpt.pt")
fi
if [ ! -f "models/meta.pkl" ]; then
    missing_files+=("meta.pkl")
fi
if [ -z "$(ls models/*.model 2>/dev/null)" ]; then
    missing_files+=("*.model")
fi

if [ ${#missing_files[@]} -gt 0 ]; then
    echo "⚠️  다음 모델 파일이 없습니다: ${missing_files[*]}"
    echo "   모델 파일을 models/ 폴더에 복사해주세요."
    echo ""
    echo "   예시:"
    echo "   scp user@pc:/path/to/ckpt.pt models/"
    echo "   scp user@pc:/path/to/meta.pkl models/"
    echo "   scp user@pc:/path/to/*.model models/"
    echo ""
    read -p "계속하시겠습니까? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ 업데이트를 취소합니다."
        exit 1
    fi
fi

# 6. Gemini API 키 확인
echo "🔑 Gemini API 키 확인 중..."
if grep -q "YOUR_GEMINI_API_KEY\|AIzaSyBMcS5oe_-A6eZ8JXTdRbvZ4waMH2VdXIs" run_echoes_workflow.py; then
    echo "⚠️  Gemini API 키가 기본값으로 설정되어 있습니다."
    echo "   run_echoes_workflow.py 파일에서 GEMINI_API_KEY를 수정해주세요."
    echo ""
fi

# 7. 권한 설정
echo "🔑 실행 권한 설정 중..."
chmod +x run_echoes_workflow.py
chmod +x sample.py
chmod +x *.sh

# 8. 완료 메시지
echo ""
echo "✅ piGPT 업데이트가 완료되었습니다!"
echo ""
echo "🚀 실행하기:"
echo "   python run_echoes_workflow.py"
echo ""
echo "📊 시스템 정보:"
echo "   Python: $(python --version)"
echo "   PyTorch: $(python -c 'import torch; print(torch.__version__)' 2>/dev/null || echo 'Not installed')"
echo "   디바이스: $(python -c 'import torch; print("cuda" if torch.cuda.is_available() else "cpu")' 2>/dev/null || echo 'cpu')"
echo "   메모리: $(free -h | awk '/^Mem:/ {print $2}' || echo 'Unknown')"
echo ""

# 9. 실행 여부 선택
read -p "🎯 지금 piGPT를 실행하시겠습니까? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 piGPT 시작 중..."
    python run_echoes_workflow.py
else
    echo "👋 나중에 실행하려면: python run_echoes_workflow.py"
fi