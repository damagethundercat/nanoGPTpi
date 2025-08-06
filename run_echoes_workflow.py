import os
import subprocess
import time
import random
import pickle
import sys
import torch  # CPU/CUDA 자동 판별용
import google.generativeai as genai  # Gemini API
import sentencepiece as spm
import argparse
import json

"""
piGPT 전용 run_echoes_workflow.py
---------------------------------
라즈베리파이와 같은 CPU-only 환경에서도 동작하도록 nanoGPT 기반 워크플로우를 래핑합니다.
원본 nanoGPT 코드는 프로젝트 루트의 "nanoGPT" 폴더에 그대로 보존되고,
이 스크립트는 해당 폴더를 참조하여 실행에 필요한 파일을 호출합니다.
"""

# --------------------------------------------------
# 경로 설정
# --------------------------------------------------
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
# 원본 nanoGPT 위치
NANO_GPT_DIR = os.path.join(PROJECT_ROOT, "nanoGPT")

# --------------------------------------------------
# nanoGPT 관련 설정값
# --------------------------------------------------
NANO_GPT_DATA_DIR_NAME = "parannoul"  # 데이터 폴더 이름
PIGPT_MODEL_DIR_NAME = "models"  # piGPT 내부 모델 디렉터리
PIGPT_MODEL_DIR = os.path.join(CURRENT_DIR, PIGPT_MODEL_DIR_NAME)
PIGPT_DATA_DIR = PIGPT_MODEL_DIR  # meta.pkl 과 SentencePiece 모델도 같은 폴더에 둠
# 라즈베리파이는 GPU가 없으므로 CPU 자동 선택. CUDA 가능 시에는 활용.
NANO_GPT_DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
NANO_GPT_TEMP = 1.0
NANO_GPT_MAX_NEW_TOKENS = 150

# --------------------------------------------------
# Gemini API 설정 (원본과 동일)
# --------------------------------------------------
GEMINI_API_KEY = "AIzaSyBMcS5oe_-A6eZ8JXTdRbvZ4waMH2VdXIs"  # <-- 실제 키로 교체 필요
GEMINI_MODEL_NAME = "gemini-2.5-flash"
GEMINI_MAX_OUTPUT_TOKENS = 1000000  # MAX_TOKENS 오류 방지를 위해 줄임
GEMINI_TEMPERATURE = 0.8
GEMINI_TOP_K = 40

# --------------------------------------------------
# 전역 변수
# --------------------------------------------------
gemini_client = None  # genai.Client()
generation_config = None  # genai.types.GenerateContentConfig
safety_settings_global = None  # list[genai.types.SafetySetting]
sp_processor = None
sp_vocab_size = None

# --------------------------------------------------
# Argument Parser (원본 유지)
# --------------------------------------------------
parser = argparse.ArgumentParser()
parser.add_argument("--prompt", default="ECHOES")
parser.add_argument("--stream", action="store_true")
args = parser.parse_args()

# ==================================================
# 함수 정의
# ==================================================

def load_models_and_tokenizers():
    """SentencePiece, Gemini API 모델 초기화"""
    global gemini_model, sp_processor, sp_vocab_size

    # 1) SentencePiece 로드
    meta_path = os.path.join(PIGPT_DATA_DIR, "meta.pkl")
    if not os.path.exists(meta_path):
        print(f"meta.pkl not found: {meta_path}", file=sys.stderr)
        sys.exit(1)
    with open(meta_path, "rb") as f:
        meta = pickle.load(f)
    if "sp_model_path" not in meta:
        print("sp_model_path not in meta.pkl", file=sys.stderr)
        sys.exit(1)
    sp_model_path = meta.get("sp_model_path")
    if sp_model_path and not os.path.isabs(sp_model_path):
        sp_model_path = os.path.join(os.path.dirname(meta_path), sp_model_path)
    # models 디렉터리에서 직접 탐색 fallback
    if not sp_model_path or not os.path.exists(sp_model_path):
        for fname in os.listdir(os.path.dirname(meta_path)):
            if fname.endswith('.model'):
                sp_model_path = os.path.join(os.path.dirname(meta_path), fname)
                break
    if not sp_model_path or not os.path.exists(sp_model_path):
        print("SentencePiece 모델 파일을 찾을 수 없습니다.", file=sys.stderr)
        sys.exit(1)
    sp_processor = spm.SentencePieceProcessor()
    sp_processor.load(sp_model_path)
    sp_vocab_size = meta.get("vocab_size", None)

    # 2) Gemini API
    if GEMINI_API_KEY in (None, "", "YOUR_GEMINI_API_KEY"):
        print("Gemini API 키가 설정되지 않았습니다.", file=sys.stderr)
        sys.exit(1)
    genai.configure(api_key=GEMINI_API_KEY)
    # 2) Gemini API - GenerativeModel 방식 (안전 설정 강화)
    generation_config = genai.types.GenerationConfig(
        max_output_tokens=GEMINI_MAX_OUTPUT_TOKENS,
        temperature=GEMINI_TEMPERATURE,
        top_k=GEMINI_TOP_K,
    )
    
    # 모든 안전 필터를 BLOCK_NONE으로 설정
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"}, 
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]
    
    global gemini_model
    gemini_model = genai.GenerativeModel(
        model_name=GEMINI_MODEL_NAME,
        generation_config=generation_config,
        safety_settings=safety_settings,
    )


