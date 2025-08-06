import os
import shutil
from pathlib import Path

"""
자동 구성 스크립트
==================
piGPT 폴더 내부에 모델(checkpoint) 및 SentencePiece 메타 파일을 복사하여
라즈베리파이 등 독립적인 환경에서 nanoGPT 추론을 실행할 수 있도록 준비합니다.

1. nanoGPT/out-parannoul-bpe/ckpt.pt  ->  piGPT/out-parannoul-bpe/ckpt.pt
2. nanoGPT/out-parannoul-bpe/meta.pkl (있을 경우) -> 동일 위치
3. nanoGPT/data/parannoul/* (meta.pkl, *.model) -> piGPT/data/parannoul/

원본 파일이 없을 경우 오류를 출력하지만 실행은 계속됩니다.
"""

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_NANO_GPT = PROJECT_ROOT / "nanoGPT"
DST_PIGPT = PROJECT_ROOT / "piGPT"

MODEL_DIR_NAME = "models"
DATA_DIR_NAME = "parannoul"

SRC_MODEL_DIR = SRC_NANO_GPT / "out-parannoul-bpe"
DST_MODEL_DIR = DST_PIGPT / MODEL_DIR_NAME

SRC_DATA_DIR = SRC_NANO_GPT / "data" / DATA_DIR_NAME
DST_DATA_DIR = DST_MODEL_DIR


def copy_file(src: Path, dst: Path):
    if not src.exists():
        print(f"[WARN] Source not found: {src}")
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    print(f"[OK] {src} -> {dst}")


def main():
    # 1. 모델 체크포인트와 meta.pkl (폴더 내부)
    # 1. 모델 체크포인트 복사
    copy_file(SRC_MODEL_DIR / "ckpt.pt", DST_MODEL_DIR / "ckpt.pt")

    # 2. 데이터 디렉토리의 meta.pkl 및 SentencePiece 모델 복사
    if SRC_DATA_DIR.exists():
        for item in SRC_DATA_DIR.iterdir():
            if item.name.endswith(".model"):
                copy_file(item, DST_MODEL_DIR / item.name)
        # dataset meta.pkl 을 models/meta.pkl 로 덮어쓰기해 토크나이저 정보 일관성 유지
        copy_file(SRC_DATA_DIR / "meta.pkl", DST_MODEL_DIR / "meta.pkl")
    else:
        print(f"[WARN] Source data dir not found: {SRC_DATA_DIR}")

    print("\n완료. piGPT 구성 파일이 준비되었습니다.")

if __name__ == "__main__":
    main()