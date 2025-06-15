<div align="center">

# 🔍 PDF Reference Mapper

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)](https://flask.palletsprojects.com/)
[![PaddleOCR](https://img.shields.io/badge/PaddleOCR-3.0+-orange.svg)](https://github.com/PaddlePaddle/PaddleOCR)
[![License](https://img.shields.io/badge/License-APACHE-yellow.svg)](LICENSE)

*레이아웃 감지, OCR, 도표-참조 자동 매핑을 통한 지능형 PDF 처리*

</div>

---

## 📑 목차

- [✨ 주요 기능](#-주요-기능)
- [🏗️ 아키텍처](#️-아키텍처)
- [🔧 설치](#-설치)
- [🚀 빠른 시작](#-빠른-시작)
- [📊 API 응답](#-api-응답-형식)
- [⚙️ 설정](#️-설정)
- [🧪 고급 기능](#-고급-기능)
- [🐛 문제 해결](#-문제-해결)
- [📚 API 문서](#-api-문서)
- [🤝 기여하기](#-기여하기)
- [📝 라이선스](#-라이선스)

---

## ✨ 주요 기능

<details>
<summary><strong>📄 종합 PDF 분석</strong></summary>

- **🔄 다중 페이지 처리**: 대용량 PDF 문서를 자동으로 페이지별 분석
- **📋 메타데이터 추출**: 문서 제목, 저자, 생성일 등 메타데이터 추출
</details>

<details>
<summary><strong>🔍 레이아웃 감지</strong></summary>

- **🎯 요소 인식**: 그림, 표, 수식, 알고리즘, 제목, 캡션 감지
- **🧩 지능형 그룹화**: 관련 요소(예: 그림+제목+캡션) 자동 그룹화
- **📐 공간 분석**: 공간적 관계와 정렬 패턴을 활용한 정확한 그룹화
- **🔀 다중 전략**: ID, 패턴, 근접도 기반 그룹화 병행

</details>

<details>
<summary><strong>📝 텍스트 처리</strong></summary>

- **🎯 고정밀 OCR**: PaddleOCR로 텍스트 및 바운딩 박스 추출
- **🏷️ 타입 인식 참조 추출**: 참조(예: Fig. 1, Table 2, Eq. (3) 등) 식별 및 분류

</details>

<details>
<summary><strong>🔗 참조 매핑</strong></summary>

- **🕸️ 그래프 기반 매핑**: NetworkX로 도표-참조 관계 추론
- **✅ 타입 호환 매칭**: 타입 일치 기반 참조-도표 매칭
- **📊 신뢰도 점수**: 매핑 신뢰도 제공
- **🗺️ 공간 맥락**: 문서 레이아웃, 근접도 고려

</details>

---

## 🏗️ 아키텍처

```
🔍 PDF Reference Mapper
├── 📁 app/
│   ├── 📁 api/                     # 🌐 REST API 엔드포인트
│   ├── 📁 services/                # ⚙️ 핵심 처리 서비스
│   │   ├── 🧠 pdf_processor.py       # 메인 PDF 처리 파이프라인
│   │   ├── 👁️ layout_detector.py     # PaddleOCR 기반 레이아웃 감지
│   │   ├── 🧩 figure_grouper.py      # 지능형 요소 그룹화
│   │   ├── 🏷️ figure_id_generator.py # 도표 ID 추출 및 생성
│   │   ├── 📝 reference_extractor.py # 참조 감지 및 분류
│   │   └── 🔗 figure_mapper.py       # 그래프 기반 도표-참조 매핑
│   └── 📁 templates/               # 🖥️ 웹 인터페이스 템플릿
├── 📄 config.py                   # ⚙️ 설정 관리
├── 📄 main.py                     # 🚀 앱 진입점
└── 📄 requirements.txt            # 📦 의존성 목록
```

---

## 🔧 설치

### 📋 사전 준비

> **필수 요구사항**
> - 🐍 **Python 3.9+** (3.9~3.11 권장)
> - 🚀 **CUDA 12.9** (선택사항, GPU 가속용)

### ⚡ 자동 설치 (권장)

```bash
# 1️⃣ 저장소 클론
git clone https://github.com/yourusername/pdf-recognition-api.git
cd pdf-recognition-api

# 2️⃣ 원클릭 설치
python setup.py
```

<details>
<summary>🔧 수동 설치</summary>

```bash
# 가상환경 생성
conda create -n pdfrec python=3.9
conda activate pdfrec

# 의존성 설치
pip install -r requirements.txt

# GPU 지원 (선택)
pip install paddlepaddle-gpu==3.0.0 -i https://www.paddlepaddle.org.cn/packages/stable/cu123/
```

</details>

---

## 🚀 빠른 시작

### 1️⃣ 서버 실행

```bash
python main.py
```

🎉 **서버가 실행되었습니다!** API는 `http://localhost:5000`에서 사용 가능합니다.

### 2️⃣ 인터페이스 확인

| 인터페이스 | URL | 설명 |
|-----------|-----|------|
| 🖥️ **웹 테스트** | [`http://localhost:5000/`](http://localhost:5000/) | 브라우저에서 바로 테스트 |
| 📖 **API 문서** | [`http://localhost:5000/api/docs/`](http://localhost:5000/api/docs/) | Swagger UI 인터랙티브 문서 |

### 3️⃣ API 사용 예시

<details>
<summary><strong>🔥 cURL로 빠른 테스트</strong></summary>

```bash
curl -X POST \
  http://localhost:5000/api/v1/analyze \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@your_document.pdf'
```

</details>

<details>
<summary><strong>🐍 Python 예제</strong></summary>

```python
import requests

# 📄 PDF 업로드 및 분석
url = "http://localhost:5000/api/v1/analyze"
with open("document.pdf", "rb") as file:
    files = {"file": file}
    response = requests.post(url, files=files)

result = response.json()

# 📊 결과 확인
print(f"📄 문서: {result['metadata']['title']}")
print(f"📄 페이지 수: {len(result['pages'])}")
print(f"🖼️ 감지된 도표 수: {len(result['figures'])}")

# 🔗 매핑 통계 확인 (내부 통계는 API 응답에 포함되지 않음)
for page in result['pages']:
    matched_refs = [r for r in page['references'] if not r.get('not_matched', True)]
    total_refs = len(page['references'])
    print(f"📝 페이지 {page['index']}: {len(matched_refs)}/{total_refs} 참조 매칭")
```

</details>

---

## 📊 API 응답 형식

<details>
<summary><strong>📋 전체 JSON 스키마</strong></summary>

```json
{
  "metadata": {
    "title": "문서 제목",
    "author": "저자명", 
    "pages": 10
  },
  "pages": [
    {
      "index": 0,
      "page_size": [595, 842],
      "blocks": [
        {
          "text": "추출된 텍스트",
          "bbox": {"x": 100, "y": 200, "width": 150, "height": 20}
        }
      ],
      "references": [
        {
          "text": "Fig. 1",
          "bbox": {"x": 50, "y": 100, "width": 40, "height": 15},
          "figure_id": "1",
          "not_matched": false
        }
      ]
    }
  ],
  "figures": [
    {
      "figure_id": "1",
      "type": "figure",
      "bbox": {"x": 100, "y": 300, "width": 200, "height": 150},
      "page_idx": 0,
      "text": "Figure 1: 예시 캡션"
    }
  ]
}
```

</details>

### 📋 주요 필드 설명

| 필드 | 타입 | 설명 |
|------|------|------|
| `metadata` | Object | 📄 문서 메타정보 (제목, 저자, 페이지 수) |
| `pages` | Array | 📄 페이지별 텍스트 블록 및 참조 정보 |
| `figures` | Array | 🖼️ 감지된 도표/그림/표 정보 |
| `bbox` | Object | 📐 바운딩 박스 좌표 (x, y, width, height) |
| `not_matched` | Boolean | ❌ 참조가 도표와 매칭되지 않은 경우 true |

---

## ⚙️ 설정

<details>
<summary><strong>🔧 config.py 설정 옵션</strong></summary>

```python
# 🌐 서버 설정
HOST = "0.0.0.0"                # 서버 호스트
PORT = 5000                     # 포트 번호
DEBUG = False                   # 디버그 모드

# ⚡ 처리 설정
OCR_USE_GPU = True              # 🚀 GPU 가속 사용
DPI = 300                       # 🖼️ 이미지 변환 DPI
MAX_CONTENT_LENGTH = 50         # 📁 최대 파일 크기(MB)

# 🔍 PaddleOCR 설정
OCR_LANG = "en"                 # 🌍 OCR 언어
OCR_USE_ANGLE_CLS = True        # 🔄 텍스트 각도 감지 활성화
```

</details>

### 🌍 환경 변수 설정

```bash
# GPU 사용 여부
export OCR_USE_GPU=True

# 이미지 해상도 조정
export DPI=150

# 언어 설정
export OCR_LANG=en
```

---

## 🧪 고급 기능

### 🎯 타입 인식 처리

API는 다양한 요소 타입을 지능적으로 인식 및 처리합니다:

| 타입 | 설명 | 예시 |
|------|------|------|
| 🖼️ **그림** | 이미지, 차트, 다이어그램 | `Fig. 1`, `Figure 2.1` |
| 📊 **표** | 캡션 포함 데이터 표 | `Table 1`, `Tab. 2.1` |
| 🧮 **수식** | 번호가 있는 수식 | `Eq. (1)`, `(2.1)` |
| 🔧 **알고리즘** | 의사코드 블록 | `Algorithm 1` |
| 💡 **예제** | 코드 스니펫, 예제 | `Example 1` |

### 🧩 지능형 그룹화

고급 그룹화 전략 (다중 방식):

1. **🏷️ ID 기반 그룹화**: 동일 식별자 요소 매칭
2. **🔍 패턴 매칭**: 일반 레이아웃 패턴 인식  
3. **📐 공간 분석**: 근접도, 정렬 활용
4. **✅ 타입 호환성**: 논리적 요소 관계 보장

### 🕸️ 그래프 기반 매핑

NetworkX 기반 참조 매핑 시스템:

- 📊 **문서 구조 모델링**: 그래프로 문서 구조 표현
- 🎯 **관계 확률 계산**: 요소 간 연결 확률 산출
- 🧠 **지능형 추론**: AI 기반 관계 추론
- 📈 **신뢰도 제공**: 매핑 결과에 대한 신뢰도 점수

---

## 🐛 문제 해결

<details>
<summary><strong>⚡ CUDA 메모리 부족</strong></summary>

```bash
# 해결: CPU 모드 사용 또는 DPI 낮추기
export OCR_USE_GPU=False
export DPI=150
```

</details>

<details>
<summary><strong>📦 모델 다운로드 문제</strong></summary>

```bash
# 첫 실행 시 모델 자동 다운로드
# ✅ 인터넷 연결 확인
# 📁 모델은 ~/.paddlex/에 캐시됨
```

</details>

<details>
<summary><strong>📄 PDF 처리 오류</strong></summary>

```bash
# ✅ 파일 권한, 포맷 확인
# ✅ PDF가 손상/암호화되지 않았는지 확인
# ⚙️ 대용량 파일은 DPI 낮추기
```

</details>

<details>
<summary><strong>🔧 설치 문제</strong></summary>

```bash
# Python 3.12+ 호환성 문제
conda create -n pdfrec python=3.9
conda activate pdfrec

# PyMuPDF 오류
pip install PyMuPDF==1.24.0
```

</details>

---

## 📚 API 문서

### 🌐 엔드포인트

#### `POST /api/v1/analyze`

📄 **PDF 문서를 분석하여 구조화된 정보를 반환합니다.**

**파라미터:**
- `file` (필수): 📁 분석할 PDF 파일 (최대 50MB)

**응답:** 📊 문서 분석 결과 (JSON)

#### `GET /api/docs/`

📖 **Swagger 기반 인터랙티브 문서**

### 📋 응답 코드

| 코드 | 상태 | 설명 |
|------|------|------|
| `200` | ✅ 성공 | 정상 처리 완료 |
| `400` | ❌ 요청 오류 | 파일 오류, 용량 초과 등 |
| `500` | 🔥 서버 오류 | 처리 실패 |

---

## 🤝 기여하기

<div align="center">

**🎉 오픈소스 기여를 환영합니다!**

[![Contributors](https://img.shields.io/github/contributors/jaeho0718/PDF-Reference-Mapper)](https://github.com/CommitBang/PDF-Reference-Mapper/contributors)
[![Issues](https://img.shields.io/github/issues/jaeho0718/PDF-Reference-Mapper)](https://github.com/CommitBang/PDF-Reference-Mapper/issues)
[![Pull Requests](https://img.shields.io/github/issues-pr/jaeho0718/PDF-Reference-Mapper)](https://github.com/CommitBang/PDF-Reference-Mapper/pulls)

</div>

### 🛠️ 기여 절차

1. 🍴 **저장소 포크**
2. 🌟 **기능 브랜치 생성**
3. ✏️ **변경사항 반영**
4. 🧪 **테스트 추가**
5. 📝 **PR 제출**

자세한 내용은 [📖 기여 가이드라인](CONTRIBUTING.md)을 참고하세요.

### 🔧 개발 환경 설정

```bash
# 저장소 클론 및 개발 환경 설정
git clone https://github.com/CommitBang/PDFRecognitionAPI.git
cd PDFRecognitionAPI

# 개발 의존성 설치
python setup.py
pip install pytest pytest-flask black flake8

# 테스트 실행
pytest tests/
```

---

## 📝 라이선스

<div align="center">

**📄 버전 정책 및 변경 이력**

  **버전 정책**: [Semantic Versioning](https://semver.org/lang/ko/)
 
  **변경 이력**: [CHANGELOG.md](docs/CHANGELOG.md)

**⚖️ 라이선스**

이 프로젝트는 [Apache License 2.0](LICENSE) 하에 배포됩니다.

---
</div>