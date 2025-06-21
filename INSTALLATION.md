# 설치 안내서 - PDF Mapper

## 사전 요구사항

- **Python 3.9-3.12** (Python 3.10 권장)
- **CUDA 12.1-12.9** (GPU 가속용)
- **16GB 이상 시스템 RAM**
- **10GB 이상 VRAM을 갖춘 NVIDIA GPU** (RTX 3090, RTX 4090 또는 유사 사양)

## 단계별 설치 방법

### 1. 가상 환경 생성

```bash
# Conda 사용 (권장)
conda create -n pdf-mapper python=3.10
conda activate pdf-mapper

# 또는 venv 사용
python -m venv pdf-mapper
source pdf-mapper/bin/activate  # Linux/Mac
# pdf-mapper\Scripts\activate     # Windows
```

### 2. CUDA를 지원하는 PyTorch 설치

**CUDA 12.8-12.9용 (권장):**

```bash
# pip 사용
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128

# 또는 conda 사용
conda install pytorch torchvision torchaudio pytorch-cuda=12.8 -c pytorch -c nvidia
```

**CPU 전용 (GPU가 없는 경우):**

```bash
pip install torch>=2.1.0 torchvision>=0.16.0 torchaudio>=2.1.0 --index-url https://download.pytorch.org/whl/cpu
```

### 3. 프로젝트 의존성 설치

**⚠️ 중요: 의존성 충돌을 피하기 위해 단계별 설치를 사용하세요.**

```bash
# 1단계: CUDA 12.8 버전의 PyTorch를 먼저 설치합니다.
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128

# 2단계: 핵심 의존성 설치
pip install -r requirements-step1.txt

# 3단계: nougat-ocr 설치 (timm==0.5.4 버전이 설치됩니다)
pip install -r requirements-step2.txt

# 4단계: 나머지 의존성 설치
pip install -r requirements-step3.txt
```

**대안: 단일 명령 (충돌 가능성 있음)**
```bash
pip install -r requirements.txt
```

### 4. 언어 모델 다운로드

```bash
# spaCy 영어 모델 다운로드
python -m spacy download en_core_web_sm
```

### 5. 설치 확인

```bash
python test_nougat_setup.py
```

이 테스트는 다음을 확인합니다:
- ✅ 설정 로딩
- ✅ GPU 사용 가능 여부 및 메모리
- ✅ PyTorch CUDA 설정
- ✅ Nougat 모델 로딩
- ✅ 모든 서비스 컴포넌트

## 문제 해결

### CUDA 문제

**문제: `torch.cuda.is_available()`가 `False`를 반환합니다.**

```bash
# CUDA 설치 확인
nvidia-smi

# PyTorch CUDA 확인
python -c "import torch; print('CUDA available:', torch.cuda.is_available()); print('CUDA version:', torch.version.cuda)"
```

**해결책:** 올바른 CUDA 버전으로 PyTorch를 재설치하세요:

```bash
pip uninstall torch torchvision torchaudio
pip install torch>=2.1.0 torchvision>=0.16.0 torchaudio>=2.1.0 --index-url https://download.pytorch.org/whl/cu121
```

### 메모리 문제

**문제: GPU 메모리 부족(Out of Memory) 오류**

1.  **배치 크기 줄이기** (`config.yaml`):
    ```yaml
    models:
      nougat:
        batch_size: 2  # 4에서 줄임
    ```

2.  **FP16 정밀도 활성화**:
    ```yaml
    models:
      nougat:
        precision: "fp16"
    ```

3.  **GPU 사용량 모니터링**:
    ```bash
    watch -n 1 nvidia-smi
    ```

### 의존성 충돌

**문제: `timm` 버전이 nougat-ocr과 충돌합니다.**

```
ERROR: Cannot install timm>=0.9.12 and nougat-ocr 0.1.17 
because nougat-ocr depends on timm==0.5.4
```

**해결책: 단계별 설치를 사용하세요.**

```bash
# 1. 새로운 환경 생성
conda create -n pdf-mapper python=3.10
conda activate pdf-mapper

# 2. CUDA 12.8 버전의 PyTorch 설치
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128

# 3. 단계별 의존성 설치
pip install -r requirements-step1.txt  # 핵심 의존성
pip install -r requirements-step2.txt  # nougat-ocr과 timm==0.5.4 설치
pip install -r requirements-step3.txt  # 나머지 의존성

# 4. 설치 확인
python -c "import nougat; import timm; print(f'timm version: {timm.__version__}')"
```

**대안: nougat-ocr 먼저 설치하기**

