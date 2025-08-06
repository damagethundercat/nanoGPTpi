#!/bin/bash
# piGPT 라즈베리파이5 원클릭 설치 스크립트
# 사용법: curl -sSL https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/piGPT/setup_pi.sh | bash

set -e  # 오류 발생시 중단

echo "🚀 piGPT 라즈베리파이5 설치를 시작합니다..."

# 1. 시스템 업데이트
echo "📦 시스템 패키지 업데이트 중..."
sudo apt update && sudo apt upgrade -y

# 2. 필수 의존성 설치
echo "🔧 필수 패키지 설치 중..."
sudo apt install -y python3.11 python3.11-venv python3.11-dev \
    build-essential cmake pkg-config \
    git curl wget \
    libblas-dev liblapack-dev libopenblas-dev \
    libffi-dev libssl-dev

# 3. Python 3.11이 기본이 되도록 설정
echo "🐍 Python 3.11 설정 중..."
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
sudo apt install -y python3-pip

# 4. piGPT 다운로드 (Git 클론)
echo "📥 piGPT 소스코드 다운로드 중..."
cd ~
if [ -d "piGPT" ]; then
    echo "기존 piGPT 폴더 제거 중..."
    rm -rf piGPT
fi
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO/piGPT

# 5. Python 3.11 가상환경 생성
echo "🏠 Python 3.11 가상환경 생성 중..."
python3.11 -m venv venv_pigpt
source venv_pigpt/bin/activate

# 6. pip 업그레이드
echo "⬆️ pip 업그레이드 중..."
pip install --upgrade pip

# 7. PyTorch CPU 버전 먼저 설치 (라즈베리파이 최적화)
echo "🔥 PyTorch CPU 버전 설치 중..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# 8. 나머지 의존성 설치 (바이너리 우선)
echo "📚 나머지 패키지 설치 중..."
pip install --prefer-binary -r requirements_pi.txt

# 9. 모델 파일 다운로드 확인
echo "🧠 모델 파일 확인 중..."
if [ ! -f "models/ckpt.pt" ]; then
    echo "⚠️  모델 파일이 없습니다. GitHub LFS 또는 별도 다운로드가 필요합니다."
    echo "   모델 파일을 수동으로 models/ 폴더에 복사해주세요:"
    echo "   - ckpt.pt"
    echo "   - meta.pkl"
    echo "   - *.model (SentencePiece 파일)"
fi

# 10. 권한 설정
echo "🔑 실행 권한 설정 중..."
chmod +x run_echoes_workflow.py
chmod +x sample.py

# 11. 완료 메시지
echo ""
echo "✅ piGPT 설치가 완료되었습니다!"
echo ""
echo "🎯 사용 방법:"
echo "   cd ~/YOUR_REPO/piGPT"
echo "   source venv_pigpt/bin/activate"
echo "   python run_echoes_workflow.py"
echo ""
echo "🔧 Gemini API 키 설정:"
echo "   run_echoes_workflow.py 파일의 GEMINI_API_KEY 수정 필요"
echo ""
echo "📁 모델 파일이 없다면:"
echo "   models/ 폴더에 ckpt.pt, meta.pkl, *.model 파일 복사"
echo ""