<div align="center">

# 🔍 PDF Figure-Reference Mapping System (PDF 그림-참조 매핑 시스템)

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

***Marker**를 사용하여 텍스트를 추출하고, 향상된 정확도와 성능으로 구조화된 텍스트 블록을 제공하는 최신 PDF 분석 시스템입니다.

</div>

---

## 📑 목차

- [🚀 구현된 기능](#-구현된-기능)
- [🏗️ 아키텍처](#️-아키텍처)
- [📋 사전 요구사항](#-사전-요구사항)
- [🔧 설치](#-설치)
- [🧪 테스트](#-테스트)
- [🚀 사용법](#-사용법)
- [⚙️ 설정](#️-설정)
- [🐛 문제 해결](#-문제-해결)
- [📊 성능](#-성능)
- [🛠️ 개발](#-개발)
- [📝 현재 상태](#-현재-상태)
- [📚 문서](#-문서)
- [🤝 기여](#-기여)
- [📄 라이선스](#-라이선스)

---

## 🚀 구현된 기능

### ✅ 섹션 1: 프로젝트 구조 및 환경 설정
- 모듈화된 프로젝트 구조 (서비스별 분리)
- `config.yaml`을 통한 설정 관리
- GPU 메모리 관리 유틸리티
- 최신 의존성을 사용한 요구사항 관리

### ✅ 섹션 2: PDF 처리 및 추출
- 대용량 문서를 위한 메모리 효율적인 배치 처리
- 페이지 메타데이터 추출

### ✅ 섹션 3: Marker OCR 구현 (PaddleOCR에서 업그레이드)
- **Marker PDF-to-Markdown 변환**
- 향상된 레이아웃 이해 및 텍스트 구조 보존
- ollama를 이용한 OCR 보완 (`config.yaml`에서 llm_services 확인)
- 약 5GB VRAM을 사용하는 GPU 가속
- 의존성 충돌 없음 - 최신이며 잘 관리되는 라이브러리

### ✅ 피규어 맵핑
- 정규표현을 이용한 Figure매칭
- llm을 이용하여 Figure 추출 (다양한 참조 텍스트 유형 지원, `config.yaml`의 reference_mapper 확인)

---

## 🏗️ 아키텍처

```
app/
├── config/          # 설정 관리
├── services/        # 핵심 비즈니스 로직
├── utils/           # 유틸리티 함수
├── api/
│   └── routes/
│       ├── analyze.py      # /analyze 라우트
│       ├── health.py       # /health 라우트
│       └── __init__.py     # 블루프린트 통합
└── main.py          # Flask API 서버
```

---

## 📋 사전 요구사항

- Python 3.10 이상
- CUDA 12.8 이상 (GPU 가속용)
- 16GB 이상 시스템 RAM (24GB 이상 권장)
- 8GB 이상 VRAM을 갖춘 NVIDIA GPU (RTX 3090 권장, CPU 폴백 가능)

---

## 🔧 설치

<details>
<summary><strong>빠른 설치 (Windows)</strong></summary>

```batch
# 1. 환경 생성
conda create -n pdf-mapper python=3.10
conda activate pdf-mapper

# 2. 자동 설치 스크립트 실행
install_marker_gpu.bat    # GPU 사용자를 위한 스크립트
```
</details>

<details>
<summary><strong>수동 설치</strong></summary>

```bash
# 1. 가상 환경 생성
conda create -n pdf-mapper python=3.10
conda activate pdf-mapper

# 2. CUDA 12.8 버전의 PyTorch 설치
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128

# 3. Marker 및 의존성 설치
pip install marker-pdf[full]
pip install -r requirements.txt

# 4. spaCy 모델 다운로드
python -m spacy download en_core_web_sm
```
</details>

---

## 🧪 테스트

종합 테스트 스위트를 실행하여 설정을 확인하세요:

```bash
python test_marker_setup.py
```

이 테스트는 다음을 확인합니다:
- 설정 로딩
- Marker 라이브러리 사용 가능 여부
- GPU 사용 가능 여부 및 메모리 관리
- Marker 모델 로딩 및 처리
- PDF 처리 기능
- 텍스트 블록 추출 파이프라인

---

## 🚀 사용법

### 서버 시작

```bash
python -m app.main
```

API 서버는 `http://localhost:12321`에서 시작됩니다.

### API 엔드포인트

<details>
<summary><strong>POST `/analyze` (SSE 전용)</strong></summary>

PDF 파일을 업로드하고 **서버-전송 이벤트(SSE)**를 통해 실시간 진행 상황과 결과를 받습니다.

**요청:**
- Content-Type: `multipart/form-data`
- 파라미터: `file` (PDF 파일, 최대 50MB)

**응답:**
- `text/event-stream` (SSE)
- 각 이벤트는 다음과 같은 JSON 객체입니다:
  ```json
  {
    "status": "progress|completed|error|started|warning",
    "message": "...",
    "data": { ... },      // 'completed' 상태일 때 전체 결과
    "progress": 0~100     // 진행률 (퍼센트)
  }
  ```
- 마지막 이벤트(`status: completed`)에 전체 분석 결과가 포함됩니다.
</details>

<details>
<summary><strong>GET `/health`</strong></summary>

시스템 상태를 JSON 형식으로 반환합니다.
</details>

### 사용 예시

```bash
# SSE로 분석 진행 상황 및 결과 수신
curl -N -X POST -F "file=@sample.pdf" http://localhost:5000/analyze

# 시스템 상태 확인
curl http://localhost:5000/health
```

---

## ⚙️ 설정

`config.yaml` 파일을 수정하여 다음을 커스터마이징하세요:

```yaml
models:
  marker: # 모델 이름은 nougat 대신 marker 또는 프로젝트에 맞게 변경하는 것이 좋습니다.
    model_name: "naver-clova-ix/donut-base-finetuned-docvqa" # 예시, 실제 사용하는 Marker 모델로 변경
    batch_size: 4          # GPU 메모리 문제 시 줄이세요
    # gpu_memory: 10       # Marker는 자동 메모리 관리가 더 효율적일 수 있습니다.
    precision: "fp16"      # 메모리 효율성을 위해 FP16 사용

hardware:
  gpu_device: 0
  # total_gpu_memory: 24   # 필요 시 설정
  cpu_cores: 8

api:
  host: "0.0.0.0"
  port: 5000
  max_file_size: 52428800  # 50MB
```

---

## 🐛 문제 해결

<details>
<summary><strong>GPU 메모리 문제</strong></summary>

- `config.yaml`에서 `batch_size`를 줄입니다.
- `precision: "fp16"`을 활성화합니다.
- 더 작은 문서나 페이지 범위를 처리합니다.
</details>

<details>
<summary><strong>모델 로딩 실패</strong></summary>

- 인터넷 연결을 확인하세요 (모델은 첫 사용 시 다운로드됩니다).
- CUDA 설치를 확인하세요: `nvidia-smi`
- `CUDA_VISIBLE_DEVICES=""`로 설정하여 CPU 전용 모드를 시도해보세요.
</details>

<details>
<summary><strong>처리 시간 초과</strong></summary>

- 대용량 문서는 배치 처리를 사용하세요.
- `nvidia-smi`로 GPU 사용량을 모니터링하세요.
</details>

---

## 📊 성능

### **처리 시간 (RTX 3090 기준):**
- 작은 PDF (20 페이지): **2분**
- 큰 PDF (1000+ 페이지): **5-10분**

---

## 🛠️ 개발

### 새로운 기능 추가

이 시스템은 확장이 용이하도록 설계되었습니다. 향후 다음 기능들이 추가될 예정입니다:
- BERT 참조 추출
- 시맨틱 매칭
- 완전한 Flask API (인증토큰 도입)

### 코드 구조

- `services/`: 독립적인 서비스 모듈
- `utils/`: 공유 유틸리티 함수
- `config/`: 설정 관리
- API 라우트는 `app/api/routes/` 내에서 기능별로 분리됩니다.
- 테스트는 `app/tests/`에 추가해야 합니다.

---

## 📝 현재 상태

### ✅ **완료 (Marker 마이그레이션):**
- ✅ Marker를 사용한 최신 PDF-to-text 추출
- ✅ 처리 속도 및 정확도 향상
- ✅ 깨끗한 의존성 관리 (충돌 없음)
- ✅ 향상된 텍스트 블록 분류
- ✅ 향상된 레이아웃 이해

### 🔄 **다음 단계:**
- BERT 참조 추출
- 시맨틱 매칭
- API 기능 완성

---

## 📚 문서

- API 문서: 이 README 참조
- 설정 참조: `config.yaml`

---

## 🤝 기여

이 프로젝트에 기여하고 싶으신가요? 언제나 환영합니다!

자세한 내용은 아래의 가이드를 참고해주세요:
- **[기여 가이드라인](docs/CONTRIBUTING.md)**: 코드 스타일, 커밋 메시지 규칙, PR 절차 등 기여에 필요한 모든 정보를 담고 있습니다.
- **[브랜치 전략](docs/BRANCH_STRATEGY.md)**: 프로젝트에서 사용하는 Git 브랜치 전략에 대해 설명합니다.

## Contributors
- jaeho0718 (이재호)


---

## 📞 문의 및 지원

- **이슈 리포트**: [GitHub Issues](https://github.com/CommitBang/PDF-Reference-Mapper/issues)
- **기능 제안**: [GitHub Discussions](https://github.com/CommitBang/PDF-Reference-Mapper/discussions)
- **문서**: [docs/](docs/) 폴더 참조

---

## 📄 라이선스

이 프로젝트는 [GNU General Public License v3.0 (GPL-3.0)](LICENSE) 하에 배포됩니다.
Copyright © 2025 commit bang. All rights reserved.

이 프로젝트는 `marker-pdf` 라이브러리(GPL-3.0-or-later)를 사용하므로, GPLv3 라이선스 요구사항을 따릅니다.
`marker-pdf`의 모델 가중치는 [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) 라이선스가 적용되며, 상업적 사용에 대한 자세한 내용은 [Marker 저장소](https://github.com/VikParuchuri/marker)를 참고하세요.

</div>
