import os
import sys
import pickle
from contextlib import nullcontext
import torch
try:
    import tiktoken  # fallback
except ImportError:
    tiktoken = None
import sentencepiece as spm

"""
piGPT 전용 sample.py
--------------------
원본 nanoGPT/sample.py 를 가볍게 수정하여 CPU 환경에서 기본 동작하도록 함.
필요한 GPT 모델 정의는 nanoGPT 폴더를 sys.path 에 추가하여 재사용합니다.
"""

# nanoGPT 경로를 import 경로에 추가
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
NANO_GPT_DIR = os.path.join(PROJECT_ROOT, "nanoGPT")
sys.path.append(NANO_GPT_DIR)

from model import GPTConfig, GPT  # type: ignore

# -----------------------------------------------------------------------------
# 기본 설정 (CLI 인자로 덮어쓰기 가능)
# -----------------------------------------------------------------------------
init_from = 'resume'
out_dir = 'models'
start = "\n"
num_samples = 1
max_new_tokens = 150
temperature = 0.8
top_k = 200
seed = 1337
# 라즈베리파이에서는 CPU-only
device = 'cuda' if torch.cuda.is_available() else 'cpu'
# CUDA 사용 가능 여부 재확인 (CLI 인자가 cuda라도 실제 환경에 없으면 CPU로 강제)
if device.startswith('cuda') and not torch.cuda.is_available():
    print('[WARN] CUDA 미지원 환경입니다. device를 cpu로 변경합니다.', file=sys.stderr)
    device = 'cpu'

# dtype 결정
dtype = 'float16' if device.startswith('cuda') else 'float32'
compile_model = False

# CLI 인자 파싱으로 기본값 덮어쓰기
import argparse
parser = argparse.ArgumentParser(add_help=False)
parser.add_argument("--out_dir")
parser.add_argument("--device")
parser.add_argument("--temperature", type=float)
parser.add_argument("--start")
parser.add_argument("--num_samples", type=int)
parser.add_argument("--max_new_tokens", type=int)
parser.add_argument("--top_k", type=int)
parser.add_argument("--seed", type=int)
cli_args, _ = parser.parse_known_args()
if cli_args.out_dir: out_dir = cli_args.out_dir
if cli_args.device: device = cli_args.device
if cli_args.temperature is not None: temperature = cli_args.temperature
if cli_args.start is not None: start = cli_args.start
if cli_args.num_samples is not None: num_samples = cli_args.num_samples
if cli_args.max_new_tokens is not None: max_new_tokens = cli_args.max_new_tokens
if cli_args.top_k is not None: top_k = cli_args.top_k
if cli_args.seed is not None:
    seed = cli_args.seed
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)

# -----------------------------------------------------------------------------
# 시드 고정
# -----------------------------------------------------------------------------
torch.manual_seed(seed)
if torch.cuda.is_available():
    torch.cuda.manual_seed(seed)

torch.backends.cuda.matmul.allow_tf32 = True
torch.backends.cudnn.allow_tf32 = True

device_type = 'cuda' if device.startswith('cuda') else 'cpu'
ptdtype = {'float32': torch.float32, 'bfloat16': torch.bfloat16, 'float16': torch.float16}[dtype]
ctx = nullcontext() if device_type == 'cpu' else torch.amp.autocast(device_type=device_type, dtype=ptdtype)

# -----------------------------------------------------------------------------
# 체크포인트 로드
# -----------------------------------------------------------------------------
checkpoint_dir = os.path.join(CURRENT_DIR, out_dir) if not os.path.isabs(out_dir) else out_dir
ckpt_path = os.path.join(checkpoint_dir, 'ckpt.pt')
if not os.path.exists(ckpt_path):
    print(f"Checkpoint not found: {ckpt_path}")
    sys.exit(1)

map_loc = torch.device('cuda') if device.startswith('cuda') else torch.device('cpu')
checkpoint = torch.load(ckpt_path, map_location=map_loc)
model_args = checkpoint.get('model_args', None)
if model_args is None:
    print("model_args missing in checkpoint")
    sys.exit(1)

model = GPT(GPTConfig(**model_args))
model.load_state_dict(checkpoint['model'], strict=False)
model.eval()
model.to(device)

# -----------------------------------------------------------------------------
# 토크나이저 결정 (SentencePiece 우선)
# -----------------------------------------------------------------------------
meta_path = os.path.join(checkpoint_dir, 'meta.pkl')
encode = None
decode = None

if os.path.exists(meta_path):
    with open(meta_path, 'rb') as f:
        meta = pickle.load(f)
    spm_path = None
    if 'sp_model_path' in meta:
        spm_path = meta['sp_model_path']
        if not os.path.isabs(spm_path):
            spm_path = os.path.join(os.path.dirname(meta_path), spm_path)
    # sp_model_path 가 없거나 파일이 없으면 models 디렉터리에서 *.model 탐색
    if not spm_path or not os.path.exists(spm_path):
        for fname in os.listdir(os.path.dirname(meta_path)):
            if fname.endswith('.model'):
                spm_path = os.path.join(os.path.dirname(meta_path), fname)
                break
    if spm_path and os.path.exists(spm_path):
        sp = spm.SentencePieceProcessor()
        sp.load(spm_path)
        encode = lambda s: sp.encode_as_ids(s)
        decode = lambda l: sp.decode_ids(l)

if encode is None or decode is None:
    if tiktoken is None:
        print("[ERROR] SentencePiece 로더 실패 및 tiktoken 미설치", file=sys.stderr)
        sys.exit(1)
    enc = tiktoken.get_encoding('gpt2')
    encode = lambda s: enc.encode(s)
    decode = lambda l: enc.decode(l)

# -----------------------------------------------------------------------------
# 시작 프롬프트 처리 및 인코딩
# -----------------------------------------------------------------------------
start_ids = encode(start)
# 빈 토큰 시 에러 방지용 fallback
if len(start_ids) == 0:
    try:
        start_ids = [sp.piece_to_id(start)]
        if start_ids[0] < 0:
            start_ids = [0]
    except Exception:
        start_ids = [0]
x = torch.tensor(start_ids, dtype=torch.long, device=device)[None, ...]

# -----------------------------------------------------------------------------
# 생성
# -----------------------------------------------------------------------------
with torch.no_grad():
    with ctx:
        for k in range(num_samples):
            y = model.generate(x, max_new_tokens, temperature=temperature, top_k=top_k)
            print(decode(y[0].tolist()))