```bash
# timm 버전을 고정하기 위해 nougat-ocr 먼저 설치
pip install nougat-ocr==0.1.17

# 그 다음 다른 패키지 설치
pip install -r requirements.txt --no-deps
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
```

### Marker 라이브러리 문제

**문제: Marker 라이브러리 설치 실패**

```
ERROR: Could not find a version that satisfies the requirement marker-pdf
```

**해결방법:**

```bash
# 1. pip 업데이트 후 올바른 소스에서 설치
pip install --upgrade pip
pip install marker-pdf[full]

# 2. 그래도 실패하면, 의존성을 먼저 설치해보세요
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
pip install transformers
pip install marker-pdf[full]
```

### 모델 다운로드 문제

**문제: Marker 모델 다운로드 실패**

1.  **인터넷 연결 확인**
2.  **수동 모델 초기화 시도**:
    ```bash
    python -c "from marker.models import create_model_dict; create_model_dict()"
    ```
3.  **HuggingFace 캐시 사용**:
    ```bash
    export HF_HOME=/path/to/cache
    python -c "from marker.models import create_model_dict; create_model_dict()"
    ```

## 버전 호환성 매트릭스

| 구성 요소 | 버전 | 비고 |
|---|---|---|
| Python | 3.10-3.12 | 3.10 권장 |
| PyTorch | 2.1.0+ | CUDA 버전과 일치해야 함 |
| CUDA | 12.8-12.9 | 12.8 빌드 권장 |
| Transformers | 4.35.0+ | Marker에 필요 |
| Marker-PDF | 0.2.0+ | 최신 버전 권장 |

## 하드웨어 요구사항

### 최소 요구사항
- **GPU:** 8GB VRAM (GTX 1080, RTX 3070)
- **RAM:** 16GB 시스템 메모리
- **저장 공간:** 10GB 여유 공간 (모델용)

### 권장 요구사항
- **GPU:** 24GB VRAM (RTX 3090, RTX 4090)
- **RAM:** 32GB 시스템 메모리
- **저장 공간:** 50GB 여유 공간 (모델 캐시용)

### 성능 예상 (Marker 사용 시)

| 문서 크기 | RTX 3090 | RTX 3070 | CPU만 |
|---|---|---|---|
| 10 페이지 | 8-15초 | 15-25초 | 3-6분 |
| 50 페이지 | 1-2분 | 3-5분 | 12-20분 |
| 200 페이지 | 4-8분 | 10-18분 | 1-2시간 |

## 환경 변수

```bash
# 선택사항: CUDA 장치 설정
export CUDA_VISIBLE_DEVICES=0

# 선택사항: HuggingFace 캐시 디렉토리
export HF_HOME=/path/to/huggingface/cache

# 선택사항: 토크나이저 병렬 처리 경고 비활성화
export TOKENIZERS_PARALLELISM=false
```

## 설치 테스트

```bash
# 빠른 테스트
python -c "import torch; print('PyTorch:', torch.__version__); print('CUDA:', torch.cuda.is_available())"

# 전체 시스템 테스트
python test_marker_setup.py

# 서버 시작 테스트
python -m app.main &
curl -X GET http://localhost:5000/health
```

## 일반적인 설치 명령어

### 완전한 새로 설치

**Linux/Mac:**
```bash
# 1. 환경 생성
conda create -n pdf-mapper python=3.10 -y
conda activate pdf-mapper

# 2. CUDA 12.8 버전의 PyTorch 설치
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128

# 3. 의존성 설치 (충돌 방지를 위해 단계별로)
pip install -r requirements-step1.txt  # 핵심 의존성
pip install -r requirements-step2.txt  # nougat-ocr과 timm==0.5.4
pip install -r requirements-step3.txt  # 나머지 의존성

# 4. 모델 다운로드
python -m spacy download en_core_web_sm

# 5. 설치 테스트
python test_marker_setup.py
```

**Windows:**
```batch
# 1. 환경 생성
conda create -n pdf-mapper python=3.10 -y
conda activate pdf-mapper

# 2. 자동 설치 스크립트 실행
install_marker_gpu.bat    # Marker를 사용하는 GPU 유저용
```

### 기존 설치 업데이트

```bash
# 패키지 업데이트
pip install --upgrade -r requirements.txt

# 버전 확인
pip list | grep -E "(torch|transformers|nougat)"
```

여기서 다루지 않은 문제가 발생하면, 메인 `README.md`를 확인하거나 시스템 사양과 오류 메시지를 포함하여 이슈를 생성해주세요.