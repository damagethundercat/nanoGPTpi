# 🚀 piGPT - Raspberry Pi 5 Edition

라즈베리파이5에서 실행되는 경량화된 nanoGPT + Gemini API 워크플로우입니다.

## 📋 시스템 요구사항

- **Raspberry Pi 5** (ARMv8 아키텍처)
- **Python 3.11** (중요: 3.13은 호환성 문제 있음)
- **최소 4GB RAM** 권장
- **인터넷 연결** (Gemini API 사용)
- **Git** 설치됨

## ⚡ 원클릭 자동 설치

라즈베리파이에서 터미널을 열고 다음 **한 줄**만 실행하세요:

```bash
curl -sSL https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/piGPT/setup_pi.sh | bash
```

> ⚠️ **중요**: 위 명령어는 GitHub에 업로드 후 실제 저장소 URL로 수정해서 사용하세요.

---

## 🔧 수동 설치 (단계별)

자동 설치가 실패하거나 수동으로 하고 싶다면:

### 1️⃣ 시스템 패키지 업데이트
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.11 python3.11-venv python3.11-dev \
    build-essential cmake pkg-config git curl wget \
    libblas-dev liblapack-dev libopenblas-dev
```

### 2️⃣ piGPT 다운로드
```bash
cd ~
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO/piGPT
```

### 3️⃣ Python 3.11 가상환경 생성
```bash
python3.11 -m venv venv_pigpt
source venv_pigpt/bin/activate
pip install --upgrade pip
```

### 4️⃣ PyTorch CPU 버전 설치 (라즈베리파이 최적화)
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

### 5️⃣ 나머지 의존성 설치
```bash
pip install --prefer-binary -r requirements_pi.txt
```

---

## 🧠 모델 파일 설정

`models/` 폴더에 다음 파일들이 필요합니다:

| 파일 | 설명 | 크기(예상) |
|------|------|-----------|
| `ckpt.pt` | 훈련된 nanoGPT 모델 | ~48MB |
| `meta.pkl` | 메타데이터 파일 | ~1KB |
| `*.model` | SentencePiece BPE 모델 | ~1MB |

**모델 파일이 없다면:**
```bash
# 원본 nanoGPT에서 복사하거나 별도 다운로드 필요
# 예시 (Windows에서 라즈베리파이로):
scp user@your-pc:/path/to/nanoGPT/out-*/ckpt.pt ~/YOUR_REPO/piGPT/models/
scp user@your-pc:/path/to/nanoGPT/data/*/meta.pkl ~/YOUR_REPO/piGPT/models/
scp user@your-pc:/path/to/nanoGPT/data/*/*.model ~/YOUR_REPO/piGPT/models/
```

---

## 🔑 Gemini API 키 설정

`run_echoes_workflow.py` 파일에서 API 키를 수정하세요:

```python
# 44번째 줄 근처
GEMINI_API_KEY = "AIzaSyBMcS5oe_-A6eZ8JXTdRbvZ4waMH2VdXIs"  # 실제 키로 교체
```

**또는 환경변수로 설정:**
```bash
export GEMINI_API_KEY="your_actual_api_key"
```

---

## 🎯 사용 방법

### 1️⃣ piGPT 실행
```bash
cd ~/YOUR_REPO/piGPT
source venv_pigpt/bin/activate
python run_echoes_workflow.py
```

### 2️⃣ 프롬프트 입력
```
piGPT 준비 완료 (device: cpu)
프롬프트를 입력하세요 (exit/quit 종료): 안녕하세요
```

### 3️⃣ 결과 확인
- nanoGPT가 토큰별로 텍스트 생성
- Gemini API가 자연스럽게 교정
- 최종 결과 출력

---

## 🛠️ 문제 해결

### Python 버전 문제
```bash
# Python 3.11 확인
python3.11 --version

# 기본 python3를 3.11로 설정
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
```

### 패키지 설치 오류
```bash
# CMake 관련 오류시
sudo apt install cmake build-essential

# 메모리 부족시
sudo dphys-swapfile swapoff
sudo dphys-swapfile swapon
```

### 모델 로딩 오류
```bash
# 모델 파일 권한 확인
ls -la models/
chmod 644 models/*
```

---

## ✨ 주요 특징

- ✅ **CPU 전용 실행** (CUDA 불필요)
- ✅ **자동 디바이스 감지** (cuda → cpu fallback)
- ✅ **경량화된 의존성** (라즈베리파이 최적화)
- ✅ **Gemini API 통합** (텍스트 교정)
- ✅ **스트리밍 모드** (안정적인 응답)
- ✅ **깔끔한 출력** (디버그 코드 주석처리)

---

## 📊 성능 정보

**라즈베리파이5에서 예상 성능:**
- **모델 로딩**: ~5-10초
- **토큰당 생성**: ~0.5-1초
- **Gemini 교정**: ~2-3초
- **메모리 사용**: ~1-2GB

---

## 🔄 업데이트

GitHub에서 최신 버전으로 업데이트:

```bash
cd ~/YOUR_REPO/piGPT
git pull origin main
source venv_pigpt/bin/activate
pip install --prefer-binary -r requirements_pi.txt
```

---

## 📁 프로젝트 구조

```
piGPT/
├── run_echoes_workflow.py    # 메인 워크플로우 (CPU 자동 전환)
├── sample.py                 # 텍스트 생성 래퍼 (nanoGPT 모델 사용)
├── models/                   # 모델 파일 위치
│   ├── ckpt.pt              # nanoGPT 체크포인트
│   ├── meta.pkl             # 메타데이터
│   └── *.model              # SentencePiece BPE 모델
├── requirements_pi.txt       # 라즈베리파이 최적화 의존성
├── setup_pi.sh              # 원클릭 설치 스크립트
├── build_piGPT.py           # 모델 파일 복사 유틸리티
└── README_pi.md             # 이 문서
```

---

## 🆘 지원

문제가 발생하면 GitHub Issues에 다음 정보와 함께 보고해주세요:

```bash
# 시스템 정보
uname -a
python3.11 --version
pip list | grep -E "(torch|sentencepiece|google-generativeai)"

# 오류 로그
python run_echoes_workflow.py 2>&1 | tee error.log
```

---

## 🤝 개발 워크플로우

**Windows에서 개발 → 라즈베리파이 배포:**

1. Windows에서 piGPT 폴더 수정/테스트
2. Git에 커밋 & 푸시
3. 라즈베리파이에서 `git pull` 후 바로 사용

**코드 수정 없이 라즈베리파이에서 바로 실행 가능!** 🎉