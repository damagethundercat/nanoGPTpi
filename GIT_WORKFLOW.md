# 🔄 Git 워크플로우 가이드

Windows에서 개발하고 라즈베리파이에서 배포하는 완전한 워크플로우입니다.

## 🎯 목표: 코드 수정 없이 배포

**Windows (개발환경)** → **GitHub** → **라즈베리파이 (배포환경)**

---

## 1️⃣ 초기 Git 설정 (Windows에서)

### Git 저장소 초기화
```bash
# 프로젝트 루트에서
git init
git add .
git commit -m "Initial piGPT setup for Raspberry Pi 5"
```

### GitHub 저장소 생성 & 연결
```bash
# GitHub에서 새 저장소 생성 후
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git branch -M main
git push -u origin main
```

---

## 2️⃣ 개발 워크플로우 (Windows)

### 기능 개발/수정
```bash
# 현재 piGPT 폴더에서 작업
cd piGPT

# 코드 수정 (예: run_echoes_workflow.py)
# - 새로운 기능 추가
# - 프롬프트 엔지니어링 개선
# - 버그 수정 등

# 변경사항 확인
git status
git diff
```

### 커밋 & 푸시
```bash
# 변경된 파일 추가
git add .

# 의미있는 커밋 메시지
git commit -m "feat: 새로운 프롬프트 엔지니어링 로직 추가"

# GitHub에 푸시
git push origin main
```

---

## 3️⃣ 라즈베리파이 배포

### 초기 설치 (최초 1회만)
```bash
# 원클릭 설치
curl -sSL https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/piGPT/setup_pi.sh | bash
```

### 업데이트 (개발 후)
```bash
# 라즈베리파이에서
cd ~/YOUR_REPO/piGPT

# 최신 코드 받기
git pull origin main

# 가상환경 활성화
source venv_pigpt/bin/activate

# 새 의존성이 있다면
pip install --prefer-binary -r requirements_pi.txt

# 바로 실행
python run_echoes_workflow.py
```

---

## 4️⃣ 브랜치 전략 (고급)

### 개발 브랜치 사용
```bash
# 새 기능 개발시
git checkout -b feature/new-prompt-engineering
# 개발 작업...
git commit -m "feat: 새로운 기능 구현"
git push origin feature/new-prompt-engineering

# GitHub에서 Pull Request 생성
# 리뷰 후 main에 merge
```

### 라즈베리파이에서 특정 브랜치 테스트
```bash
# 라즈베리파이에서
cd ~/YOUR_REPO/piGPT
git fetch
git checkout feature/new-prompt-engineering
python run_echoes_workflow.py
```

---

## 5️⃣ 모델 파일 관리

### .gitignore 설정
```gitignore
# piGPT/.gitignore
models/ckpt.pt
models/*.pkl
models/*.model
venv_pigpt/
__pycache__/
*.pyc
.env
```

### 모델 파일 동기화 방법

**옵션 1: SCP 사용**
```bash
# Windows → 라즈베리파이
scp models/ckpt.pt pi@raspberrypi.local:~/YOUR_REPO/piGPT/models/
scp models/meta.pkl pi@raspberrypi.local:~/YOUR_REPO/piGPT/models/
scp models/*.model pi@raspberrypi.local:~/YOUR_REPO/piGPT/models/
```

**옵션 2: Git LFS 사용 (권장)**
```bash
# 대용량 파일 추적
git lfs track "*.pt"
git lfs track "*.pkl"
git lfs track "*.model"

git add .gitattributes
git add models/
git commit -m "Add model files with Git LFS"
git push origin main
```

**옵션 3: 클라우드 스토리지**
```bash
# Google Drive, Dropbox 등에 업로드 후
# 라즈베리파이에서 직접 다운로드
wget "https://drive.google.com/uc?id=FILE_ID" -O models/ckpt.pt
```

---

## 6️⃣ 자동화 스크립트

### 개발→배포 자동화 (Windows)
```bash
# deploy.bat 생성
@echo off
echo Pushing to GitHub...
git add .
git commit -m "Auto deploy: %date% %time%"
git push origin main

echo Connecting to Raspberry Pi...
ssh pi@raspberrypi.local "cd ~/YOUR_REPO/piGPT && git pull origin main"
echo Deployment completed!
```

### 라즈베리파이 업데이트 스크립트
```bash
# update_pigpt.sh
#!/bin/bash
cd ~/YOUR_REPO/piGPT
echo "🔄 Updating piGPT..."
git pull origin main
source venv_pigpt/bin/activate
pip install --prefer-binary -r requirements_pi.txt
echo "✅ Update completed!"
echo "🚀 Starting piGPT..."
python run_echoes_workflow.py
```

---

## 7️⃣ 환경 분리 설정

### 환경별 설정 파일
```python
# config.py
import os

# 환경 감지
IS_RASPBERRY_PI = os.uname().machine in ['armv7l', 'aarch64']

if IS_RASPBERRY_PI:
    # 라즈베리파이 설정
    DEVICE = "cpu"
    MAX_NEW_TOKENS = 50  # 더 빠른 생성
    TEMPERATURE = 0.7
else:
    # Windows 개발환경 설정
    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
    MAX_NEW_TOKENS = 150
    TEMPERATURE = 0.8
```

---

## 8️⃣ 문제 해결

### Git 충돌 해결
```bash
# 라즈베리파이에서 로컬 변경사항이 있을 때
git stash  # 임시 저장
git pull origin main  # 최신 코드 받기
git stash pop  # 임시 저장 복원
```

### SSH 키 설정 (편의성)
```bash
# Windows에서 SSH 키 생성
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"

# 라즈베리파이에 키 복사
ssh-copy-id pi@raspberrypi.local

# 이제 패스워드 없이 접속 가능
ssh pi@raspberrypi.local
```

---

## 🎉 완전 자동화 워크플로우

**최종 목표 달성:**

1. **Windows에서 개발** ✅
2. **Git 푸시** ✅
3. **라즈베리파이에서 한 줄 명령어로 업데이트** ✅
4. **코드 수정 없이 바로 실행** ✅

```bash
# 라즈베리파이에서 이것만 하면 끝!
bash update_pigpt.sh
```

더 이상 라즈베리파이에서 코드를 수정할 필요가 없습니다! 🚀