# -----------------------------------------------------------------------------
# 이하의 tokenize_text_bpe_recursive, generate_with_nanogpt_bpe_recursive,
# refine_with_gemini_api 함수는 원본과 동일 로직을 유지하되 NANO_GPT_DIR 변수를
# 이 스크립트에서 정의한 값으로 사용합니다.
# -----------------------------------------------------------------------------

def tokenize_text_bpe_recursive(text: str):
    if not sp_processor:
        print("SentencePiece not loaded", file=sys.stderr)
        return []
    token_ids = sp_processor.encode_as_ids(text)
    return [sp_processor.id_to_piece(tid) for tid in token_ids]


def generate_with_nanogpt_bpe_recursive(seed_bpe_token: str):
    if not seed_bpe_token.strip():
        return ""
    current_seed = random.randint(0, 2**32 - 1)
    python_executable = sys.executable
    sample_script_path = os.path.join(CURRENT_DIR, "sample.py")
    model_out_dir = PIGPT_MODEL_DIR_NAME

    command = [
        python_executable,
        sample_script_path,
        f"--out_dir={model_out_dir}",
        f"--device={NANO_GPT_DEVICE}",
        f"--temperature={NANO_GPT_TEMP}",
        f"--start={seed_bpe_token}",
        "--num_samples=1",
        f"--max_new_tokens={NANO_GPT_MAX_NEW_TOKENS}",
        f"--seed={current_seed}",
    ]
    try:
        result = subprocess.run(
            command,
            cwd=CURRENT_DIR,  # sample.py 는 nanoGPT 기준 경로에서 실행
            capture_output=True,
            text=True,
            check=True,
            encoding="utf-8",
            errors="replace",
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        # ====== 추가: 전체 STDOUT 확인 ======
        # print("\n=== sample.py RAW STDOUT ===", file=sys.stderr)
        # print(result.stdout, file=sys.stderr)
        # print("=== END STDOUT ===\n", file=sys.stderr)
        # ===================================
        full_out = result.stdout.splitlines()
        # 필터: 파라미터 라인 제거 및 빈 줄 제거
        meaningful = [ln for ln in full_out if ln.strip() and not ln.lower().startswith('number of parameters')]
        if not meaningful:
            return ""
        # 여러 줄이면 첫 줄만 사용
        return meaningful[0].strip()
    except subprocess.CalledProcessError as e:
        print(f"sample.py 오류: {e.stderr}", file=sys.stderr)
        return ""


def refine_with_gemini_api(raw_text: str, seed_token: str):
    """Gemini 교정. 실패하면 원문 반환"""
    if not raw_text:
        return ""
    prompt = f"""다음 텍스트를 자연스럽게 교정해주세요. 
규칙:
1. 원본의 형태와 길이를 최대한 유지하세요
2. 불필요한 설명이나 부가 설명은 하지 마세요
3. 줄바꿈이나 특수문자(/)를 추가하지 마세요
4. 교정된 텍스트만 출력하세요

원본: {raw_text}

교정:"""
    # print(f"[DEBUG] raw_text({seed_token}) >>> {raw_text}", file=sys.stderr)
    
    try:
        # GenerativeModel 방식으로 호출 (스트리밍 모드)
        response = gemini_model.generate_content(
            prompt,
            stream=True,  # 스트리밍 활성화로 더 안정적인 응답
        )
        
        # 스트리밍 모드에서는 chunk 단위로 처리
        collected = ""
        finish_reason = "N/A"
        prompt_feedback = None
        
        for chunk in response:
            if hasattr(chunk, "candidates") and chunk.candidates:
                candidate = chunk.candidates[0]
                if hasattr(candidate, "content") and candidate.content.parts:
                    part_text = candidate.content.parts[0].text
                    collected += part_text
                finish_reason = getattr(candidate, "finish_reason", finish_reason)
            
            if hasattr(chunk, "prompt_feedback") and chunk.prompt_feedback:
                prompt_feedback = chunk.prompt_feedback
        
        # 디버그 로그
        # print(f"[DEBUG] collected_len: {len(collected)}, finish_reason: {finish_reason}", file=sys.stderr)
        # if prompt_feedback:
        #     print(f"[DEBUG] prompt_feedback: {prompt_feedback}", file=sys.stderr)

        if collected.strip():
            return collected.strip()
        else:
            # print("[WARN] Gemini returned empty. Falling back to raw_text.", file=sys.stderr)
            return raw_text
            
    except Exception as e:
        # print(f"Gemini API 예외: {repr(e)}", file=sys.stderr)
        # import traceback
        # traceback.print_exc(file=sys.stderr)
        return raw_text
        

# ==================================================
# 메인 루프
# ==================================================
if __name__ == "__main__":
    load_models_and_tokenizers()
    print("piGPT 준비 완료 (device: {})".format(NANO_GPT_DEVICE))

    while True:
        try:
            prompt = input("프롬프트를 입력하세요 (exit/quit 종료): ").strip()
        except EOFError:
            break
        if prompt.lower() in ("exit", "quit"):
            break
        if not prompt:
            continue

        bpe_tokens = tokenize_text_bpe_recursive(prompt)
        refined_map = {}
        for token in bpe_tokens:
            raw = generate_with_nanogpt_bpe_recursive(token)
            refined = refine_with_gemini_api(raw, token)
            refined_map[token] = refined
            print({"seed_token": token, "generated_text": refined})

        print("--- 최종 결과 ---", file=sys.stderr)
        for tk, txt in refined_map.items():
            print(f"[{tk}] {txt}", file=sys.stderr)

    print("종료합니다.", file=sys.stderr)